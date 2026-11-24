"""1인칭 뷰모델(팔 + 무기 한 몸 스켈레탈) 공용 라이브러리 — fpvm_<무기>.py 가 import 해서 씀.
 좌표 규칙: 작업 공간 = '내보내기 카메라 공간'(Blender m). UE 로 가면 (x, -y, z)*100 cm = FPCamera 로컬(X 앞, Y 오른쪽, Z 위).
   즉 Blender +X = 앞, -Y = 오른쪽, +Z = 위.  무기 원본(정리본 FBX, cm): 총구 -Y, 위 +Z, 총의 오른쪽 -X  -> Rz(+90°) 로 카메라 공간에 놓음.
 팔: Furina_cm.fbx 를 UE PIE 1인칭 기록(Data/lyra_fp_arms_pose_<태그>.json)의 카메라 기준으로 옮기고(어깨 위치가 실제 게임과 같음), 팔 정점만 남긴다(스키닝 유지).
 손: 팔꿈치 IK(2 마디) + 손목 회전 목표 + 손가락 자동 쥐기(뼈 따라 점을 찍어 무기 표면과 닿을 때까지 굽힘)."""
import bpy, bmesh, json, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree
import os as _os   # 2026-11-23: 프로젝트를 Downloads 에서 옮겨 옛 고정 경로가 없어짐 -> 이 파일 위치 기준(환경변수 FURINA_D / FURINA_EXP 로 바꿀 수 있음)
D = _os.environ.get('FURINA_D') or _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
EXP = _os.environ.get('FURINA_EXP') or _os.path.join(D, 'FBX', 'Weapons', '_export')   # 무기 정리본 SM_DE_<키>.fbx (lyra_export_weapon_src.py 가 언리얼 SM_DE_* 에서 다시 뽑음)
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
    info['bones_kept'] = len(arm.data.bones); info['arm_verts'] = len(body.data.vertices); info['K'] = K.tolist()   # 아마추어 로컬(cm) -> 카메라 공간(m)
    global _LAST_K; _LAST_K = Matrix(K.tolist())
    for side in ('Left', 'Right'):
        h = arm.data.bones['%s arm' % side].head_local; e = arm.data.bones['%s elbow' % side].head_local; w = arm.data.bones['%s wrist' % side].head_local
        info['%s_shoulder_cm' % side] = [round(v * 100, 2) for v in h]; info['%s_len_cm' % side] = [round((e - h).length * 100, 2), round((w - e).length * 100, 2)]
    if FP_CHAR != 'furina':   # 2026-11-23 캐릭터 통일: 1인칭 팔 메시 = 통일 캐릭터 팔(같은 팔 뼈대, 재질 CA<Key>_*) -> 손가락 쥐기·소매 접기·휴식 자세 굳히기가 모두 이 피부 기준
        ca = class_arm_objects(arm, keys=((FP_CHAR, FP_KEY),)); bpy.data.objects.remove(body, do_unlink=True); body = ca[0]; body.name = 'Body'
        info['fp_char'] = FP_CHAR; info['arm_verts'] = len(body.data.vertices)
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
    _restore_ue_export(g, key)
    if key == 'p38': seat_p38_slide(g)
    return g
UE_SANITIZED = {'6_5': '6.5', 'p_line': 'p line', '7_92х57_l': '7.92х57 l', 'mg_34_mag': 'mg 34 mag', 'mg_34': 'mg 34'}   # 언리얼 슬롯 이름(점·빈칸 -> _) -> 원래 재질 이름
def _restore_ue_export(g, key):
    """언리얼에서 다시 뽑은 원본(lyra_export_weapon_src.py)이면: 임시 재질 이름 M_SNN -> 원래 슬롯 이름(.slots.json), 언리얼이 UV·법선 경계에서 쪼갠 정점을 다시 붙임(연결 성분이 원본과 같게)."""
    side = _os.path.join(EXP, 'SM_DE_%s.slots.json' % key)
    if not _os.path.exists(side): return
    table = {t['tmp']: t['slot'] for t in json.load(open(side, encoding='utf-8'))}
    for m in g.data.materials:
        if m is None: continue
        base = m.name.split('.')[0]
        if base in table: m.name = UE_SANITIZED.get(table[base], table[base])
    bm = bmesh.new(); bm.from_mesh(g.data)   # 같은 재질 안에서만 붙임(언리얼은 재질 구역마다 정점을 따로 둠; 다른 재질 부품끼리 붙으면 성분이 합쳐짐 - MP38 탄창)
    for mi in sorted({f.material_index for f in bm.faces}):
        vs = list({v for f in bm.faces if f.material_index == mi for v in f.verts})
        bmesh.ops.remove_doubles(bm, verts=vs, dist=1e-4)
    bm.to_mesh(g.data); bm.free()
P38_SLIDE_SHIFT_CM = 3.31
def seat_p38_slide(g):
    """원본 P38 은 슬라이드가 뒤로 3.3cm 당겨진(후퇴) 상태로 모델링돼 있음(슬라이드 앞 y -1.74 > 프레임 앞 -5.05, 뒤끝이 공이치기를 덮음).
    슬라이드에 붙은 성분(윗몸·가늠자·안전장치·약실표시 핀 등: 성분 최저 z >= 2.2, 최소 y >= -1.8)을 앞(-Y)으로 옮겨 장전 완료 위치(슬라이드 앞 = 프레임 앞)로."""
    bm = bmesh.new(); bm.from_mesh(g.data); bm.verts.ensure_lookup_table()
    same = {}
    for v in bm.verts: same.setdefault(tuple(round(c, 3) for c in v.co), []).append(v)
    lab = {}; comps = []
    for v in bm.verts:
        if v.index in lab: continue
        st = [v]; lab[v.index] = len(comps); ids = []
        while st:
            x = st.pop(); ids.append(x)
            for y in [e.other_vert(x) for e in x.link_edges] + same[tuple(round(c, 3) for c in x.co)]:
                if y.index not in lab: lab[y.index] = len(comps); st.append(y)
        comps.append(ids)
    moved = 0
    for ids in comps:
        if min(v.co.z for v in ids) >= 2.2 and min(v.co.y for v in ids) >= -1.8:
            for v in ids: v.co.y -= P38_SLIDE_SHIFT_CM
            moved += len(ids)
    bm.to_mesh(g.data); bm.free(); g.data.update()
    return moved
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


# ------------------------------------------------------------------ 병과 캐릭터 1인칭 팔(2026-11-22)
CLASS_KEYS = (('officer', 'Officer'), ('infantry', 'Infantry'), ('assault', 'Assault'), ('antitank', 'AntiTank'), ('heavy', 'Heavy'), ('sniper', 'Sniper'), ('armor', 'Armor'),
              ('jp_officer', 'JpOfficer'), ('jp_infantry', 'JpInfantry'), ('jp_assault', 'JpAssault'), ('jp_antitank', 'JpAntiTank'), ('jp_heavy', 'JpHeavy'), ('jp_sniper', 'JpSniper'), ('jp_armor', 'JpArmor'))
SLEEVE_MAX_CM = {'arm': 5.0, 'elbow': 3.8}   # 1인칭에서 화면을 가리던 큰 소매(미카·유라·진·아야토 등): 팔 축에서 이 반지름 밖은 축 쪽으로 당김(손·손가락은 그대로)
SLEEVE_CUT = {'robin': {'mats': ('Mat23', 'Mat24', 'Mat25', 'Mat26'), 'r_cm': (5.5, 3.9), 'no_clamp': True, 'drop': ('Mat07',)},   # Robin: 위팔 프릴 소매(袖外·袖內·袖金屬·袖珠, 최대 13cm), Mat07 = 왼팔에 묻은 드레스 조각
              'sparxie': {'mats': ('Mat29', 'Mat20', 'Mat19'), 'r_cm': (4.6, 3.9), 'no_clamp': True, 'drop': ('Mat21',)}}   # drop: 어깨 카드 장식(肩飾)은 1인칭 팔에서 뺌   # 소매(袖)·소매 레이스(袖花边): 어깨부터 종 모양으로 최대 32cm 퍼짐 -> 위팔 4.6 / 아래팔 3.9cm 안으로
_LAST_K = None
# 2026-11-23 사용자 지정: 캐릭터 통일(Sparxie). 1인칭 팔은 이 캐릭터 하나(load_arms 의 body), 병과 팔 14종은 넣지 않음. FURINA_FP_CHAR=furina 면 예전 방식(푸리나 몸 + 병과 팔 14종)
FP_CHAR = _os.environ.get('FURINA_FP_CHAR', 'robin'); FP_KEY = {'sparxie': 'Sparxie', 'robin': 'Robin'}.get(FP_CHAR, FP_CHAR.title())   # 2026-11-23: Sparxie -> Robin 으로 교체(사용자 지정)
def class_arm_objects(arm, K=None, th=0.5, keys=None):
    if keys is None:
        if FP_CHAR != 'furina': return []   # 통일 캐릭터: 팔은 load_arms 가 이미 넣음
        keys = CLASS_KEYS
    """1인칭 무기 메시에 함께 넣을 병과 캐릭터 7종의 팔·손 메시(같은 팔 뼈대 arm 에 스키닝). 재질 이름 CA<Key>_<원래 슬롯>(언리얼에서 캐릭터별로 보이기/가리기).
    캐릭터 팔(FBX/Classes/<key>_cm.fbx, 뼈 방향은 푸리나와 같음)을 뼈마다 '푸리나 관절 + (정점 - 캐릭터 관절) × 길이비'로 옮겨 푸리나 1인칭 팔 길이에 맞추고 K(아마추어 cm -> 카메라 m)로.
    언리얼 리더 포즈로 별도 메시를 따라가게 하면 이 뷰모델 구조에서 축소·엇나가서(2026-11-22 시험) 무기 메시 안에 같이 넣는다."""
    K = K or _LAST_K; assert K is not None, 'load_arms 먼저'
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=D + r'\FBX\Furina_cm.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
    fa = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
    fur = {b.name: (b.head_local.copy(), (b.tail_local - b.head_local).length) for b in fa.data.bones}; FI = fa.matrix_world.inverted()
    for o in [o for o in bpy.data.objects if o not in before]: bpy.data.objects.remove(o, do_unlink=True)
    out = []
    for key, Key in keys:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=D + r'\FBX\Classes\%s_cm.fbx' % key, automatic_bone_orientation=False, ignore_leaf_bones=False)
        new = [o for o in bpy.data.objects if o not in before]
        ca = [o for o in new if o.type == 'ARMATURE'][0]; cm = [o for o in new if o.type == 'MESH'][0]; CW = ca.matrix_world.copy()
        cls = {b.name: (FI @ (CW @ b.head_local), (FI @ (CW @ b.tail_local) - FI @ (CW @ b.head_local)).length) for b in ca.data.bones}
        def desc(b):
            r = [b.name]
            for c in b.children: r += desc(c)
            return r
        chain = set(desc(ca.data.bones['Left arm'])) | set(desc(ca.data.bones['Right arm']))
        me = cm.data; me.transform(FI @ cm.matrix_world); cm.parent = None; cm.matrix_world = Matrix.Identity(4)
        gi = {g.index: g.name for g in cm.vertex_groups}
        keep = [sum(g.weight for g in v.groups if gi.get(g.group) in chain) >= th for v in me.vertices]
        bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS'); bm.to_mesh(me); bm.free()
        for v in me.vertices:
            acc = Vector((0, 0, 0)); tot = 0.0
            for g in v.groups:
                n = gi.get(g.group)
                if not n or n not in cls or n not in fur or g.weight <= 0: continue
                hc, lc = cls[n]; hf, lf = fur[n]; sc = (lf / lc) if (n in chain and lc > 0.3) else 1.0
                acc += g.weight * (hf + (v.co - hc) * sc); tot += g.weight
            if tot > 0: v.co = acc / tot
        # 큰 소매 줄이기: 손목·손가락 가중치가 작은 정점만, 지배 뼈(위팔/아래팔) 축에서 반지름 제한
        hand_like = lambda n: n and (('wrist' in n) or ('Finger' in n) or n.startswith('Thumb'))
        cut = SLEEVE_CUT.get(key)
        if cut:   # 반지름을 눌러 자르면(clamp) 겹친 천이 구겨져 덩어리·꼬인 손목이 됨 -> 팔 따라 1cm 단면마다 '가장 넓은 폭 -> 목표 반지름' 비율로 소매 전체를 고르게 줄임(모양 유지, 겹침 없음)
            mi = {i for i, m in enumerate(me.materials) if m and m.name.split('.')[0] in cut['mats']}
            di = {i for i, m in enumerate(me.materials) if m and m.name.split('.')[0] in cut.get('drop', ())}
            if di:
                bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in di], context='FACES_ONLY')
                bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(me); bm.free()
            sv = {vi for p in me.polygons if p.material_index in mi for vi in p.vertices}
            lines = {s: (fur['%s arm' % s][0], fur['%s elbow' % s][0], fur['%s wrist' % s][0]) for s in ('Left', 'Right')}
            def foot(co):
                best = None
                for s, (A0, E0, W0) in lines.items():
                    for k, (a, b, s0) in enumerate(((A0, E0, 0.0), (E0, W0, (E0 - A0).length))):
                        ab = b - a; t = max(0.0, min(1.0, (co - a).dot(ab) / ab.length_squared)); p = a + ab * t; d = co - p
                        if best is None or d.length < best[0]: best = (d.length, s, s0 + t * ab.length, p, d, k)
                return best
            F = {vi: foot(me.vertices[vi].co) for vi in sv}; mx = {}
            for vi, (r, s, sp, p, d, k) in F.items(): key2 = (s, int(sp)); mx[key2] = max(mx.get(key2, 0.0), r)
            for vi, (r, s, sp, p, d, k) in F.items():
                m_ = max(mx.get((s, int(sp) + j), 0.0) for j in (-2, -1, 0, 1, 2))
                tgt = cut['r_cm'][k]; f = min(1.0, tgt / m_) if m_ > 1e-6 else 1.0
                me.vertices[vi].co = p + d * f
            # 소매 가중치: 원래 소매 물리 뼈가 가슴·어깨(조상)에 합쳐져 있어 팔을 굽히면 천이 판처럼 늘어남 -> 팔 축 위치로 위팔/아래팔/손목에만(팔꿈치 ±3cm, 손목 앞 2cm 섞음)
            groups = {g.name: g for g in cm.vertex_groups}
            for s in ('Left', 'Right'):
                for b in ('arm', 'elbow', 'wrist'):
                    if '%s %s' % (s, b) not in groups: groups['%s %s' % (s, b)] = cm.vertex_groups.new(name='%s %s' % (s, b))
            for vi, (r, s, sp, p, d, k) in F.items():
                A0, E0, W0 = lines[s]; Lu = (E0 - A0).length; Lf = (W0 - E0).length
                wa = max(0.0, min(1.0, (Lu + 3.0 - sp) / 6.0)); ww = max(0.0, min(1.0, (sp - (Lu + Lf - 2.0)) / 2.0)); we = max(0.0, 1.0 - wa - ww)
                for g in cm.vertex_groups: g.remove([vi])
                for b, w in (('arm', wa), ('elbow', we), ('wrist', ww)):
                    if w > 1e-3: groups['%s %s' % (s, b)].add([vi], w, 'REPLACE')
        for v in (me.vertices if not (cut and cut.get('no_clamp')) else []):
            ws = [(gi.get(g.group), g.weight) for g in v.groups if g.weight > 0]
            if not ws: continue
            n, _ = max(ws, key=lambda t: t[1])
            if not n or n not in fur: continue
            if sum(w for nn, w in ws if nn and ('Finger' in nn or nn.startswith('Thumb'))) > 0.2: continue   # 손가락은 그대로
            if n.endswith(' wrist'):   # 손목 지배 정점 중 손목 관절 앞(팔꿈치 쪽) = 소맷부리 -> 아래팔 축 기준으로 줄임
                el = fur[n.replace(' wrist', ' elbow')][0]; wr = fur[n][0]; ab = wr - el
                if (v.co - el).dot(ab) / ab.length_squared > 1.02: continue
                n = n.replace(' wrist', ' elbow')
            elif sum(w for nn, w in ws if hand_like(nn)) > 0.3: continue
            kind = 'arm' if n.endswith(' arm') else ('elbow' if n.endswith(' elbow') else None)
            if not kind: continue
            child = n.replace(' arm', ' elbow') if kind == 'arm' else n.replace(' elbow', ' wrist')
            a = fur[n][0]; b = fur[child][0]; ab = b - a
            t = max(0.0, min(1.0, (v.co - a).dot(ab) / ab.length_squared)); pnt = a + ab * t; d = v.co - pnt
            if d.length > SLEEVE_MAX_CM[kind]: v.co = pnt + d.normalized() * SLEEVE_MAX_CM[kind]
        me.transform(K)
        for m in list(cm.modifiers): cm.modifiers.remove(m)
        for g in list(cm.vertex_groups):
            if g.name not in arm.data.bones: cm.vertex_groups.remove(g)
        used = {p.material_index for p in me.polygons}
        mats = list(me.materials)
        for i, m in enumerate(mats):
            if m is not None and i in used:
                nm = 'CA%s_%s' % (Key, m.name.split('.')[0]); mm = bpy.data.materials.get(nm) or m.copy(); mm.name = nm; me.materials[i] = mm
        bpy.context.view_layer.objects.active = cm
        for i in reversed(range(len(cm.material_slots))):
            if i not in used: cm.active_material_index = i; bpy.ops.object.material_slot_remove()
        cm.parent = arm; cm.matrix_parent_inverse = arm.matrix_world.inverted()
        md = cm.modifiers.new('Armature', 'ARMATURE'); md.object = arm
        for uv in list(me.uv_layers)[1:]: me.uv_layers.remove(uv)   # UV 1개(무기 메시와 UV 채널 수 맞춤)
        bpy.data.objects.remove(ca, do_unlink=True); cm.name = 'Arms_' + Key; out.append(cm)
    return out


def bake_arms_rest(arm, meshes):
    """지금 팔 자세(쇄골·소매 접기)를 휴식 자세로 굳힘: 메시마다 아마추어 모디파이어를 적용(변형을 정점에 굳힘) -> 뼈 휴식 자세 갱신 -> 모디파이어 다시 연결.
    2026-11-22: 예전엔 푸리나 팔(body)만 굳히고 병과 팔(Arms_*)은 빼먹어, 게임에서 보이는 병과 팔이 새 휴식 자세와 어긋나 손목 10~40cm·손가락 4~11cm 틀어져 있었음."""
    for o in meshes:
        bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = o; o.select_set(True)
        if o.data.shape_keys: o.shape_key_clear()   # 얼굴 표정 등 셰이프키(팔에는 불필요, 있으면 모디파이어 적용이 안 됨)
        for mod in list(o.modifiers):
            if mod.type == 'ARMATURE': bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.armature_apply(selected=False); bpy.ops.object.mode_set(mode='OBJECT')
    for o in meshes:
        m = o.modifiers.new('Armature', 'ARMATURE'); m.object = arm
