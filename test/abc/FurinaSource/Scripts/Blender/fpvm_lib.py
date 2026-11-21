"""1인칭 뷰모델(팔 + 무기 한 몸 스켈레탈) 공용 라이브러리 — fpvm_<무기>.py 가 import 해서 씀.
 좌표 규칙: 작업 공간 = '내보내기 카메라 공간'(Blender m). UE 로 가면 (x, -y, z)*100 cm = FPCamera 로컬(X 앞, Y 오른쪽, Z 위).
   즉 Blender +X = 앞, -Y = 오른쪽, +Z = 위.  무기 원본(정리본 FBX, cm): 총구 -Y, 위 +Z, 총의 오른쪽 -X  -> Rz(+90°) 로 카메라 공간에 놓음.
 팔: Furina_cm.fbx 를 UE PIE 1인칭 기록(Data/lyra_fp_arms_pose_<태그>.json)의 카메라 기준으로 옮기고(어깨 위치가 실제 게임과 같음), 팔 정점만 남긴다(스키닝 유지).
 손: 팔꿈치 IK(2 마디) + 손목 회전 목표 + 손가락 자동 쥐기(뼈 따라 점을 찍어 무기 표면과 닿을 때까지 굽힘)."""
import bpy, bmesh, json, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'; EXP = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany\_export'
FINGERS = ['Thumb', 'IndexFinger', 'MiddleFinger', 'RingFinger', 'LittleFinger']
def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def fbones(side, f):
    return ['Thumb0_%s' % side, 'Thumb1_%s' % side, 'Thumb2_%s' % side] if f == 'Thumb' else ['%s%d_%s' % (f, i, side) for i in (1, 2, 3)]

# ------------------------------------------------------------------ 팔(푸리나) 불러와 카메라 공간으로
def load_arms(pose_tag='a1', sample=0, th=0.5):
    """반환: arm(아마추어), body(팔만 남은 메시), info(dict). 둘 다 카메라 공간(m)으로 변환 적용됨."""
    P = json.load(open(D + r'\Data\lyra_fp_arms_pose_%s.json' % pose_tag, encoding='utf-8')); S0 = P['samples'][0]; SM = P['samples'][sample]
    UB = S0['bones']; ref_cs = {}
    def ref_of(b):
        if b in ref_cs: return ref_cs[b]
        e = UB[b]; r = e['ref']; R_l = qmat(r['q']); t_l = np.array(r['loc']); s_l = np.array(r['scale']); par = e.get('parent')
        if par in (None, 'None', '') or par not in UB: ref_cs[b] = (R_l, t_l, s_l); return ref_cs[b]
        Rp, tp, sp = ref_of(par); ref_cs[b] = (Rp @ R_l, Rp @ (sp * t_l) + tp, sp * s_l); return ref_cs[b]
    for b in UB: ref_of(b)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=D + r'\FBX\Furina_cm.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
    arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]; body = [o for o in bpy.data.objects if o.type == 'MESH'][0]
    def bname(u):
        if u in arm.data.bones: return u
        v = u.replace('-', ' '); return v if v in arm.data.bones else None
    pairs = [(u, bname(u)) for u in UB if bname(u)]
    X = np.array([ref_cs[u][1] for u, b in pairs]); Y = np.array([list(arm.data.bones[b].head_local) for u, b in pairs])
    xc = X.mean(0); yc = Y.mean(0); Xc = X - xc; Yc = Y - yc; U_, S_, Vt = np.linalg.svd(Yc.T @ Xc); best = None
    for d in (1, -1):
        Dm = np.diag([1, 1, d]); A = U_ @ Dm @ Vt; s = np.trace(np.diag(S_) @ Dm) / (Xc ** 2).sum(); bvec = yc - s * A @ xc
        err = np.linalg.norm((s * (A @ X.T)).T + bvec - Y, axis=1)
        if best is None or err.mean() < best[0]: best = (err.mean(), A, s, bvec)
    _, A, s, bvec = best
    # 아마추어 공간 x -> UE cs -> UE 월드 -> 카메라 로컬(UE cm) -> 내보내기 공간(m, y 뒤집기)
    Rm = qmat(SM['mesh']['q']); tm = np.array(SM['mesh']['loc']); sm_ = np.array(SM['mesh']['scale'])
    Rc = qmat(SM['fpcam']['q']); tc = np.array(SM['fpcam']['loc']); Ainv = A.T / s
    def a2c(x): cs = Ainv @ (np.array(x) - bvec); wv = Rm @ (sm_ * cs) + tm; return Rc.T @ (wv - tc)
    Sx = np.diag([0.01, -0.01, 0.01]); c0 = Sx @ a2c(np.zeros(3)); L = np.column_stack([Sx @ a2c(e) - c0 for e in np.eye(3)])
    K = np.eye(4); K[:3, :3] = L; K[:3, 3] = c0
    info = {'phi_err': float(best[0]), 'K_det': float(np.linalg.det(L)), 'scale': float(np.cbrt(abs(np.linalg.det(L))))}
    # 팔 정점만 남김(스키닝 유지)
    def desc(b):
        out = [b]
        for c in b.children: out += desc(c)
        return out
    armset = set(b.name for b in desc(arm.data.bones['Left arm'])) | set(b.name for b in desc(arm.data.bones['Right arm']))
    gi = {g.index: g.name for g in body.vertex_groups}
    keep = [sum(g.weight for g in v.groups if gi.get(g.group) in armset) >= th for v in body.data.vertices]
    bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS'); bm.to_mesh(body.data); bm.free()
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o is not body]: bpy.data.objects.remove(o)
    used = set(p.material_index for p in body.data.polygons); bpy.context.view_layer.objects.active = body
    for i in reversed(range(len(body.material_slots))):
        if i not in used: body.active_material_index = i; bpy.ops.object.material_slot_remove()
    # 필요 없는 뼈 삭제: 팔 사슬 + 조상만 유지
    keepb = set(armset)
    for side in ('Left', 'Right'):
        b = arm.data.bones['%s arm' % side].parent
        while b: keepb.add(b.name); b = b.parent
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
    for eb in list(arm.data.edit_bones):
        if eb.name not in keepb: arm.data.edit_bones.remove(eb)
    bpy.ops.object.mode_set(mode='OBJECT')
    # 카메라 공간으로 옮기고 변환 적용
    MB = arm.matrix_world.inverted() @ body.matrix_world
    arm.matrix_world = Matrix(K.tolist()); body.matrix_world = arm.matrix_world @ MB
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); body.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    info['bones_kept'] = len(arm.data.bones); info['arm_verts'] = len(body.data.vertices)
    for side in ('Left', 'Right'):
        h = arm.data.bones['%s arm' % side].head_local; e = arm.data.bones['%s elbow' % side].head_local; w = arm.data.bones['%s wrist' % side].head_local
        info['%s_shoulder_cm' % side] = [round(v * 100, 2) for v in h]; info['%s_len_cm' % side] = [round((e - h).length * 100, 2), round((w - e).length * 100, 2)]
    return arm, body, info

# ------------------------------------------------------------------ 무기
def gun_native_to_cam(pos_cm, yaw=0.0, pitch=0.0, roll=0.0):
    """무기 원본(cm, 총구 -Y) -> 카메라 공간(m) 행렬. pos_cm = 카메라 공간(Blender 축, cm)에서 무기 원점 위치.
    yaw/pitch/roll(°): 총구 기준(+yaw = 총구가 왼쪽, +pitch = 총구 위, +roll = 윗면이 오른쪽으로)."""
    base = Matrix.Rotation(math.pi / 2, 4, 'Z')   # 총구 -Y -> +X(앞)
    R = Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(-pitch), 4, 'Y') @ Matrix.Rotation(math.radians(roll), 4, 'X')
    return Matrix.Translation(Vector(pos_cm) / 100.0) @ R @ base @ Matrix.Scale(0.01, 4)
def load_weapon(key):
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=EXP + '\\SM_DE_%s.fbx' % key)
    obs = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before and bpy.data.objects[k].type == 'MESH']
    for o in [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before and bpy.data.objects[k].type != 'MESH']: bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(obs) > 1: bpy.ops.object.join()
    g = bpy.context.view_layer.objects.active; g.data.transform(Matrix.Scale(100, 4)); g.name = 'W_' + key   # 원본 cm 로
    return g
def split_by(g, name, face_pred):
    """face_pred(material_name, centroid_cm) 가 참인 면을 떼어 새 오브젝트로."""
    bm = bmesh.new(); bm.from_mesh(g.data); mats = [m.name if m else '' for m in g.data.materials]
    sel = [f for f in bm.faces if face_pred(mats[f.material_index] if mats else '', f.calc_center_median())]
    me2 = g.data.copy(); bm2 = bmesh.new(); bm2.from_mesh(me2); ids = set(f.index for f in sel)
    bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in ids], context='FACES'); bm2.to_mesh(me2); bm2.free()
    bmesh.ops.delete(bm, geom=sel, context='FACES'); bm.to_mesh(g.data); bm.free()
    o = bpy.data.objects.new(name, me2); bpy.context.scene.collection.objects.link(o); o.matrix_world = g.matrix_world.copy(); return o, len(ids)

# ------------------------------------------------------------------ 뼈 추가(무기 부품) + 스키닝
def add_bone(arm, name, parent, head, tail):
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones.new(name); eb.head = Vector(head); eb.tail = Vector(tail); eb.roll = 0.0
    if parent: eb.parent = arm.data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
def bind_rigid(arm, ob, bone):
    """메시를 아마추어 자식 + 뼈 하나에 100% 가중치."""
    vg = ob.vertex_groups.new(name=bone); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    mw = ob.matrix_world.copy(); ob.parent = arm; ob.matrix_world = mw
    mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = arm

# ------------------------------------------------------------------ 손 축(손목 로컬): 손가락 방향 f, 손바닥 방향 p
def hand_axes(arm, side):
    B = arm.data.bones; w = B['%s wrist' % ('Left' if side == 'L' else 'Right')]
    Mw = w.matrix_local.to_3x3(); hw = w.head_local
    f = (B['MiddleFinger1_%s' % side].head_local - hw).normalized()
    a = (B['IndexFinger1_%s' % side].head_local - B['LittleFinger1_%s' % side].head_local).normalized()
    p = a.cross(f).normalized() if side == 'R' else f.cross(a).normalized()
    # 손가락이 굽는 쪽이 손바닥: 엄지 끝이 손바닥 쪽에 있는지로 부호 확인
    t = B['Thumb2_%s' % side].tail_local - hw
    if t.dot(p) < 0: p = -p
    inv = Mw.inverted()
    return {'f_local': inv @ f, 'p_local': inv @ p, 'len_palm': (B['MiddleFinger1_%s' % side].head_local - hw).length}
def wrist_rot_for(axes, f_world, p_world):
    """손가락 방향 f, 손바닥 방향 p(카메라 공간) 를 만족하는 손목 뼈 월드 회전(3x3)."""
    def basis(f, p):
        f = Vector(f).normalized(); p = (Vector(p) - Vector(p).dot(f) * f).normalized(); return Matrix((f, p, f.cross(p))).transposed()
    return basis(f_world, p_world) @ basis(axes['f_local'], axes['p_local']).inverted()

# ------------------------------------------------------------------ 손가락 굽힘 축(뼈 로컬) — 손끝이 손바닥 쪽으로 가는 회전축
def finger_axes(arm, side, axes):
    B = arm.data.bones; w = B['%s wrist' % ('Left' if side == 'L' else 'Right')]; p_world = w.matrix_local.to_3x3() @ axes['p_local']
    out = {}
    for f in FINGERS:
        for bn in fbones(side, f):
            b = B[bn]; d = (b.tail_local - b.head_local).normalized()
            if f == 'Thumb':   # 엄지: 손바닥 쪽 + 검지 쪽으로 감싸기
                ax = d.cross((p_world + 0.6 * (B['IndexFinger1_%s' % side].head_local - b.head_local).normalized()).normalized())
            else: ax = d.cross(p_world)
            out[bn] = (b.matrix_local.to_3x3().inverted() @ ax.normalized()).normalized()
    return out
