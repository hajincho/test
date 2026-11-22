"""blender -b --python build_class_fp_arms.py -- <class_key|all> [preview]
병과 캐릭터별 1인칭 팔 -> FBX/Classes/FPArms_<key>.fbx (언리얼: 1인칭 무기 메시(FurinaFPVM)를 리더 포즈로 따라가는 별도 메시)
 - 1인칭 무기 메시의 팔은 모두 fpvm_lib.load_arms('a1') = 푸리나 몸에서 팔 사슬 가중치 >= 0.5 인 정점 + 팔 뼈대(카메라 공간 K).
 - 여기서는 같은 팔 뼈대(K, 같은 뼈 이름)를 쓰고, 메시만 병과 캐릭터(FBX/Classes/<key>_cm.fbx)의 팔·손으로 바꿈.
 - 캐릭터 팔은 뼈 길이가 달라(케이아 184cm 등) 그대로 붙이면 무기를 쥐는 손 위치가 어긋남 -> 뼈마다 '푸리나 관절 + (정점 - 캐릭터 관절) × 길이비'로 옮겨
   (가중치로 섞음) 푸리나 1인칭 팔 길이에 맞춤. 뼈 방향은 이미 푸리나와 같음(build_class_on_furina.py).
 - 재질 슬롯 이름은 캐릭터 메시 그대로(MatNN) -> 언리얼에서 MI_<Key>_MatNN 사용."""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpvm_lib as L

R0 = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
KEYS = ['officer', 'infantry', 'assault', 'antitank', 'heavy', 'sniper', 'armor']
A = sys.argv[sys.argv.index('--') + 1:]
WANT = KEYS if A[0] == 'all' else [A[0]]; MODE = A[1] if len(A) > 1 else 'build'
CHAIN_ROOTS = ('Left arm', 'Right arm')


def run(key):
    arm, fbody, info = L.load_arms('a1', 0)          # 장면 초기화 포함
    K = Matrix(info['K']); arm.name = 'Armature'
    furina = {}
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=R0 + r'\FBX\Furina_cm.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
    fa = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
    furina = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in fa.data.bones}; FW = fa.matrix_world.copy()   # 푸리나 아마추어 로컬 = cm
    for o in [o for o in bpy.data.objects if o not in before]: bpy.data.objects.remove(o, do_unlink=True)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=R0 + rf'\FBX\Classes\{key}_cm.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
    new = [o for o in bpy.data.objects if o not in before]
    ca = [o for o in new if o.type == 'ARMATURE'][0]; cm = [o for o in new if o.type == 'MESH'][0]
    FI = FW.inverted(); CW = ca.matrix_world.copy()   # 캐릭터 FBX 는 미터로 읽힘 -> 모두 푸리나 아마추어 로컬(cm)로
    cls = {b.name: (FI @ (CW @ b.head_local), FI @ (CW @ b.tail_local)) for b in ca.data.bones}
    # 팔 사슬
    def desc(b):
        out = [b.name]
        for c in b.children: out += desc(c)
        return out
    chain = set(desc(ca.data.bones[CHAIN_ROOTS[0]])) | set(desc(ca.data.bones[CHAIN_ROOTS[1]]))
    # 메시를 아마추어 로컬(cm)로
    to_local = FI @ cm.matrix_world
    me = cm.data; me.transform(to_local); cm.parent = None; cm.matrix_world = Matrix.Identity(4)   # 부모(0.01 배율)를 먼저 끊어야 100배가 안 남음
    gi = {g.index: g.name for g in cm.vertex_groups}
    keep = np.array([sum(g.weight for g in v.groups if gi.get(g.group) in chain) >= 0.5 for v in me.vertices])
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS'); bm.to_mesh(me); bm.free()
    # 푸리나 팔 길이에 맞춤
    def seg(d, n):
        h, t = d[n]; return h, (t - h).length
    moved = 0
    for v in me.vertices:
        acc = Vector((0, 0, 0)); tot = 0.0
        for g in v.groups:
            n = gi.get(g.group)
            if not n or n not in cls or n not in furina or g.weight <= 0: continue
            hc, lc = seg(cls, n); hf, lf = seg(furina, n)
            s = (lf / lc) if (n in chain and lc > 0.3) else 1.0
            acc += g.weight * (hf + (v.co - hc) * s); tot += g.weight
        if tot > 0: v.co = acc / tot; moved += 1
    # 카메라 공간(K)으로, 1인칭 팔 뼈대에 붙임
    me.transform(K)
    cm.parent = arm; cm.matrix_parent_inverse = arm.matrix_world.inverted()
    for m in list(cm.modifiers): cm.modifiers.remove(m)
    mod = cm.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
    used = {p.material_index for p in me.polygons}
    bpy.context.view_layer.objects.active = cm
    for i in reversed(range(len(cm.material_slots))):
        if i not in used: cm.active_material_index = i; bpy.ops.object.material_slot_remove()
    bpy.data.objects.remove(ca, do_unlink=True)
    if MODE != 'preview': bpy.data.objects.remove(fbody, do_unlink=True)
    cm.name = 'Arms_' + key
    rep = {'key': key, 'verts': len(me.vertices), 'moved': moved, 'slots': [m.name for m in cm.data.materials],
           'len_ratio': {n: round(seg(furina, n)[1] / max(seg(cls, n)[1], 1e-6), 3) for n in ('Left arm', 'Left elbow', 'Right arm', 'Right elbow')}}
    if MODE == 'preview':
        sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = 900; sc.render.resolution_y = 600
        sc.display.shading.light = 'STUDIO'; sc.world = bpy.data.worlds.new('w')
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
        sc.display.shading.color_type = 'OBJECT'; cm.color = (0.9, 0.5, 0.2, 1); fbody.color = (0.3, 0.5, 0.9, 1)
        fbody.location = (0, 0.9, 0)   # 비교용 푸리나 1인칭 팔(파랑)을 옆에
        bpy.context.view_layer.update()
        pts = [cm.matrix_world @ Vector(c) for c in cm.bound_box] + [fbody.matrix_world @ Vector(c) for c in fbody.bound_box]
        ctr = sum(pts, Vector()) / len(pts); rep['bbox_cls'] = [list(cm.matrix_world @ Vector(c)) for c in (cm.bound_box[0], cm.bound_box[6])]; rep['bbox_fur'] = [list(fbody.matrix_world @ Vector(c)) for c in (fbody.bound_box[0], fbody.bound_box[6])]; print('BBOX', rep['bbox_cls'], rep['bbox_fur'], [list(b.head_local) for b in arm.data.bones if b.name == 'Left wrist']); cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.2
        d = Vector((0, 0, -1)); cam.location = ctr - d * 5; cam.rotation_euler = d.to_track_quat('-Z', 'X').to_euler(); cam.data.clip_end = 50
        sc.render.filepath = R0 + rf'\Data\fparms_{key}.png'; bpy.ops.render.render(write_still=True); rep['render'] = sc.render.filepath
    else:
        bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); cm.select_set(True); bpy.context.view_layer.objects.active = arm
        bpy.ops.export_scene.fbx(filepath=R0 + rf'\FBX\Classes\FPArms_{key}.fbx', use_selection=True, object_types={'ARMATURE', 'MESH'}, axis_forward='-Y', axis_up='Z',
                                 apply_unit_scale=True, add_leaf_bones=False, bake_anim=False, mesh_smooth_type='FACE', path_mode='STRIP', armature_nodetype='NULL',
                                 primary_bone_axis='Y', secondary_bone_axis='X')
        rep['fbx'] = rf'FBX\Classes\FPArms_{key}.fbx'
    return rep


out = {k: run(k) for k in WANT}
p = R0 + r'\Data\class_fparms.json'
old = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
old.update(out); json.dump(old, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('FPARMS_DONE', {k: (v['verts'], v['len_ratio']) for k, v in out.items()})
