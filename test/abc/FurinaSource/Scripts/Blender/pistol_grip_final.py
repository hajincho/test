"""blender -b --python pistol_grip_firm.py -- <side_probe 태그> <R|L|RL> [뷰=left]
 실제 UE 변환(side probe tf/bones/bone_q)으로 손가락을 권총 그립에 '꽉 쥐게' 하는 추가 굽힘(뼈 로컬 델타 쿼터니언 dq)과 총 미세 이동 t(월드 cm)를 구한다.
 현재 포즈(잠금된 대기 자세) 기준. 점수 = 침투*3 + 접촉 간격(목표 점이 표면+0.25cm 이내) + 작은 정규화.
 단계: (1) t=0 에서 손가락/엄지 Δ 격자 탐색 -> (2) 그 포즈로 t 탐색(±1.5, 0.25 단위) -> (3) t 에서 Δ 재탐색 -> (4) t 재탐색(±0.5)
 목표 점: 중지/약지/새끼 PIP,DIP,끝 + 엄지 중간/끝 + 손바닥(두께 1.2). 검지는 침투만 피함(방아쇠 손가락).
 출력: Data/pistol_grip_firm_<태그>.json  {fingers: {R_Middle: {dq: {뼈: [x,y,z,w]}, delta_deg}, ...}, t_world, score_after}"""
import bpy, json, sys, itertools, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
A = sys.argv[sys.argv.index('--') + 1:]; TAG = A[0]; HANDS = A[1] if len(A) > 1 else 'R'; VIEW = A[2] if len(A) > 2 else 'left'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
J = json.load(open(D + r'\lyra_pistol_side_probe_%s.json' % TAG)); sh = [s for s in J['shots'] if s['name'] == VIEW][0]; B = {k: np.array(v) for k, v in sh['bones'].items()}; BQ = sh['bone_q']
bpy.ops.wm.read_factory_settings(use_empty=True)
def load(nm):
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=D + r'\p220_export\%s.fbx' % nm)
    V = []; F = []; off = 0
    for k in bpy.data.objects.keys():
        if k in before or bpy.data.objects[k].type != 'MESH': continue
        o = bpy.data.objects[k]; M = np.array(o.matrix_world); co = np.array([v.co[:] for v in o.data.vertices]); w = (co @ M[:3, :3].T + M[:3, 3]) * 100.0
        V.append(w); F += [[off + i for i in p.vertices] for p in o.data.polygons]; off += len(w)
    return np.vstack(V), F
def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
meshes = {}; MAPS = {}; RAW = {}
for cn, fb in (('frame', 'SM_P220_Frame'), ('slide', 'SM_P220_Slide')):
    v, f = load(fb); tf = sh['tf'][cn]; bmin = np.array(tf['bmin']); bmax = np.array(tf['bmax']); best = None
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            a = v[:, list(perm)] * np.array(sg); off = bmin - a.min(0); err = np.abs((a + off).max(0) - bmax).sum()
            if best is None or err < best[0]: best = (err, perm, sg, off)
    err, perm, sg, off = best; local = v[:, list(perm)] * np.array(sg) + off; MAPS[cn] = (perm, sg, off); RAW[cn] = v
    meshes[cn] = ((local * np.array(tf['scale'])) @ qmat(tf['q']).T + np.array(tf['loc']), f)
V0, F0 = meshes['frame']; V1, F1 = meshes['slide']; allv = np.vstack([V0, V1]); allf = F0 + [[i + len(V0) for i in p] for p in F1]
tree = BVHTree.FromPolygons([Vector(x) for x in allv], allf)
DIRS = [Vector((0.31, 0.77, 0.55)).normalized(), Vector((-0.6, 0.2, 0.77)).normalized(), Vector((0.1, -0.9, 0.42)).normalized()]
OFF = np.zeros(3)   # 총 이동 t: 점 p 는 sdist(p - t)
def sdist(p):
    q = Vector(p - OFF); hit = tree.find_nearest(q)
    if hit[0] is None: return 99.0
    d = hit[3]; votes = 0
    for dr in DIRS:
        n = 0; o = q.copy()
        for _ in range(40):
            h = tree.ray_cast(o, dr)
            if h[0] is None: break
            n += 1; o = h[0] + dr * 1e-4
        votes += n % 2
    return -d if votes >= 2 else d
def rot_about(p, a, o, ang):
    a = a / np.linalg.norm(a); v = p - o; c, s = math.cos(ang), math.sin(ang)
    return o + v * c + np.cross(a, v) * s + a * (a @ v) * (1 - c)
def qaa(ax, deg):
    ax = np.array(ax) / np.linalg.norm(ax); h = math.radians(deg) / 2; return np.array([ax[0] * math.sin(h), ax[1] * math.sin(h), ax[2] * math.sin(h), math.cos(h)])
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])
LEN3 = {'Index': 1.98, 'Middle': 2.0, 'Ring': 1.9, 'Little': 1.5}; RAD = (0.8, 0.65, 0.5)
def chain(s, f):
    Jn = [B['%sFinger%d_%s' % (f, i, s)] for i in (1, 2, 3)]; d3 = qmat(BQ['%sFinger3_%s' % (f, s)]) @ np.array([0, -1.0, 0]); return Jn + [Jn[2] + d3 * LEN3[f]]
def tchain(s):
    Jn = [B['Thumb%d_%s' % (i, s)] for i in range(3)]; d2 = qmat(BQ['Thumb2_%s' % s]) @ np.array([0, -1.0, 0]); return Jn + [Jn[2] + d2 * 2.0]
def flex_normal(Jn):
    n = np.cross(Jn[1] - Jn[0], Jn[2] - Jn[1]) + np.cross(Jn[2] - Jn[1], Jn[3] - Jn[2])
    return n / np.linalg.norm(n) if np.linalg.norm(n) > 1e-3 else None
def evalc(K, goal, thumb=False):
    pen = 0.0
    for k in range(3):
        for t in (0.0, 0.5, 1.0): pen += max(0.0, RAD[k] - sdist(K[k] + (K[k + 1] - K[k]) * t))
    gap = 0.0
    if goal:
        if thumb: gap = max(0.0, sdist(K[3]) - (RAD[2] + 0.25)) + 0.5 * max(0.0, sdist(K[2]) - (RAD[1] + 0.4))
        else:
            for p, r in ((K[1], RAD[1]), (K[2], RAD[1]), (K[3], RAD[2])): gap += max(0.0, sdist(p) - (r + 0.25))
    return pen, gap
STEP = [-15, 0, 10, 20, 30, 40, 55]; TSTEP = [-20, 0, 15, 30, 45]; ASTEP = [-30, -15, 0, 15, 30]
def opt_finger(s, f):
    Jn = chain(s, f); n = flex_normal(Jn)
    if n is None:
        for g in ('Middle', 'Ring', 'Index', 'Little'):
            n = flex_normal(chain(s, g))
            if n is not None: break
    goal = (f != 'Index'); base = evalc(Jn, goal); bestc = (base[0] * 3 + base[1], (0, 0, 0), base, Jn)
    for d1, d2, d3 in itertools.product(STEP, STEP, STEP):
        P0 = [x.copy() for x in Jn]; K1 = [P0[0]] + [rot_about(p, n, P0[0], math.radians(d1)) for p in P0[1:]]
        K2 = K1[:2] + [rot_about(p, n, K1[1], math.radians(d2)) for p in K1[2:]]; K3 = K2[:3] + [rot_about(K2[3], n, K2[2], math.radians(d3))]
        pen, gap = evalc(K3, goal); sc = pen * 3 + gap + 0.0004 * (d1 * d1 + d2 * d2 + d3 * d3) / 10
        if sc < bestc[0]: bestc = (sc, (d1, d2, d3), (pen, gap), K3)
    loc = {'%sFinger%d_%s' % (f, i + 1, s): (qmat(BQ['%sFinger%d_%s' % (f, i + 1, s)]).T @ n) for i in range(3)}
    dq = {bn: qaa(ax, d).tolist() for (bn, ax), d in zip(loc.items(), bestc[1])}
    return {'dq': dq, 'delta_deg': bestc[1], 'before': [round(base[0], 2), round(base[1], 2)], 'after': [round(bestc[2][0], 2), round(bestc[2][1], 2)]}, bestc[3]
def opt_thumb(s):
    Jn = tchain(s); n = flex_normal(Jn)
    if n is None: n = np.cross(Jn[1] - Jn[0], np.array([0, 0, 1.0])); n /= np.linalg.norm(n)
    dirv = (Jn[3] - Jn[0]); m = np.cross(n, dirv); m /= np.linalg.norm(m)
    base = evalc(Jn, True, True); bestt = (base[0] * 3 + base[1], (0, 0, 0, 0), base, Jn)
    for a, d0, d1, d2_ in itertools.product(ASTEP, TSTEP, TSTEP, TSTEP):
        P = [rot_about(x, m, Jn[0], math.radians(a)) for x in Jn]; n2 = np.array(rot_about(n, m, np.zeros(3), math.radians(a)))
        K1 = [P[0]] + [rot_about(p, n2, P[0], math.radians(d0)) for p in P[1:]]
        K2 = K1[:2] + [rot_about(p, n2, K1[1], math.radians(d1)) for p in K1[2:]]
        K3 = K2[:3] + [rot_about(K2[3], n2, K2[2], math.radians(d2_))]
        pen, gap = evalc(K3, True, True); sc = pen * 3 + gap + 0.0004 * (a * a + d0 * d0 + d1 * d1 + d2_ * d2_) / 10
        if sc < bestt[0]: bestt = (sc, (a, d0, d1, d2_), (pen, gap), K3)
    a, d0, d1, d2_ = bestt[1]; ml = qmat(BQ['Thumb0_%s' % s]).T @ m; dq = {}
    for i, d in zip((0, 1, 2), (d0, d1, d2_)):
        bn = 'Thumb%d_%s' % (i, s); q = qaa(qmat(BQ[bn]).T @ n, d)
        if i == 0: q = qmul(qaa(ml, a), q)
        dq[bn] = q.tolist()
    return {'dq': dq, 'delta_deg': bestt[1], 'before': [round(base[0], 2), round(base[1], 2)], 'after': [round(bestt[2][0], 2), round(bestt[2][1], 2)]}, bestt[3]
def palm_pt(s):
    wr = B['%s-wrist' % ('Right' if s == 'R' else 'Left')]; f1 = np.mean([B['%sFinger1_%s' % (f, s)] for f in ('Index', 'Middle', 'Ring', 'Little')], axis=0); return wr * 0.5 + f1 * 0.5
def total(chains, palms):
    tot = 0.0
    for key, K in chains.items():
        f = key[1:]; sc = evalc(K, f != 'Index', f == 'Thumb'); tot += sc[0] * 3 + sc[1]
    for p in palms.values(): tot += 0.5 * abs(sdist(p) - 1.2)
    return tot

tfF = sh['tf']['frame']
Pf = RAW['frame']; Ps = RAW['slide']
perm, sg, off = MAPS['frame']
def p220_to_world(p):
    loc = np.array(p)[list(perm)] * np.array(sg) + off
    return (loc * np.array(tfF['scale'])) @ qmat(tfF['q']).T + np.array(tfF['loc'])
FBJ = json.load(open(D + r'\pistol_fbx_bounds.json', encoding='utf-8')); FB = FBJ; FBb = FB['bones']
# Armpist -> P220(Blender) : 회전 24개 + 이동 (프레임 bbox 중심 + 슬라이드 상대 위치로 선택)
Ab = {'f': (np.array(FB['frame']['min']), np.array(FB['frame']['max'])), 's': (np.array(FB['slide']['min']), np.array(FB['slide']['max']))}
Afc = (Ab['f'][0] + Ab['f'][1]) / 2; Asc = (Ab['s'][0] + Ab['s'][1]) / 2
Pfc = (RAW['frame'].min(0) + RAW['frame'].max(0)) / 2; Psc = (RAW['slide'].min(0) + RAW['slide'].max(0)) / 2
rots = []
for perm2 in itertools.permutations(range(3)):
    for sg2 in itertools.product((1, -1), repeat=3):
        M = np.zeros((3, 3))
        for i, j in enumerate(perm2): M[i, j] = sg2[i]
        if np.linalg.det(M) > 0: rots.append(M)
bestr = None
for M in rots:
    ext = np.abs(M @ (Ab['f'][1] - Ab['f'][0])); pext = RAW['frame'].max(0) - RAW['frame'].min(0)
    e = np.abs(ext - pext).sum() + 3 * np.abs(M @ (Asc - Afc) - (Psc - Pfc)).sum()
    if bestr is None or e < bestr[0]: bestr = (e, M)
Mf = bestr[1]
def fbx_to_p220(p): return Mf @ (np.array(p) - Afc) + Pfc
print('FBX->P220 rot err', round(bestr[0], 2), 'M', Mf.tolist())
# FBX 오른손 관절
def head(n): return np.array(FBb[n][0])
def tail(n): return np.array(FBb[n][1])
FING = {'Index': ('.004', '.005', '.006', '.007'), 'Middle': ('.008', '.009', '.010', '.011'), 'Ring': ('.012', '.013', '.014', '.015'), 'Little': ('.016', '.017', '.018', '.019')}
TGT = {}
wrist_f = head('Hand_R'); TGT['wrist'] = wrist_f
for f, (m0, m1, m2, m3) in FING.items():
    TGT[f + '_MCP'] = tail('Bone_R' + m0); TGT[f + '_PIP'] = tail('Bone_R' + m1); TGT[f + '_DIP'] = tail('Bone_R' + m2); TGT[f + '_tip'] = tail('Bone_R' + m3)
TGT['Thumb0'] = head('Bone_R.020'); TGT['Thumb1'] = tail('Bone_R.020'); TGT['Thumb2'] = tail('Bone_R.021'); TGT['Thumb_tip'] = tail('Bone_R.022')
TW = {k: p220_to_world(fbx_to_p220(v)) for k, v in TGT.items()}
# Furina 오른손 관절(현재)
LEN3 = {'Index': 1.98, 'Middle': 2.0, 'Ring': 1.9, 'Little': 1.5}
FJ = {'wrist': B['Right-wrist']}
for f in FING:
    for i, nm in zip((1, 2, 3), ('MCP', 'PIP', 'DIP')): FJ['%s_%s' % (f, nm)] = B['%sFinger%d_R' % (f, i)]
    d3 = qmat(BQ['%sFinger3_R' % f]) @ np.array([0, -1.0, 0]); FJ[f + '_tip'] = FJ[f + '_DIP'] + d3 * LEN3[f]
for i in range(3): FJ['Thumb%d' % i] = B['Thumb%d_R' % i]
d2 = qmat(BQ['Thumb2_R']) @ np.array([0, -1.0, 0]); FJ['Thumb_tip'] = FJ['Thumb2'] + d2 * 2.0
W = {'wrist': 0.3}
for f in FING: W.update({f + '_MCP': 1.5, f + '_PIP': 1.0, f + '_DIP': 0.6, f + '_tip': 0.4})
W.update({'Thumb0': 0.5, 'Thumb1': 1.0, 'Thumb2': 1.0, 'Thumb_tip': 0.8})
# 1단계: 강체 변환(회전 + 이동, 중심 = 손목)만으로 MCP/손목/엄지 근위를 맞춤(손가락 굽힘 고정)
def rot_axis(ax, ang):
    ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K
C0 = FJ['wrist'].copy()
def apply(Rm, t, pts): return {k: Rm @ (v - C0) + C0 + t for k, v in pts.items()}
def cost(pts, keys=None):
    return sum(W[k] * float(np.sum((pts[k] - TW[k]) ** 2)) for k in (keys or pts))
# Kabsch 가중 정합 (MCP/PIP/DIP/손목/엄지)
def kabsch(keys):
    P = np.array([FJ[k] for k in keys]); Q = np.array([TW[k] for k in keys]); w = np.array([W[k] for k in keys]); w = w / w.sum()
    pc = (P * w[:, None]).sum(0); qc = (Q * w[:, None]).sum(0); H = ((P - pc) * w[:, None]).T @ (Q - qc); U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T)); Dm = np.diag([1, 1, d]); Rm = Vt.T @ Dm @ U.T; t = qc - Rm @ pc; return Rm, t
keys_rigid = ['wrist'] + [f + '_MCP' for f in FING] + ['Thumb0', 'Thumb1']
Rk, tk = kabsch(keys_rigid)
# Rm,t : p' = Rk p + tk  (월드).  C0 기준 표현 p' = Rk (p - C0) + C0 + t  -> t = tk + Rk C0 - C0
tC = tk + Rk @ C0 - C0
P1 = apply(Rk, tC, FJ)
# FBX 오른손 관절
def head(n): return np.array(FBb[n][0])
def tail(n): return np.array(FBb[n][1])
FING = {'Index': ('.004', '.005', '.006', '.007'), 'Middle': ('.008', '.009', '.010', '.011'), 'Ring': ('.012', '.013', '.014', '.015'), 'Little': ('.016', '.017', '.018', '.019')}
TGT = {}
wrist_f = head('Hand_R'); TGT['wrist'] = wrist_f
for f, (m0, m1, m2, m3) in FING.items():
    TGT[f + '_MCP'] = tail('Bone_R' + m0); TGT[f + '_PIP'] = tail('Bone_R' + m1); TGT[f + '_DIP'] = tail('Bone_R' + m2); TGT[f + '_tip'] = tail('Bone_R' + m3)
TGT['Thumb0'] = head('Bone_R.020'); TGT['Thumb1'] = tail('Bone_R.020'); TGT['Thumb2'] = tail('Bone_R.021'); TGT['Thumb_tip'] = tail('Bone_R.022')
TW = {k: p220_to_world(fbx_to_p220(v)) for k, v in TGT.items()}
# Furina 오른손 관절(현재)
LEN3 = {'Index': 1.98, 'Middle': 2.0, 'Ring': 1.9, 'Little': 1.5}
FJ = {'wrist': B['Right-wrist']}
for f in FING:
    for i, nm in zip((1, 2, 3), ('MCP', 'PIP', 'DIP')): FJ['%s_%s' % (f, nm)] = B['%sFinger%d_R' % (f, i)]
    d3 = qmat(BQ['%sFinger3_R' % f]) @ np.array([0, -1.0, 0]); FJ[f + '_tip'] = FJ[f + '_DIP'] + d3 * LEN3[f]
for i in range(3): FJ['Thumb%d' % i] = B['Thumb%d_R' % i]
d2 = qmat(BQ['Thumb2_R']) @ np.array([0, -1.0, 0]); FJ['Thumb_tip'] = FJ['Thumb2'] + d2 * 2.0
W = {'wrist': 0.3}
for f in FING: W.update({f + '_MCP': 1.5, f + '_PIP': 1.0, f + '_DIP': 0.6, f + '_tip': 0.4})
W.update({'Thumb0': 0.5, 'Thumb1': 1.0, 'Thumb2': 1.0, 'Thumb_tip': 0.8})
# 1단계: 강체 변환(회전 + 이동, 중심 = 손목)만으로 MCP/손목/엄지 근위를 맞춤(손가락 굽힘 고정)
def rot_axis(ax, ang):
    ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K
C0 = FJ['wrist'].copy()
def apply(Rm, t, pts): return {k: Rm @ (v - C0) + C0 + t for k, v in pts.items()}
def cost(pts, keys=None):
    return sum(W[k] * float(np.sum((pts[k] - TW[k]) ** 2)) for k in (keys or pts))
# Kabsch 가중 정합 (MCP/PIP/DIP/손목/엄지)
def kabsch(keys):
    P = np.array([FJ[k] for k in keys]); Q = np.array([TW[k] for k in keys]); w = np.array([W[k] for k in keys]); w = w / w.sum()
    pc = (P * w[:, None]).sum(0); qc = (Q * w[:, None]).sum(0); H = ((P - pc) * w[:, None]).T @ (Q - qc); U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T)); Dm = np.diag([1, 1, d]); Rm = Vt.T @ Dm @ U.T; t = qc - Rm @ pc; return Rm, t
keys_rigid = ['wrist'] + [f + '_MCP' for f in FING] + ['Thumb0', 'Thumb1']
Rk, tk = kabsch(keys_rigid)
# Rm,t : p' = Rk p + tk  (월드).  C0 기준 표현 p' = Rk (p - C0) + C0 + t  -> t = tk + Rk C0 - C0
tC = tk + Rk @ C0 - C0
P1 = apply(Rk, tC, FJ)

def stage(label):
    chains = {}
    for s in HANDS:
        for f in ('Index', 'Middle', 'Ring', 'Little'):
            r, K = opt_finger(s, f); res['fingers'][s + f] = r; chains[s + f] = K; print(label, s + f, r['delta_deg'], r['before'], '->', r['after'])
        r, K = opt_thumb(s); res['fingers'][s + 'Thumb'] = r; chains[s + 'Thumb'] = K; print(label, s + 'Thumb', r['delta_deg'], r['before'], '->', r['after'])
    return chains

rigid_cost = cost(P1)
print('RIGID cost', round(rigid_cost, 2), {k: round(float(np.linalg.norm(P1[k] - TW[k])), 1) for k in ['wrist', 'Index_MCP', 'Little_MCP', 'Index_PIP', 'Middle_PIP', 'Thumb1', 'Thumb_tip']})
# 손 이동 G 를 B/BQ 에 반영 (손가락 접촉 최적화는 이동된 손 기준)
Gm = Rk; Gt = tC
for k_ in list(B.keys()): B[k_] = Gm @ (B[k_] - C0) + C0 + Gt
BQ = {k_: None for k_ in BQ} if False else BQ
def qmat_rot(Rm_, q): return Rm_ @ qmat(q)
_qm = qmat
def qmat(q):
    if isinstance(q, dict): return q['M']
    return _qm(q)
BQ = {k_: {'M': Gm @ _qm(v)} for k_, v in BQ.items()}
res = {'tag': TAG, 'view': VIEW, 'fingers': {}, 'G': {'Rm': Gm.tolist(), 't': Gt.tolist(), 'c': C0.tolist()}, 'rigid_cost': rigid_cost}
chains = stage('S1')
print('FINAL tags'); json.dump(res, open(D + r'\pistol_grip_final_%s.json' % TAG, 'w'), indent=1); print('GRIP_FINAL_OK')
