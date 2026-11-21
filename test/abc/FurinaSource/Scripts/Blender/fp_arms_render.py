"""blender -b --python fp_arms_render.py -- <굽기 태그> <포즈 태그> <상태>
 1인칭 팔(소총 로컬 FBX) + M4 를 해당 상태의 1인칭 카메라(위치/방향/FOV 85)로 Workbench 렌더.  머티리얼별 색(피부=황갈, 옷=파랑, 총=회색).
 두 장: _cull0(뒷면 표시) / _cull1(뒷면 숨김)  -> Data/fprender_<굽기>_<상태>_cull*.png"""
import bpy, json, sys, math
import numpy as np
from mathutils import Matrix, Vector
A_ = sys.argv[sys.argv.index('--') + 1:]; BT, PT, ST = A_[0], A_[1], A_[2]
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
P = json.load(open(D + r'\Data\lyra_fp_arms_pose_%s.json' % PT, encoding='utf-8'))
def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
s = [x for x in P['samples'] if x.get('state', 'hip') == ST][-1]
Rr = qmat(s['rifle']['q']); tr = np.array(s['rifle']['loc']); Rc = qmat(s['fpcam']['q']); tc = np.array(s['fpcam']['loc'])
c = Rr.T @ (tc - tr); R = Rr.T @ Rc
mir = np.array([1, -1, 1])
def ub(v): return Vector((np.array(v) * mir / 100.0).tolist())
bpy.ops.wm.read_factory_settings(use_empty=True)
cols = {'Furina_SkinHair': (0.85, 0.6, 0.35, 1), 'Furina_Outfit': (0.1, 0.2, 0.8, 1)}
for side in ('L', 'R'):
    bpy.ops.import_scene.fbx(filepath=D + r'\FBX\FPArms\SM_FurinaFPArm%s_%s.fbx' % (side, BT))
before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=D + r'\FBX\M4\SK_M4A1.fbx')
TEX = {'Furina_SkinHair': 'SkinHair.png', 'Furina_Outfit': 'Outfit.png'}
TEXMODE = len(A_) > 3 and A_[3] == 'tex'
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    for ms in o.material_slots:
        if ms.material is None: continue
        m = ms.material; nm = m.name.split('.')[0]
        m.diffuse_color = cols.get(nm, (0.5, 0.5, 0.5, 1))
        if TEXMODE and nm in TEX:
            m.use_nodes = True; nt = m.node_tree; im = nt.nodes.new('ShaderNodeTexImage'); im.image = bpy.data.images.load(D + '\\Textures\\' + TEX[nm], check_existing=True)
            nt.nodes.active = im
            bs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
            if bs: nt.links.new(im.outputs['Color'], bs[0].inputs['Base Color'])
cam_d = bpy.data.cameras.new('C'); cam_d.lens_unit = 'FOV'; cam_d.sensor_fit = 'HORIZONTAL'; cam_d.angle = math.radians(s.get('fov', 85.0)); cam_d.clip_start = 0.02; cam_d.clip_end = 100
cam = bpy.data.objects.new('C', cam_d); bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera = cam
f = R[:, 0] * mir; r = R[:, 1] * mir; u = R[:, 2] * mir
M = Matrix(((r[0], u[0], -f[0], 0), (r[1], u[1], -f[1], 0), (r[2], u[2], -f[2], 0), (0, 0, 0, 1))); M.translation = ub(c); cam.matrix_world = M
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = 1280; sc.render.resolution_y = 733
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE' if TEXMODE else 'MATERIAL'
sc.world = bpy.data.worlds.new('W') if sc.world is None else sc.world
for cull in (0, 1):
    sh.show_backface_culling = bool(cull)
    sc.render.filepath = D + r'\Data\fprender_%s_%s%s_cull%d.png' % (BT, ST, '_tex' if TEXMODE else '', cull); bpy.ops.render.render(write_still=True)
print('RENDER_OK', ST)
