"""blender -b --python fp_pistol_render.py -- <굽기 태그> <포즈 태그> [뷰들=fp,left,right,top,bottom,back]
 1인칭 권총 팔(프레임 로컬 FBX) + P220(프레임 로컬) 을 텍스처로 Workbench 렌더.  fp = 해당 포즈의 1인칭 카메라(hip), 나머지는 그립 중심을 보는 외부 카메라.
 -> Data/fpp_<굽기>_<뷰>.png"""
import bpy, json, sys, math, itertools
import numpy as np
from mathutils import Matrix, Vector
A_ = sys.argv[sys.argv.index('--') + 1:]; BT, PT = A_[0], A_[1]; VIEWS = (A_[2] if len(A_) > 2 else 'fp,left,right,top,bottom,back').split(',')
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
P = json.load(open(D + r'\Data\lyra_fp_arms_pose_%s.json' % PT, encoding='utf-8')); SM = [x for x in P['samples'] if x.get('state', 'hip') == 'hip'][-1]
FR = SM['FurinaPistolFrame']; SLD = SM['FurinaPistolSlide']
def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
Rf = qmat(FR['q']); tf = np.array(FR['loc'])
mir = np.array([1, -1, 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
for side in ('L', 'R'): bpy.ops.import_scene.fbx(filepath=D + r'\FBX\FPArms\SM_FurinaFPPistArm%s_%s.fbx' % (side, BT))
def load_place(nm, tfc, is_slide):
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=D + r'\Data\p220_export\%s.fbx' % nm)
    ucx = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before and k.startswith('UCX_')]
    for o in ucx: bpy.data.objects.remove(o, do_unlink=True)   # 충돌용 볼록 껍질 제외
    objs = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before and bpy.data.objects[k].type == 'MESH']
    V = np.vstack([(np.array([v.co[:] for v in o.data.vertices]) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]) * 100 for o in objs])
    bmin = np.array(tfc['bmin']); bmax = np.array(tfc['bmax']); bb = None
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            a = V[:, list(perm)] * np.array(sg); off = bmin - a.min(0); err = np.abs((a + off).max(0) - bmax).sum()
            if bb is None or err < bb[0]: bb = (err, perm, sg, off)
    _, perm, sg, off = bb
    for o in objs:
        M = np.array(o.matrix_world); me = o.data
        for v in me.vertices:
            w = (M[:3, :3] @ np.array(v.co[:]) + M[:3, 3]) * 100; l = w[list(perm)] * np.array(sg) + off
            if is_slide:
                wl = qmat(tfc['q']) @ (l * np.array(tfc['scale'])) + np.array(tfc['loc']); l = Rf.T @ (wl - tf)
            v.co = Vector((l * mir / 100.0).tolist())
        o.matrix_world = Matrix.Identity(4)
    return objs
G = load_place('SM_P220_Frame', FR, False) + load_place('SM_P220_Slide', SLD, True)
TEX = {'Furina_SkinHair': 'SkinHair.png', 'Furina_Outfit': 'Outfit.png'}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    for ms in o.material_slots:
        if ms.material is None: continue
        m = ms.material; nm = m.name.split('.')[0]; m.diffuse_color = (0.35, 0.35, 0.38, 1)
        if nm in TEX:
            m.use_nodes = True; nt = m.node_tree; im = nt.nodes.new('ShaderNodeTexImage'); im.image = bpy.data.images.load(D + '\\Textures\\' + TEX[nm], check_existing=True); nt.nodes.active = im
            bs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
            if bs: nt.links.new(im.outputs['Color'], bs[0].inputs['Base Color'])
gray = bpy.data.images.new('GunGray', 4, 4); gray.pixels = [0.42, 0.44, 0.48, 1.0] * 16
for o in G:
    for ms in o.material_slots:
        if ms.material:
            m = ms.material; m.use_nodes = True; nt = m.node_tree
            for n_ in list(nt.nodes):
                if n_.type == 'TEX_IMAGE': nt.nodes.remove(n_)
            im = nt.nodes.new('ShaderNodeTexImage'); im.image = gray; nt.nodes.active = im
cam_d = bpy.data.cameras.new('C'); cam_d.lens_unit = 'FOV'; cam_d.sensor_fit = 'HORIZONTAL'; cam_d.clip_start = 0.005; cam_d.clip_end = 100
cam = bpy.data.objects.new('C', cam_d); bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera = cam
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = 1100; sc.render.resolution_y = 630
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
def ub(v): return Vector((np.array(v) * mir / 100.0).tolist())
def look(pos_ue, tgt_ue, up_ue=(0, 0, 1)):
    f = np.array(tgt_ue, float) - np.array(pos_ue, float); f /= np.linalg.norm(f); u = np.array(up_ue, float)
    if abs(f @ u) > 0.95: u = np.array([1.0, 0, 0])
    r = np.cross(u, f); r /= np.linalg.norm(r); u = np.cross(f, r)     # UE(왼손): right = up x fwd
    return f, r, u
def setcam(c_ue, f, r, u, fov):
    fb, rb, ubb = f * mir, r * mir, u * mir
    M = Matrix(((rb[0], ubb[0], -fb[0], 0), (rb[1], ubb[1], -fb[1], 0), (rb[2], ubb[2], -fb[2], 0), (0, 0, 0, 1))); M.translation = ub(c_ue); cam.matrix_world = M; cam_d.angle = math.radians(fov)
# 그립 중심(프레임 로컬): 프레임 경계 아래쪽 뒤
bmin = np.array(FR['bmin']); bmax = np.array(FR['bmax']); C = np.array([0.5, 0.1, -3.5])   # 그립 근처(프레임 로컬: X 총구, Y 오른쪽, Z 위)
for vw in VIEWS:
    if vw == 'fp':
        cw = np.array(SM['fpcam']['loc']); Rc = qmat(SM['fpcam']['q']); c = Rf.T @ (cw - tf); Rl = Rf.T @ Rc
        setcam(c, Rl[:, 0], Rl[:, 1], Rl[:, 2], SM.get('fov', 85.0))
    else:
        dirs = {'gunright': (0, 1, 0), 'gunleft': (0, -1, 0), 'left': (0, 1, 0), 'right': (0, -1, 0), 'frontleft': (0.7, -0.7, 0.15), 'backleft': (-0.6, -0.75, 0.3), 'top': (0, 0, 1), 'bottom': (0, 0, -1), 'back': (-1, 0, 0), 'front': (1, 0, 0)}
        dv = np.array(dirs[vw], float); pos = C + dv * 24.0
        f, r, u = look(pos, C, (0, 0, 1) if vw not in ('top', 'bottom') else (1, 0, 0)); setcam(pos, f, r, u, 50.0)
    sc.render.filepath = D + r'\Data\fpp_%s_%s.png' % (BT, vw); bpy.ops.render.render(write_still=True)
print('PRENDER_OK')
