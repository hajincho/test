"""blender -b --python fp_arms_bake.py -- <포즈 태그> [샘플=0] [임계=0.5]
 1인칭 전용 팔: Furina_cm.fbx 를 UE PIE 에서 기록한 1인칭 소총 대기 자세(Data/lyra_fp_arms_pose_<태그>.json)로 포즈 잡고,
 팔 뼈(Left/Right arm 이하) 가중치 합 >= 임계 인 정점만 떼어 '소총 컴포넌트(FurinaRifle) 로컬 좌표' 로 굽는다.
 -> FBX/FPArms/SM_FurinaFPArm<L|R>_<태그>.fbx  (Blender m 단위, axis -Y/Z, apply_unit_scale -> UE cm, UE 로컬 = 소총 로컬)
 -> Data/fp_arms_bake_<태그>.json (맞춤 오차, 예상 경계, 손목 위치 등)
 좌표: UE 메시 컴포넌트 공간(cs) <-> Blender 아마추어 공간(cm) 대응 Phi 를 참조 포즈 뼈 위치로 맞춘다(반사 허용)."""
import bpy, bmesh, json, sys, math
import numpy as np
from mathutils import Matrix, Vector
A_ = sys.argv[sys.argv.index('--') + 1:]; TAG = A_[0]; SI = int(A_[1]) if len(A_) > 1 else 0; TH = float(A_[2]) if len(A_) > 2 else 0.5
OTAG = A_[5] if len(A_) > 5 else TAG   # 출력 태그(FBX/json 이름)
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
P = json.load(open(D + r'\Data\lyra_fp_arms_pose_%s.json' % TAG, encoding='utf-8'))
S0 = P['samples'][0]; SM = P['samples'][SI]
OUT = {'tag': OTAG, 'pose_tag': TAG, 'sample': SI, 'th': TH}
def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
# ---- UE 참조 포즈(cs) 합성
UB = S0['bones']
ref_cs = {}
def ref_of(b):
    if b in ref_cs: return ref_cs[b]
    e = UB[b]; r = e['ref']; R_l = qmat(r['q']); t_l = np.array(r['loc']); s_l = np.array(r['scale'])
    par = e.get('parent')
    if par in (None, 'None', '') or par not in UB: ref_cs[b] = (R_l, t_l, s_l); return ref_cs[b]
    Rp, tp, sp = ref_of(par)
    ref_cs[b] = (Rp @ R_l, Rp @ (sp * t_l) + tp, sp * s_l); return ref_cs[b]
for b in UB: ref_of(b)
# ---- Blender
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=D + r'\FBX\Furina_cm.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]; body = [o for o in bpy.data.objects if o.type == 'MESH'][0]
def bname(u):
    if u in arm.data.bones: return u
    v = u.replace('-', ' ')
    return v if v in arm.data.bones else None
pairs = [(u, bname(u)) for u in UB if bname(u)]
OUT['n_pairs'] = len(pairs); OUT['unmatched_ue'] = [u for u in UB if not bname(u)][:20]
# Phi: arm_space = s*A*ue + b  (Umeyama, 반사 허용)
X = np.array([ref_cs[u][1] for u, b in pairs]); Y = np.array([list(arm.data.bones[b].head_local) for u, b in pairs])
xc = X.mean(0); yc = Y.mean(0); Xc = X - xc; Yc = Y - yc
U_, S_, Vt = np.linalg.svd(Yc.T @ Xc)
best = None
for d in (1, -1):
    Dm = np.diag([1, 1, d]); A = U_ @ Dm @ Vt
    s = np.trace(np.diag(S_) @ Dm) / (Xc ** 2).sum()
    bvec = yc - s * A @ xc; err = np.linalg.norm((s * (A @ X.T)).T + bvec - Y, axis=1)
    if best is None or err.mean() < best[0]: best = (err.mean(), A, s, bvec, err.max())
_, A, s, bvec, emax = best
OUT['phi'] = {'A': A.tolist(), 's': s, 'b': bvec.tolist(), 'err_mean': best[0], 'err_max': emax, 'detA': float(np.linalg.det(A))}
print('PHI', np.round(A, 4).tolist(), round(s, 5), np.round(bvec, 3).tolist(), 'err', round(best[0], 4), round(emax, 4))
def phi(p): return s * (A @ np.array(p)) + bvec
# ---- 포즈 적용 (팔 사슬 + 어깨)
def desc(b):
    out = [b]
    for c in b.children: out += desc(c)
    return out
ARMSET = {'L': [b.name for b in desc(arm.data.bones['Left arm'])], 'R': [b.name for b in desc(arm.data.bones['Right arm'])]}
b2u = {b: u for u, b in pairs}
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='POSE')
pose_err = {}
for side in ('L', 'R'):
    for bn in ARMSET[side]:
        u = b2u.get(bn)
        if u is None: continue
        cs = SM['bones'][u]['cs']; Rp = qmat(cs['q']); Rr = ref_cs[u][0]
        Rd = A @ (Rp @ Rr.T) @ A.T
        bl = arm.data.bones[bn]; R0 = np.array(bl.matrix_local.to_3x3())
        M = np.eye(4); M[:3, :3] = Rd @ R0; M[:3, 3] = phi(cs['loc'])
        arm.pose.bones[bn].matrix = Matrix(M.tolist()); bpy.context.view_layer.update()
# 검증: 자식 머리 위치(포즈) vs UE 자식 위치
for side in ('L', 'R'):
    for bn in ARMSET[side]:
        pb = arm.pose.bones[bn]
        for c in pb.children:
            u = b2u.get(c.name)
            if u is None: continue
            pose_err[c.name] = float(np.linalg.norm(np.array(c.head) - phi(SM['bones'][u]['cs']['loc'])))
OUT['pose_child_err_max'] = max(pose_err.values()) if pose_err else None
# 소매 끝 날개(Sleeve_1..4) 접기: 뼈 방향을 아래팔(elbow) 축 쪽으로 FOLD 비율만큼 회전 (1인칭 정조준에서 안감이 화면을 가리지 않게)
FOLD = float(A_[4]) if len(A_) > 4 else 0.0
OUT['sleeve_fold'] = FOLD
if FOLD != 0:
    for side, sname in (('L', 'Left'), ('R', 'Right')):
        ev = np.array(arm.pose.bones['%s elbow' % sname].matrix)[:3, 1]; ev /= np.linalg.norm(ev)
        if FOLD < 0: ev = -ev   # 음수: 팔꿈치 쪽(뒤)으로 접기
        for k in range(1, 5):
            pb = arm.pose.bones['Sleeve_%d_%s' % (k, side)]; Mx = np.array(pb.matrix); d = Mx[:3, 1] / np.linalg.norm(Mx[:3, 1])
            ax = np.cross(d, ev); sn = np.linalg.norm(ax)
            if sn < 1e-6: continue
            ang = math.atan2(sn, float(np.dot(d, ev))) * abs(FOLD); ax /= sn
            K_ = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); Rf = np.eye(3) + math.sin(ang) * K_ + (1 - math.cos(ang)) * K_ @ K_
            Mx[:3, :3] = Rf @ Mx[:3, :3]; pb.matrix = Matrix(Mx.tolist()); bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode='OBJECT')
# 원래(부모 포함) 위치 확인: UE 월드 손목 vs 굽기 결과
dg = bpy.context.evaluated_depsgraph_get(); be = body.evaluated_get(dg)
me_all = bpy.data.meshes.new_from_object(be, preserve_all_data_layers=True, depsgraph=dg)
B2A = np.array(arm.matrix_world.inverted() @ body.matrix_world)   # body 로컬 -> 아마추어 공간
gi = {g.index: g.name for g in body.vertex_groups}
# ---- 소총 로컬 변환: arm 공간 x -> UE cs -> UE world -> rifle local (UE) -> Blender 내보내기 좌표 y = (ux, -uy, uz)/100
mw = SM['mesh']; rw = SM['rifle']
Rm = qmat(mw['q']); tm = np.array(mw['loc']); sm_ = np.array(mw['scale'])
Rr = qmat(rw['q']); tr = np.array(rw['loc']); sr = np.array(rw['scale'])
Ainv = A.T / s
def arm_to_rifle(x):
    cs = Ainv @ (np.array(x) - bvec); wv = Rm @ (sm_ * cs) + tm; return (Rr.T @ (wv - tr)) / sr
Sx = np.diag([0.01, -0.01, 0.01])
# 선형부 L 과 이동 c (y = L x + c)
c0 = Sx @ arm_to_rifle(np.zeros(3)); L = np.column_stack([Sx @ arm_to_rifle(e) - c0 for e in np.eye(3)])
OUT['L_det'] = float(np.linalg.det(L)); print('L det', OUT['L_det'])
K = np.eye(4); K[:3, :3] = L; K[:3, 3] = c0
KB = K @ B2A
OUT['wrist_rifle_local'] = {}
for u in ('Right-wrist', 'Left-wrist', 'Right-elbow', 'Left-elbow', 'Right-arm', 'Left-arm'):
    OUT['wrist_rifle_local'][u] = arm_to_rifle(phi(SM['bones'][u]['cs']['loc'])).tolist()
    # UE 에서 직접 계산한 값과 비교
    ws = np.array(SM['bones'][u]['ws']['loc']); OUT['wrist_rifle_local'][u + '_ue'] = ((Rr.T @ (ws - tr)) / sr).tolist()
# 카메라(소총 로컬)
cw = np.array(SM['fpcam']['loc']); OUT['cam_rifle_local'] = ((Rr.T @ (cw - tr)) / sr).tolist()
os_dir = D + r'\FBX\FPArms'
import os; os.makedirs(os_dir, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
HANDV = {}
for side, sname in (('L', 'Left'), ('R', 'Right')):
    bs = set(ARMSET[side]); BL = sorted(bs)
    me = me_all.copy(); me.name = 'FPArm' + side
    keep = np.zeros(len(me.vertices), bool)
    dom = me.attributes.new('domb', 'INT', 'POINT')
    for v in body.data.vertices:
        gg = [(g.weight, gi.get(g.group)) for g in v.groups if gi.get(g.group) in bs]
        ws_ = sum(w_ for w_, n_ in gg)
        keep[v.index] = ws_ >= TH
        dom.data[v.index].value = BL.index(max(gg)[1]) if gg else -1
    cutv = me.attributes.new('cutv', 'INT', 'POINT')
    for e in me.edges:
        a, b = e.vertices
        if keep[a] != keep[b]:
            cutv.data[a if keep[a] else b].value = 1
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('SM_FurinaFPArm' + side, me); bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = Matrix(KB.tolist())
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # 사용하지 않는 머티리얼 슬롯 제거
    used = set(p.material_index for p in me.polygons)
    for i in reversed(range(len(ob.material_slots))):
        if i not in used: ob.active_material_index = i; bpy.ops.object.material_slot_remove()
    co = np.array([v.co[:] for v in me.vertices])
    ue = co * np.array([100, -100, 100])
    OUT['side_' + side] = {'nv': len(me.vertices), 'nf': len(me.polygons), 'mats': [m.name for m in me.materials], 'bmin_ue': ue.min(0).tolist(), 'bmax_ue': ue.max(0).tolist()}
    cm_ = np.array([a.value for a in me.attributes['cutv'].data]) == 1
    OUT['side_' + side]['cut_ue'] = np.round(ue[cm_], 3).tolist()
    # 진단: 상태별 카메라(lyra_fp_arms_pose_<CAMT>.json)에서 화면 안 정점을 (주 뼈, 머티리얼)별로
    CAMT = A_[3] if len(A_) > 3 else None
    if CAMT:
        PC = json.load(open(D + r'\Data\lyra_fp_arms_pose_%s.json' % CAMT, encoding='utf-8'))
        vmat = np.zeros(len(me.vertices), int)
        for pl in me.polygons:
            for vi in pl.vertices: vmat[vi] = pl.material_index
        dnames = [BL[a.value] if a.value >= 0 else '' for a in me.attributes['domb'].data]
        diag = {}
        for smp in PC['samples']:
            st = smp.get('state', 'hip'); Rr_ = qmat(smp['rifle']['q']); tr_ = np.array(smp['rifle']['loc']); Rc_ = qmat(smp['fpcam']['q']); tc_ = np.array(smp['fpcam']['loc'])
            cc = Rr_.T @ (tc_ - tr_); RR = Rr_.T @ Rc_; rel = (ue - cc) @ RR; th = math.tan(math.radians(smp.get('fov', 85) / 2)); x = rel[:, 0]
            sx = rel[:, 1] / (th * np.maximum(x, 1e-3)); sy = rel[:, 2] / (th / (2530 / 1448.0) * np.maximum(x, 1e-3))
            vis = (x > 2) & (np.abs(sx) < 1) & (np.abs(sy) < 1)
            g = {}
            for i in np.where(vis)[0]:
                k = '%s|%s' % (dnames[i], me.materials[vmat[i]].name if me.materials else '')
                e = g.setdefault(k, [0, 9, -9, 9, -9]); e[0] += 1; e[1] = min(e[1], sx[i]); e[2] = max(e[2], sx[i]); e[3] = min(e[3], sy[i]); e[4] = max(e[4], sy[i])
            diag[st] = {k: [v[0]] + [round(float(t), 2) for t in v[1:]] for k, v in sorted(g.items(), key=lambda kv: -kv[1][0])}
        OUT['side_' + side]['diag'] = diag
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    fn = os_dir + r'\SM_FurinaFPArm%s_%s.fbx' % (side, OTAG)
    bpy.ops.export_scene.fbx(filepath=fn, use_selection=True, object_types={'MESH'}, add_leaf_bones=False, bake_anim=False, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                             mesh_smooth_type='OFF', use_tspace=False, use_mesh_modifiers=False, path_mode='STRIP', use_custom_props=False)
    OUT['side_' + side]['fbx'] = fn
    ob.select_set(False)
    HANDV[side] = (co.copy(), [BL[a.value] if a.value >= 0 else '' for a in me.attributes['domb'].data])
# ---- 접촉 검사: M4 메시(같은 내보내기 좌표계로 다시 가져옴)와 손 정점의 부호 거리(cm, 음수 = 관통)
from mathutils.bvhtree import BVHTree
before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=D + r'\FBX\M4\SK_M4A1.fbx')
RV, RP = [], []
for k in bpy.data.objects.keys():
    o = bpy.data.objects[k]
    if k in before or o.type != 'MESH': continue
    base = len(RV); mw_ = o.matrix_world
    RV += [tuple(mw_ @ v.co) for v in o.data.vertices]; RP += [tuple(base + i for i in p.vertices) for p in o.data.polygons]
bvh = BVHTree.FromPolygons(RV, RP); rv = np.array(RV) * np.array([100, -100, 100])
OUT['rifle_bbox_ue'] = [rv.min(0).tolist(), rv.max(0).tolist()]
CON = {}
for side, (co, names) in HANDV.items():
    per = {}
    for c, nm in zip(co, names):
        if not any(s in nm for s in ('Finger', 'Thumb', 'wrist', 'HandTwist')): continue
        loc, nrm, idx, dist = bvh.find_nearest(Vector(c))
        if loc is None: continue
        sd = dist * (1 if (Vector(c) - loc).dot(nrm) >= 0 else -1) * 100.0
        per.setdefault(nm, []).append(sd)
    CON[side] = {nm: {'n': len(v), 'min': round(min(v), 3), 'p10': round(float(np.percentile(v, 10)), 3), 'med': round(float(np.median(v)), 3),
                      'contact': int(sum(1 for x in v if -0.2 <= x <= 0.3)), 'pen': int(sum(1 for x in v if x < -0.2))} for nm, v in sorted(per.items())}
OUT['contact'] = CON
json.dump(OUT, open(D + r'\Data\fp_arms_bake_%s.json' % OTAG, 'w'), indent=1)
print('FP_ARMS_BAKE_OK', json.dumps({k: OUT[k] for k in ('phi', 'L_det', 'pose_child_err_max')})[:600])
