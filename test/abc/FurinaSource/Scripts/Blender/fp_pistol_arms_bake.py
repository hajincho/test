"""blender -b --python fp_pistol_arms_bake.py -- <포즈 태그(p..)> <출력 태그> [샘플=4] [소매접기=-0.9]
 1인칭 전용 권총 팔(권총 프레임과 한몸):
  1) UE 1인칭 권총 자세(Data/lyra_fp_arms_pose_<태그>.json)로 Furina 팔 포즈.
  2) 손 위치/방향 = Armpist.fbx(실제 권총 1인칭 애니) 손 관절을 P220 프레임 좌표로 옮긴 목표에 가중 Kabsch 강체 정합(손목+MCP+엄지 근위).
     팔은 2본 IK(어깨 고정, 팔꿈치 평면 유지; 닿지 않으면 어깨를 손 쪽으로 이동 - 1인칭에서 어깨 끝은 보이지 않음).
  3) 손가락/엄지 굽힘 격자 탐색: P220 메시(왼손은 오른손 캡슐 포함)에 관통 없이(반경 근위 .8/중위 .65/말단 .5) 표면에 닿게(+.25) + FBX 관절 모양 유지.
     오른손 검지는 방아쇠 손가락: FBX 목표 위주 + 관통 금지.
  4) 팔 정점(가중치 합 >= .5)만 떼어 'FurinaPistolFrame 로컬 좌표'로 굽기 -> FBX/FPArms/SM_FurinaFPPistArm<L|R>_<출력>.fbx
  5) 실제 피부 정점-P220 부호 거리 보고 -> Data/fp_pistol_arms_bake_<출력>.json"""
import bpy, bmesh, json, sys, math, itertools
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
A_ = sys.argv[sys.argv.index('--') + 1:]; TAG = A_[0]; OTAG = A_[1]; SI = int(A_[2]) if len(A_) > 2 else 4; FOLD = float(A_[3]) if len(A_) > 3 else -0.9
TH = 0.5
PRESS = (A_[5] if len(A_) > 5 else '1') == '1'   # 손바닥 밀착 탐색(이동만)
RIGID = (A_[6] if len(A_) > 6 else '1') == '1'   # 손 6자유도 밀착 탐색
HM = dict(kv.split('=') for kv in (A_[4] if len(A_) > 4 else 'R=fbx,L=keep').split(','))   # 손 배치: fbx(Armpist 정합) | keep(캡처 위치 유지)
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
P = json.load(open(D + r'\Data\lyra_fp_arms_pose_%s.json' % TAG, encoding='utf-8'))
S0 = P['samples'][0]; SM = P['samples'][SI]
assert SM.get('pistol_on'), 'pose is not pistol'
OUT = {'tag': OTAG, 'pose_tag': TAG, 'sample': SI, 'fold': FOLD, 'hand_mode': HM}
def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def rotm(ax, ang):
    ax = np.array(ax, float); ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K
def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); c = np.cross(a, b); sn = np.linalg.norm(c)
    if sn < 1e-9: return np.eye(3)
    return rotm(c, math.atan2(sn, float(a @ b)))
def rot_about(p, a, o, ang): return o + rotm(a, ang) @ (np.array(p) - o)
# ---- UE 참조 포즈(cs)
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
    if best is None or err.mean() < best[0]: best = (err.mean(), A, s, bvec, err.max())
_, A, s, bvec, emax = best; OUT['phi_err'] = [best[0], emax]
def phi(p): return s * (A @ np.array(p)) + bvec
mw = SM['mesh']; Rm = qmat(mw['q']); tm = np.array(mw['loc']); sm_ = np.array(mw['scale'])
def w2a(w): return phi(Rm.T @ (np.array(w) - tm) / sm_)          # UE 월드 -> 아마추어 공간
Ainv = A.T / s
def a2w(x): cs = Ainv @ (np.array(x) - bvec); return Rm @ (sm_ * cs) + tm
def desc(b):
    out = [b]
    for c in b.children: out += desc(c)
    return out
ARMSET = {'L': [b.name for b in desc(arm.data.bones['Left arm'])], 'R': [b.name for b in desc(arm.data.bones['Right arm'])]}
b2u = {b: u for u, b in pairs}
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='POSE')
for side in ('L', 'R'):
    for bn in ARMSET[side]:
        u = b2u.get(bn)
        if u is None: continue
        cs = SM['bones'][u]['cs']; Rd = A @ (qmat(cs['q']) @ ref_cs[u][0].T) @ A.T
        M = np.eye(4); M[:3, :3] = Rd @ np.array(arm.data.bones[bn].matrix_local.to_3x3()); M[:3, 3] = phi(cs['loc'])
        arm.pose.bones[bn].matrix = Matrix(M.tolist()); bpy.context.view_layer.update()
PB = arm.pose.bones
def pm(bn): return np.array(PB[bn].matrix)
def setm(bn, R3, t):
    M = np.eye(4); M[:3, :3] = R3; M[:3, 3] = t; PB[bn].matrix = Matrix(M.tolist()); bpy.context.view_layer.update()
def head(bn): return np.array(PB[bn].head)
# ---- P220 메시 (프레임/슬라이드) -> 아마추어 공간
FR = SM['FurinaPistolFrame']; SLD = SM['FurinaPistolSlide']
def load(nm):
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=D + r'\Data\p220_export\%s.fbx' % nm)
    V = []; F = []; off = 0; objs = []
    for k in list(bpy.data.objects.keys()):
        if k in before or bpy.data.objects[k].type != 'MESH': continue
        if k.startswith('UCX_'): objs.append(bpy.data.objects[k]); continue   # 충돌용 볼록 껍질 제외
        o = bpy.data.objects[k]; M = np.array(o.matrix_world); co = np.array([v.co[:] for v in o.data.vertices]); w = (co @ M[:3, :3].T + M[:3, 3]) * 100.0
        V.append(w); F += [[off + i for i in p.vertices] for p in o.data.polygons]; off += len(w); objs.append(o)
    for o in objs: bpy.data.objects.remove(o, do_unlink=True)
    return np.vstack(V), F
def fitmap(v, tf):
    bmin = np.array(tf['bmin']); bmax = np.array(tf['bmax']); bb = None
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            a = v[:, list(perm)] * np.array(sg); off = bmin - a.min(0); err = np.abs((a + off).max(0) - bmax).sum()
            if bb is None or err < bb[0]: bb = (err, perm, sg, off)
    return bb
bpy.ops.object.mode_set(mode='OBJECT')
RAWF, FF = load('SM_P220_Frame'); RAWS, FS = load('SM_P220_Slide')
mf = fitmap(RAWF, FR); msd = fitmap(RAWS, SLD); OUT['p220_fit_err'] = [mf[0], msd[0]]
def raw_to_local(p, mp): return np.array(p)[..., list(mp[1])] * np.array(mp[2]) + mp[3]
def local_to_world(l, tf): return (np.array(l) * np.array(tf['scale'])) @ qmat(tf['q']).T + np.array(tf['loc'])
GA = np.array([w2a(x) for x in local_to_world(raw_to_local(RAWF, mf), FR)]); GS = np.array([w2a(x) for x in local_to_world(raw_to_local(RAWS, msd), SLD)])
GV = np.vstack([GA, GS]); GF = FF + [[i + len(GA) for i in p] for p in FS]
tree = BVHTree.FromPolygons([Vector(x) for x in GV], GF)
DIRS = [Vector((0.31, 0.77, 0.55)).normalized(), Vector((-0.6, 0.2, 0.77)).normalized(), Vector((0.1, -0.9, 0.42)).normalized()]
def sd_gun(p):
    q = Vector(p); hit = tree.find_nearest(q)
    if hit[0] is None: return 99.0
    votes = 0
    for dr in DIRS:
        n = 0; o = q.copy()
        for _ in range(40):
            h = tree.ray_cast(o, dr)
            if h[0] is None: break
            n += 1; o = h[0] + dr * 1e-4
        votes += n % 2
    return -hit[3] if votes >= 2 else hit[3]
CAPS = []   # 장애물 캡슐(오른손): (a, b, r)
def sd_caps(p):
    best = 99.0
    for a, b, r in CAPS:
        ab = b - a; t = min(1.0, max(0.0, float((p - a) @ ab / max(ab @ ab, 1e-9)))); best = min(best, float(np.linalg.norm(p - (a + ab * t))) - r)
    return best
def sdist(p): return min(sd_gun(p), sd_caps(p)) if CAPS else sd_gun(p)
# ---- FBX(Armpist) 목표 관절 -> P220 원본 -> 프레임 로컬 -> 월드 -> 아마추어
FB = json.load(open(D + r'\Data\pistol_fbx_bounds.json', encoding='utf-8')); FBb = FB['bones']
Ab = {'f': (np.array(FB['frame']['min']), np.array(FB['frame']['max'])), 's': (np.array(FB['slide']['min']), np.array(FB['slide']['max']))}
Afc = (Ab['f'][0] + Ab['f'][1]) / 2; Asc = (Ab['s'][0] + Ab['s'][1]) / 2; Pfc = (RAWF.min(0) + RAWF.max(0)) / 2; Psc = (RAWS.min(0) + RAWS.max(0)) / 2
bestr = None
for perm2 in itertools.permutations(range(3)):
    for sg2 in itertools.product((1, -1), repeat=3):
        Mx = np.zeros((3, 3))
        for i, j in enumerate(perm2): Mx[i, j] = sg2[i]
        if np.linalg.det(Mx) <= 0: continue
        e = np.abs(np.abs(Mx @ (Ab['f'][1] - Ab['f'][0])) - (RAWF.max(0) - RAWF.min(0))).sum() + 3 * np.abs(Mx @ (Asc - Afc) - (Psc - Pfc)).sum()
        if bestr is None or e < bestr[0]: bestr = (e, Mx)
Mf = bestr[1]; OUT['fbx_map_err'] = bestr[0]
def fbx_to_arm(p): return w2a(local_to_world(raw_to_local(Mf @ (np.array(p) - Afc) + Pfc, mf), FR))
FING = {'Index': ('.004', '.005', '.006', '.007'), 'Middle': ('.008', '.009', '.010', '.011'), 'Ring': ('.012', '.013', '.014', '.015'), 'Little': ('.016', '.017', '.018', '.019')}
def fbx_targets(sd):
    h = lambda n: np.array(FBb[n][0]); t = lambda n: np.array(FBb[n][1]); T = {'wrist': h('Hand_' + sd)}
    for f, (m0, m1, m2, m3) in FING.items():
        T[f + '_MCP'] = t('Bone_%s%s' % (sd, m0)); T[f + '_PIP'] = t('Bone_%s%s' % (sd, m1)); T[f + '_DIP'] = t('Bone_%s%s' % (sd, m2)); T[f + '_tip'] = t('Bone_%s%s' % (sd, m3))
    T['Thumb0'] = h('Bone_%s.020' % sd); T['Thumb1'] = t('Bone_%s.020' % sd); T['Thumb2'] = t('Bone_%s.021' % sd); T['Thumb_tip'] = t('Bone_%s.022' % sd)
    return {k: fbx_to_arm(v) for k, v in T.items()}
LEN3 = {'Index': 1.98, 'Middle': 2.0, 'Ring': 1.9, 'Little': 1.5}
def tip_dir(b3, b2):
    # 끝마디 방향: 휴식 자세에서 (b3 머리 - b2 머리)에 가장 가까운 뼈 로컬 축을 포즈에서 사용
    R0 = np.array(arm.data.bones[b3].matrix_local.to_3x3()); d0 = np.array(arm.data.bones[b3].head_local) - np.array(arm.data.bones[b2].head_local); d0 /= np.linalg.norm(d0)
    axs = [(R0[:, i] * sg) for i in range(3) for sg in (1, -1)]; k = int(np.argmax([a @ d0 for a in axs])); i, sg = k // 2, (1, -1)[k % 2]
    return np.array(PB[b3].matrix)[:3, i] * sg
def joints(sd):
    S = 'Right' if sd == 'R' else 'Left'; J = {'wrist': head('%s wrist' % S)}
    for f in FING:
        for i, nm in zip((1, 2, 3), ('MCP', 'PIP', 'DIP')): J['%s_%s' % (f, nm)] = head('%sFinger%d_%s' % (f, i, sd))
        J[f + '_tip'] = J[f + '_DIP'] + tip_dir('%sFinger3_%s' % (f, sd), '%sFinger2_%s' % (f, sd)) * LEN3[f]
    for i in range(3): J['Thumb%d' % i] = head('Thumb%d_%s' % (i, sd))
    J['Thumb_tip'] = J['Thumb2'] + tip_dir('Thumb2_%s' % sd, 'Thumb1_%s' % sd) * 2.0
    return J
W = {'wrist': 0.3}
for f in FING: W.update({f + '_MCP': 1.5, f + '_PIP': 1.0, f + '_DIP': 0.6, f + '_tip': 0.4})
W.update({'Thumb0': 0.5, 'Thumb1': 1.0, 'Thumb2': 1.0, 'Thumb_tip': 0.8})
def kabsch(Pd, Qd, keys):
    P_ = np.array([Pd[k] for k in keys]); Q_ = np.array([Qd[k] for k in keys]); w = np.array([W[k] for k in keys]); w = w / w.sum()
    pc = (P_ * w[:, None]).sum(0); qc = (Q_ * w[:, None]).sum(0); H = ((P_ - pc) * w[:, None]).T @ (Q_ - qc); U, S2, Vt2 = np.linalg.svd(H)
    dd = np.sign(np.linalg.det(Vt2.T @ U.T)); Rk = Vt2.T @ np.diag([1, 1, dd]) @ U.T; return Rk, qc - Rk @ pc
def place_hand(sd, TW):
    S = 'Right' if sd == 'R' else 'Left'; J = joints(sd)
    keys = ['wrist'] + [f + '_MCP' for f in FING] + ['Thumb0', 'Thumb1']
    Rk, tk = kabsch(J, TW, keys); res = {'rigid_err_before': {k: round(float(np.linalg.norm(J[k] - TW[k])), 2) for k in keys}}
    Mw = pm('%s wrist' % S); Rw_new = Rk @ Mw[:3, :3]; T = Rk @ Mw[:3, 3] + tk
    Sp = head('%s arm' % S); E = head('%s elbow' % S); Wo = Mw[:3, 3]; L1 = np.linalg.norm(E - Sp); L2 = np.linalg.norm(Wo - E)
    dist = np.linalg.norm(T - Sp); res['reach'] = [round(float(dist), 2), round(float(L1 + L2), 2)]
    shift = np.zeros(3)
    if dist > (L1 + L2) * 0.985: shift = (T - Sp) * (1 - (L1 + L2) * 0.985 / dist)
    Sp2 = Sp + shift; u = (T - Sp2) / np.linalg.norm(T - Sp2); dd = np.linalg.norm(T - Sp2)
    v = (E - Sp) - ((E - Sp) @ u) * u; v = v / np.linalg.norm(v)
    ca = (L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd); al = math.acos(max(-1.0, min(1.0, ca))); E2 = Sp2 + L1 * (math.cos(al) * u + math.sin(al) * v)
    Ma = pm('%s arm' % S); setm('%s arm' % S, rot_between(E - Sp, E2 - Sp2) @ Ma[:3, :3], Sp2)
    Me = pm('%s elbow' % S); Wc = pm('%s wrist' % S)[:3, 3]; setm('%s elbow' % S, rot_between(Wc - Me[:3, 3], T - Me[:3, 3]) @ Me[:3, :3], Me[:3, 3])
    setm('%s wrist' % S, Rw_new, T)
    J2 = joints(sd); res['shoulder_shift'] = shift.round(2).tolist(); res['wrist_err'] = round(float(np.linalg.norm(J2['wrist'] - T)), 3)
    res['rigid_err_after'] = {k: round(float(np.linalg.norm(J2[k] - TW[k])), 2) for k in keys}
    return res
# ---- 설계 목표(P220 그립 실측 단면 기반, 프레임 로컬 UE: X 총구, Y 총의 오른쪽, Z 위) -> 아마추어 공간
#  그립: 뒷면 x = -4.25 + (z+8)*0.323, 앞면 x = 1.72 + (z+8)*0.227 (z -8..-2), 폭 y -1.03..1.47, 방아쇠울 아래 z -2.5, 방아쇠 x 5~6.5 z -1.5~-0.5
def gback(z): return -4.25 + (z + 8) * 0.323
def gfront(z): return 1.72 + (z + 8) * 0.227
def sem_targets(sd):
    T = {}
    if sd == 'R':   # 사격 손(해머 그립): 손바닥 = 오른쪽 면+뒷면, MCP 줄 = 오른쪽 면 앞쪽 62%, 엄지 = 왼쪽 면 위
        for f, z, yo in (('Index', -1.6, 2.4), ('Middle', -3.2, 2.6), ('Ring', -4.9, 2.6), ('Little', -6.4, 2.4)):
            T[f + '_MCP'] = [gback(z) + 0.62 * (gfront(z) - gback(z)), yo, z]
        T['wrist'] = [gback(-4.0) - 4.2, 1.3, -4.6]
        T['Thumb0'] = [gback(-2.6) - 1.0, -0.4, -2.6]; T['Thumb1'] = [-1.9, -2.0, -1.0]
        T['Index_tip'] = [5.2, 0.35, -1.2]; T['Thumb_tip'] = [3.0, -1.75, 0.0]   # 검지 끝 = 방아쇠 앞면, 엄지 끝 = 왼쪽 면 프레임 윗선
    else:          # 지지 손(엄지 앞으로): MCP 줄 = 그립 앞-왼쪽(오른손가락 바깥), 손바닥 = 왼쪽 면, 엄지 = 왼쪽 면 오른엄지 아래 앞으로
        for f, z in (('Index', -3.0), ('Middle', -4.6), ('Ring', -6.1), ('Little', -7.5)):
            T[f + '_MCP'] = [gfront(z) + 0.6, -3.2, z]
        T['wrist'] = [gback(-7.0) + 0.5, -4.4, -9.3]
        T['Thumb0'] = [-1.2, -2.9, -3.6]; T['Thumb1'] = [1.6, -2.6, -2.0]
        T['Thumb_tip'] = [6.6, -1.65, -1.2]   # 지지 엄지 = 방아쇠울 위 프레임 왼쪽 면을 따라 앞으로
    return {k: w2a(local_to_world(np.array(v, float), FR)) for k, v in T.items()}
# ---- 손가락/손 최적화: 실제 피부 정점(주 뼈에 강체로 붙였다고 근사)과 장애물(P220, 왼손일 때는 오른손 피부)의 부호 거리
def chain(sd, f): J = joints(sd); return [J[f + '_MCP'], J[f + '_PIP'], J[f + '_DIP'], J[f + '_tip']]
def tchain(sd): J = joints(sd); return [J['Thumb0'], J['Thumb1'], J['Thumb2'], J['Thumb_tip']]
def flex_normal(K):
    n = np.cross(K[1] - K[0], K[2] - K[1]) + np.cross(K[2] - K[1], K[3] - K[2]); l = np.linalg.norm(n)
    return n / l if l > 1e-3 else None
HANDB = {}
for sd, S_ in (('R', 'Right'), ('L', 'Left')):
    HANDB[sd] = set(['%s wrist' % S_, 'zHandTwist_%s' % sd] + ['%sFinger%d_%s' % (f, i, sd) for f in FING for i in (1, 2, 3)] + ['Thumb%d_%s' % (i, sd) for i in range(3)])
gi_ = {g.index: g.name for g in body.vertex_groups}; DOMV = {'R': ([], []), 'L': ([], [])}
for v in body.data.vertices:
    gg = [(g.weight, gi_.get(g.group)) for g in v.groups]
    if not gg: continue
    w_, nm_ = max(gg)
    for sd in ('R', 'L'):
        if nm_ in HANDB[sd]: DOMV[sd][0].append(v.index); DOMV[sd][1].append(nm_)
DOMV = {k: (np.array(v[0]), v[1]) for k, v in DOMV.items()}
B2A_ = np.array(arm.matrix_world.inverted() @ body.matrix_world)
def skin(sd):
    bpy.context.view_layer.update(); dg_ = bpy.context.evaluated_depsgraph_get(); be_ = body.evaluated_get(dg_); me_ = be_.to_mesh()
    idx, bn = DOMV[sd]; co = np.array([me_.vertices[int(i)].co[:] for i in idx]); be_.to_mesh_clear()
    return co @ B2A_[:3, :3].T + B2A_[:3, 3], bn
def orient_sign(t, verts):
    c = np.array(verts).mean(0); far = c + np.array([500.0, 300.0, 200.0]); loc, nrm, _, d = t.find_nearest(Vector(far))
    return 1.0 if (Vector(far) - loc).dot(nrm) >= 0 else -1.0
TREES = [(tree, orient_sign(tree, GV))]; OUT['gun_normal_sign'] = TREES[0][1]
def sdf(Pts, trees):
    out = np.empty(len(Pts))
    for i, p in enumerate(Pts):
        v = Vector(p); b = 99.0
        for t, sg_ in trees:
            loc, nrm, _, d = t.find_nearest(v)
            if loc is None: continue
            x = d if (v - loc).dot(nrm) * sg_ >= 0 else -d
            if x < b: b = x
        out[i] = b
    return out
def move_wrist(sd, Rw_new, T):
    S = 'Right' if sd == 'R' else 'Left'
    Sp = head('%s arm' % S); E = head('%s elbow' % S); Wo = pm('%s wrist' % S)[:3, 3]; L1 = np.linalg.norm(E - Sp); L2 = np.linalg.norm(Wo - E)
    dist = np.linalg.norm(T - Sp); shift = np.zeros(3)
    if dist > (L1 + L2) * 0.985: shift = (T - Sp) * (1 - (L1 + L2) * 0.985 / dist)
    Sp2 = Sp + shift; u = (T - Sp2) / np.linalg.norm(T - Sp2); dd = np.linalg.norm(T - Sp2)
    v = (E - Sp) - ((E - Sp) @ u) * u; v = v / np.linalg.norm(v)
    ca = (L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd); al = math.acos(max(-1.0, min(1.0, ca))); E2 = Sp2 + L1 * (math.cos(al) * u + math.sin(al) * v)
    Ma = pm('%s arm' % S); setm('%s arm' % S, rot_between(E - Sp, E2 - Sp2) @ Ma[:3, :3], Sp2)
    Me = pm('%s elbow' % S); Wc = pm('%s wrist' % S)[:3, 3]; setm('%s elbow' % S, rot_between(Wc - Me[:3, 3], T - Me[:3, 3]) @ Me[:3, :3], Me[:3, 3])
    setm('%s wrist' % S, Rw_new, T); return shift
def press(sd, trees):
    S = 'Right' if sd == 'R' else 'Left'; P_, bn = skin(sd)
    pal = set(['%s wrist' % S] + ['%sFinger1_%s' % (f, sd) for f in FING] + ['Thumb0_%s' % sd]); Q = P_[np.array([b in pal for b in bn])]
    Q = Q[::2]; c = Q.mean(0); loc = trees[0][0].find_nearest(Vector(c))[0]; u = np.array(loc) - c; u /= np.linalg.norm(u)
    p1 = np.cross(u, [0, 0, 1.0]); p1 = p1 / np.linalg.norm(p1) if np.linalg.norm(p1) > 1e-3 else np.array([1.0, 0, 0]); p2 = np.cross(u, p1)
    best = None
    for lam in np.arange(-1.5, 3.01, 0.25):
        for a in (-1.0, -0.5, 0, 0.5, 1.0):
            for b in (-1.0, -0.5, 0, 0.5, 1.0):
                t = u * lam + p1 * a + p2 * b; sv = sdf(Q + t, trees)
                pen = float(np.sum(np.clip(-sv - 0.05, 0, None))); con = int(np.sum((sv > -0.05) & (sv < 0.25)))
                sc = 20 * pen - 0.05 * con + 0.05 * float(np.linalg.norm(t))
                if best is None or sc < best[0]: best = (sc, t, pen, con)
    sv0 = sdf(Q, trees); r = {'t': best[1].round(2).tolist(), 'pen_before': round(float(np.sum(np.clip(-sv0 - 0.05, 0, None))), 2), 'con_before': int(np.sum((sv0 > -0.05) & (sv0 < 0.25))), 'pen_after': round(best[2], 2), 'con_after': best[3]}
    Mw = pm('%s wrist' % S); r['shoulder_shift'] = move_wrist(sd, Mw[:3, :3], Mw[:3, 3] + best[1]).round(2).tolist(); return r
def rigid_fit(sd, trees, TWd=None):
    # 손 전체 강체 6자유도(손바닥 중심 기준 회전 + 이동) 국소 탐색: 손바닥/근위 마디/엄지 뿌리가 관통 없이 닿게 (FBX 자세에서 너무 벗어나지 않게 정규화)
    S = 'Right' if sd == 'R' else 'Left'; P_, bn = skin(sd); bn = np.array(bn)
    grp = {'palm': ['%s wrist' % S], 'M1': ['MiddleFinger1_%s' % sd], 'R1': ['RingFinger1_%s' % sd], 'L1': ['LittleFinger1_%s' % sd], 'I1': ['IndexFinger1_%s' % sd], 'T0': ['Thumb0_%s' % sd]}
    G = {k: P_[np.isin(bn, v)][::2] for k, v in grp.items()}
    want = {'palm': 0.1, 'M1': 0.15, 'R1': 0.15, 'L1': 0.3, 'T0': 0.25} if sd == 'R' else {'palm': 0.1, 'M1': 0.3, 'R1': 0.3, 'I1': 0.3}
    c = G['palm'].mean(0)
    J0 = joints(sd); AK = [k for k in (['wrist', 'Thumb0', 'Thumb1'] + [f + '_MCP' for f in FING]) if TWd is not None and k in TWd]
    def tf(p):
        Rd = rotm([1, 0, 0], math.radians(p[0])) @ rotm([0, 1, 0], math.radians(p[1])) @ rotm([0, 0, 1], math.radians(p[2])); t = np.array(p[3:])
        return Rd, t
    def score(p):
        Rd, t = tf(p); pen = 0.0; gap = 0.0; con = 0
        for k, Q in G.items():
            sv = sdf((Q - c) @ Rd.T + c + t, trees); pen += float(np.sum(np.clip(-sv - 0.05, 0, None))); con += int(np.sum((sv > -0.05) & (sv < 0.25)))
            if k in want: gap += max(0.0, float(sv.min()) - want[k])
        att = sum(float(np.linalg.norm((Rd @ (J0[k] - c) + c + t) - TWd[k])) for k in AK) * 0.25
        if sd == 'R' and TWd is not None and 'Index_tip' in TWd:   # 검지가 방아쇠에 닿을 수 있는 거리(MCP-방아쇠 <= 4.3)
            att += 2.0 * max(0.0, float(np.linalg.norm((Rd @ (J0['Index_MCP'] - c) + c + t) - TWd['Index_tip'])) - 4.3)
        if np.abs(p[:3]).max() > 10.01 or np.abs(p[3:]).max() > 1.001: return 1e9, 0, 0, 0   # 설계 자세 근처로 제한
        return 20 * pen + gap - 0.01 * con + 0.03 * float(np.linalg.norm(p[3:])) + 0.004 * float(np.abs(p[:3]).sum()) + att, pen, gap, con
    p = np.zeros(6); best = score(p); s0 = best
    for stepA, stepT in ((8.0, 1.0), (4.0, 0.5), (2.0, 0.25), (1.0, 0.125)):
        improved = True
        while improved:
            improved = False
            for i in range(6):
                for sg in (1, -1):
                    q = p.copy(); q[i] += sg * (stepA if i < 3 else stepT); sc = score(q)
                    if sc[0] < best[0] - 1e-6: p, best, improved = q, sc, True
    Rd, t = tf(p); Mw = pm('%s wrist' % S); T = c + Rd @ (Mw[:3, 3] - c) + t
    shift = move_wrist(sd, Rd @ Mw[:3, :3], T)
    return {'p': p.round(2).tolist(), 'before': [round(s0[1], 2), round(s0[2], 2), s0[3]], 'after': [round(best[1], 2), round(best[2], 2), best[3]], 'shoulder_shift': shift.round(2).tolist()}
def bone_sets(sd, bones):
    P_, bn = skin(sd); Ms = [pm(b) for b in bones]; H = [M[:3, 3] for M in Ms]; Rs = [M[:3, :3] for M in Ms]
    offs = [((P_[np.array([x == b for x in bn])] - H[k]) @ Rs[k])[::2] for k, b in enumerate(bones)]
    return H, Rs, offs
def shape_cost(K, TWd, keys, wt): return 0.0 if TWd is None else wt * sum(float(np.linalg.norm(K[i] - TWd[k])) for i, k in keys if k in TWd)
def score_chain(V, mode, trees):
    s_ = [sdf(v, trees) for v in V]; pen = sum(float(np.sum(np.clip(-x - 0.05, 0, None))) for x in s_)
    if mode == 'wrap': gap = sum(max(0.0, float(x.min()) - 0.12) for x in s_)
    elif mode == 'trigger': gap = max(0.0, float(s_[2].min()) - 0.15)
    else: gap = max(0.0, float(s_[1].min()) - 0.15) + max(0.0, float(s_[2].min()) - 0.12)   # 엄지: 중간/끝 마디
    return pen, gap
def pose_chain(H, Rs, offs, n, ds, pre):
    # 같은 축 n 으로 관절마다 ds 만큼 굽힘 (pre: 첫 관절 앞 추가 회전 = 엄지 벌림)
    acc = pre; accs = []; hs = []; Vs = []; Rn = []
    for k in range(3):
        acc = rotm(n, math.radians(ds[k])) @ acc; accs.append(acc)
        hs.append(H[0] if k == 0 else hs[k - 1] + accs[k - 1] @ (H[k] - H[k - 1]))
        Rk = acc @ Rs[k]; Rn.append(Rk); Vs.append(hs[k] + offs[k] @ Rk.T)
    return Vs, hs, Rn
def opt_chain(sd, bones, mode, grid, trees, K0, TWd=None, keys=None, wt=0.0, thumb=False):
    H, Rs, offs = bone_sets(sd, bones)
    n = flex_normal(K0)
    if n is None:
        for g in ('Middle', 'Ring', 'Little'):
            n = flex_normal(chain(sd, g))
            if n is not None: break
    m = np.cross(n, K0[3] - K0[0]); m /= np.linalg.norm(m)
    tipoff = Rs[2].T @ (K0[3] - H[2])
    def evalc(a, ds):
        pre = rotm(m, math.radians(a)); n2 = pre @ n
        Vs, hs, Rn = pose_chain(H, Rs, offs, n2, ds, pre)
        pen, gap = score_chain(Vs, mode, trees)
        Kp = hs + [hs[2] + Rn[2] @ tipoff]
        return 4 * pen + gap + shape_cost(Kp, TWd, keys, wt) + 0.0001 * (a * a + sum(d * d for d in ds)) / 10, pen, gap
    best = None
    for a in grid.get('a', [0]):
        for ds in itertools.product(*grid['d']):
            sc, pen, gap = evalc(a, ds)
            if best is None or sc < best[0]: best = (sc, a, ds, pen, gap)
    a0, d0 = best[1], best[2]
    for da in ((-5, 0, 5) if 'a' in grid else (0,)):
        for dd in itertools.product((-5, -2.5, 0, 2.5, 5), repeat=3):
            a = a0 + da; ds = tuple(x + y for x, y in zip(d0, dd)); sc, pen, gap = evalc(a, ds)
            if sc < best[0]: best = (sc, a, ds, pen, gap)
    base = evalc(0, (0, 0, 0))
    a, ds = best[1], best[2]; pre = rotm(m, math.radians(a)); n2 = pre @ n; acc = pre
    for k, b in enumerate(bones):
        acc = rotm(n2, math.radians(ds[k])) @ acc; M = pm(b); setm(b, acc @ Rs[k], M[:3, 3])
    return {'abd': a, 'deg': [float(x) for x in ds], 'before': [round(base[1], 2), round(base[2], 2)], 'after': [round(best[3], 2), round(best[4], 2)]}
GRID_F = {'d': [(-20, -10, 0, 10, 20, 30, 45, 60, 75)] * 3}
GRID_T = {'a': (-30, -15, 0, 15, 30), 'd': [(-20, 0, 15, 30, 45)] * 3}
GRID_I = {'a': (-30, -20, -10, 0, 10, 20, 30), 'd': [(-20, -10, 0, 15, 30, 45, 60)] * 3}   # 방아쇠 검지: 옆 벌림 포함
bpy.ops.object.mode_set(mode='POSE')
OUT['hands'] = {}
for sd in ('R', 'L'):
    TW = sem_targets(sd) if HM.get(sd) == 'sem' else fbx_targets(sd); r = place_hand(sd, TW) if HM.get(sd) in ('fbx', 'sem') else {'mode': 'keep'}
    TREES_CUR = TREES
    if sd == 'L':   # 왼손 장애물 = 총 + 오른손 피부
        bpy.context.view_layer.update(); dg_ = bpy.context.evaluated_depsgraph_get(); be_ = body.evaluated_get(dg_); me_ = be_.to_mesh()
        ridx = set(int(i) for i in DOMV['R'][0]); co = np.array([v.co[:] for v in me_.vertices]) @ B2A_[:3, :3].T + B2A_[:3, 3]
        faces = [list(pl.vertices) for pl in me_.polygons if all(int(x) in ridx for x in pl.vertices)]; be_.to_mesh_clear()
        rt = BVHTree.FromPolygons([Vector(x) for x in co], faces); TREES_CUR = TREES + [(rt, orient_sign(rt, co[sorted(ridx)]))]
        OUT['rhand_faces'] = len(faces)
    if PRESS: r['press'] = press(sd, TREES_CUR)
    if RIGID: r['rigid'] = rigid_fit(sd, TREES_CUR, TW if HM.get(sd) == 'sem' else None)
    r['fingers'] = {}
    TWd = TW if HM.get(sd) in ('fbx', 'sem') else None
    for f in ('Middle', 'Ring', 'Little', 'Index'):
        trig = (sd == 'R' and f == 'Index')
        bones = ['%sFinger%d_%s' % (f, i, sd) for i in (1, 2, 3)]
        r['fingers'][f] = opt_chain(sd, bones, 'trigger' if trig else 'wrap', GRID_I if trig else GRID_F, TREES_CUR, chain(sd, f), TWd, [(1, f + '_PIP'), (2, f + '_DIP'), (3, f + '_tip')], 1.0 if trig else 0.05)
    r['fingers']['Thumb'] = opt_chain(sd, ['Thumb%d_%s' % (i, sd) for i in range(3)], 'thumb', GRID_T, TREES_CUR, tchain(sd), TWd, [(3, 'Thumb_tip')], 0.4, thumb=True)
    OUT['hands'][sd] = r; print('HAND', sd, json.dumps(r)[:1500])
Rf0 = qmat(FR['q']); tf0 = np.array(FR['loc'])
def a2f(x): return (Rf0.T @ (a2w(x) - tf0)) / np.array(FR['scale'])
OUT['joints_frame'] = {sd: {k: np.round(a2f(v), 2).tolist() for k, v in joints(sd).items()} for sd in ('R', 'L')}
# 소매 접기 (소총 팔과 같은 처리)
if FOLD != 0:
    for side, sname in (('L', 'Left'), ('R', 'Right')):
        ev = pm('%s elbow' % sname)[:3, 1]; ev = ev / np.linalg.norm(ev)
        if FOLD < 0: ev = -ev
        for k in range(1, 5):
            bn = 'Sleeve_%d_%s' % (k, side); Mx = pm(bn); d = Mx[:3, 1] / np.linalg.norm(Mx[:3, 1]); ax = np.cross(d, ev); sn = np.linalg.norm(ax)
            if sn < 1e-6: continue
            setm(bn, rotm(ax, math.atan2(sn, float(d @ ev)) * abs(FOLD)) @ Mx[:3, :3], Mx[:3, 3])
bpy.ops.object.mode_set(mode='OBJECT')
# ---- 메시 굽기 (프레임 로컬)
dg = bpy.context.evaluated_depsgraph_get(); be = body.evaluated_get(dg)
me_all = bpy.data.meshes.new_from_object(be, preserve_all_data_layers=True, depsgraph=dg)
B2A = np.array(arm.matrix_world.inverted() @ body.matrix_world); gi = {g.index: g.name for g in body.vertex_groups}
Rf_ = qmat(FR['q']); tf_ = np.array(FR['loc']); sf_ = np.array(FR['scale'])
def arm_to_frame(x): return (Rf_.T @ (a2w(x) - tf_)) / sf_
Sx = np.diag([0.01, -0.01, 0.01]); c0 = Sx @ arm_to_frame(np.zeros(3)); L = np.column_stack([Sx @ arm_to_frame(e) - c0 for e in np.eye(3)])
OUT['L_det'] = float(np.linalg.det(L)); K4 = np.eye(4); K4[:3, :3] = L; K4[:3, 3] = c0; KB = K4 @ B2A
OUT['wrist_frame_local'] = {S: arm_to_frame(head('%s wrist' % S)).tolist() for S in ('Right', 'Left')}
cw = np.array(SM['fpcam']['loc']); OUT['cam_frame_local'] = ((Rf_.T @ (cw - tf_)) / sf_).tolist()
os_dir = D + r'\FBX\FPArms'; HANDV = {}
for side in ('L', 'R'):
    bs = set(ARMSET[side]); BL = sorted(bs); me = me_all.copy(); me.name = 'FPPistArm' + side
    keep = np.zeros(len(me.vertices), bool); dom = me.attributes.new('domb', 'INT', 'POINT')
    for v in body.data.vertices:
        gg = [(g.weight, gi.get(g.group)) for g in v.groups if gi.get(g.group) in bs]
        keep[v.index] = sum(w_ for w_, n_ in gg) >= TH; dom.data[v.index].value = BL.index(max(gg)[1]) if gg else -1
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('SM_FurinaFPPistArm' + side, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = Matrix(KB.tolist())
    bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    used = set(p.material_index for p in me.polygons)
    for i in reversed(range(len(ob.material_slots))):
        if i not in used: ob.active_material_index = i; bpy.ops.object.material_slot_remove()
    co = np.array([v.co[:] for v in me.vertices]); ue = co * np.array([100, -100, 100])
    OUT['side_' + side] = {'nv': len(me.vertices), 'mats': [m.name for m in me.materials], 'bmin_ue': ue.min(0).tolist(), 'bmax_ue': ue.max(0).tolist()}
    fn = os_dir + r'\SM_FurinaFPPistArm%s_%s.fbx' % (side, OTAG)
    bpy.ops.export_scene.fbx(filepath=fn, use_selection=True, object_types={'MESH'}, add_leaf_bones=False, bake_anim=False, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                             mesh_smooth_type='OFF', use_tspace=False, use_mesh_modifiers=False, path_mode='STRIP', use_custom_props=False)
    OUT['side_' + side]['fbx'] = fn; ob.select_set(False)
    # 실제 피부 정점(아마추어 공간) 접촉 검사용
    HANDV[side] = ([BL[a.value] if a.value >= 0 else '' for a in me.attributes['domb'].data], ue)
# ---- 접촉: 프레임 로컬(UE) 정점 -> 아마추어 공간 아님. 여기서는 P220 을 프레임 로컬로 다시 구성해서 비교
LV = np.vstack([raw_to_local(RAWF, mf), (qmat(FR['q']).T @ (local_to_world(raw_to_local(RAWS, msd), SLD) - tf_).T).T / sf_])
tree2 = BVHTree.FromPolygons([Vector(x) for x in LV], GF)
CON = {}
for side, (names, ue) in HANDV.items():
    per = {}
    for c, nm in zip(ue, names):
        if not any(k in nm for k in ('Finger', 'Thumb', 'wrist', 'HandTwist')): continue
        loc, nrm, idx, dist = tree2.find_nearest(Vector(c))
        if loc is None: continue
        per.setdefault(nm, []).append(dist * (1 if (Vector(c) - loc).dot(nrm) >= 0 else -1))
    CON[side] = {nm: {'n': len(v), 'min': round(min(v), 3), 'p10': round(float(np.percentile(v, 10)), 3), 'med': round(float(np.median(v)), 3), 'contact': int(sum(1 for x in v if -0.2 <= x <= 0.3)), 'pen': int(sum(1 for x in v if x < -0.2))} for nm, v in sorted(per.items())}
OUT['contact'] = CON; OUT['p220_local_bbox'] = [LV.min(0).tolist(), LV.max(0).tolist()]
json.dump(OUT, open(D + r'\Data\fp_pistol_arms_bake_%s.json' % OTAG, 'w'), indent=1)
print('FP_PISTOL_BAKE_OK', OTAG)
