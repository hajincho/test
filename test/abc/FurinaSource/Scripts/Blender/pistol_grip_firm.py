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
meshes = {}
for cn, fb in (('frame', 'SM_P220_Frame'), ('slide', 'SM_P220_Slide')):
    v, f = load(fb); tf = sh['tf'][cn]; bmin = np.array(tf['bmin']); bmax = np.array(tf['bmax']); best = None
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            a = v[:, list(perm)] * np.array(sg); off = bmin - a.min(0); err = np.abs((a + off).max(0) - bmax).sum()
            if best is None or err < best[0]: best = (err, perm, sg, off)
    err, perm, sg, off = best; local = v[:, list(perm)] * np.array(sg) + off
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
res = {'tag': TAG, 'view': VIEW, 'fingers': {}}
def stage(label):
    chains = {}
    for s in HANDS:
        for f in ('Index', 'Middle', 'Ring', 'Little'):
            r, K = opt_finger(s, f); res['fingers'][s + f] = r; chains[s + f] = K; print(label, s + f, r['delta_deg'], r['before'], '->', r['after'])
        r, K = opt_thumb(s); res['fingers'][s + 'Thumb'] = r; chains[s + 'Thumb'] = K; print(label, s + 'Thumb', r['delta_deg'], r['before'], '->', r['after'])
    return chains
def tsearch(chains, rng, c):
    global OFF
    palms = {s: palm_pt(s) for s in HANDS}; best = None
    for dx, dy, dz in itertools.product(rng, rng, rng):
        OFF = c + np.array([dx, dy, dz]); sc = total(chains, palms) + 0.05 * float(OFF @ OFF)
        if best is None or sc < best[0]: best = (sc, OFF.copy())
    OFF = best[1]; return best
OFF = np.zeros(3); chains = stage('S1')
b1 = tsearch(chains, [x * 0.25 for x in range(-6, 7)], np.zeros(3)); print('T1', [round(float(x), 2) for x in b1[1]], round(b1[0], 3))
chains = stage('S2')
b2 = tsearch(chains, [x * 0.25 for x in range(-2, 3)], OFF.copy()); print('T2', [round(float(x), 2) for x in b2[1]], round(b2[0], 3))
res['t_world'] = [float(x) for x in OFF]; res['score_after'] = float(b2[0])
json.dump(res, open(D + r'\pistol_grip_firm_%s.json' % TAG, 'w'), indent=1); print('GRIP_FIRM_OK')
