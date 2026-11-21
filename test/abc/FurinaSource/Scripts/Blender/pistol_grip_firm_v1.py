"""blender -b --python pistol_grip_firm.py -- <side_probe 태그> <R|L|RL> [뷰=left]
 실제 UE 변환(side probe tf/bones/bone_q)으로 손가락을 권총 그립에 '꽉 쥐게' 하는 추가 굽힘 Δ(도)를 구한다. (현재 포즈 = 잠금된 대기 자세 기준)
 - 손가락: 마디별 Δ(MCP/PIP/DIP) 격자 탐색, 점수 = 관통*3 + 접촉 간격(PIP/DIP/끝이 표면+0.25cm 이내가 목표) + 작은 정규화
 - 검지(Index): 방아쇠 손가락이라 간격 목표 없이 관통만 피함(옵션 --index)
 - 엄지: 끝이 프레임 옆면에 닿도록
 출력: Data/pistol_grip_firm_<태그>.json : 뼈별 axis_local(뼈 로컬), Δ(도), 점수 전/후.   CR 적용은 lyra_cr_pistol_grip_apply.py"""
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
def sdist(p):
    q = Vector(p); hit = tree.find_nearest(q)
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
LEN3 = {'Index': 1.98, 'Middle': 2.0, 'Ring': 1.9, 'Little': 1.5}; RAD = (0.8, 0.65, 0.5)
def chain(s, f):
    Jn = [B['%sFinger%d_%s' % (f, i, s)] for i in (1, 2, 3)]; d3 = qmat(BQ['%sFinger3_%s' % (f, s)]) @ np.array([0, -1.0, 0]); return Jn + [Jn[2] + d3 * LEN3[f]]
def flex_normal(Jn):
    n = np.cross(Jn[1] - Jn[0], Jn[2] - Jn[1]) + np.cross(Jn[2] - Jn[1], Jn[3] - Jn[2])
    return n / np.linalg.norm(n) if np.linalg.norm(n) > 1e-3 else None
def evalc(Jn, goal):
    pen = 0.0
    for k in range(3):
        for t in (0.0, 0.5, 1.0): pen += max(0.0, RAD[k] - sdist(Jn[k] + (Jn[k + 1] - Jn[k]) * t))
    gap = 0.0
    if goal:
        for p, r in ((Jn[1], RAD[1]), (Jn[2], RAD[1]), (Jn[3], RAD[2])): gap += max(0.0, sdist(p) - (r + 0.25))
    return pen, gap
def qaa(ax, deg):
    ax = np.array(ax) / np.linalg.norm(ax); h = math.radians(deg) / 2; return np.array([ax[0] * math.sin(h), ax[1] * math.sin(h), ax[2] * math.sin(h), math.cos(h)])
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])
STEP = [-15, 0, 10, 20, 30, 40, 55]
R = {'tag': TAG, 'view': VIEW, 'fingers': {}}
def tchain(s):
    Jn = [B['Thumb%d_%s' % (i, s)] for i in range(3)]; d2 = qmat(BQ['Thumb2_%s' % s]) @ np.array([0, -1.0, 0]); return Jn + [Jn[2] + d2 * 2.0]

if 'shift' in A:
    # 총 이동 t(월드, cm) 탐색: 점을 -t 만큼 이동해 평가(= 총을 +t 이동). 오른손 침투 + 손바닥 접촉 간격, 왼손은 가중치 0.5
    def hand_pts(s):
        pts = []
        for f in ('Index', 'Middle', 'Ring', 'Little'):
            Jn = chain(s, f)
            for k in range(3):
                for t_ in (0.0, 0.5, 1.0): pts.append((Jn[k] + (Jn[k + 1] - Jn[k]) * t_, RAD[k]))
        Jt = tchain(s) if 'tchain' in globals() else [B['Thumb%d_%s' % (i, s)] for i in range(3)]
        for k in range(len(Jt) - 1):
            for t_ in (0.0, 0.5, 1.0): pts.append((Jt[k] + (Jt[k + 1] - Jt[k]) * t_, RAD[min(k, 2)]))
        wr = B['%s-wrist' % ('Right' if s == 'R' else 'Left')]; f1 = np.mean([B['%sFinger1_%s' % (f, s)] for f in ('Index', 'Middle', 'Ring', 'Little')], axis=0)
        pts.append(((wr * 0.5 + f1 * 0.5), 1.2))
        return pts, (wr * 0.5 + f1 * 0.5)
    HP = {s_: hand_pts(s_) for s_ in 'RL'}
    def score(t):
        tot = 0.0
        for s_, w in (('R', 1.0), ('L', 0.5)):
            pts, palm = HP[s_]
            for p, r in pts: tot += w * max(0.0, r - sdist(p - t))
            tot += w * 0.5 * max(0.0, sdist(palm - t) - 1.5)
        return tot
    best = None
    rng = [-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]
    for tx, ty, tz in itertools.product(rng, rng, rng):
        t = np.array([tx, ty, tz]); sc = score(t) + 0.05 * float(t @ t)
        if best is None or sc < best[0]: best = (sc, t)
    print('SHIFT_COARSE', [round(x, 2) for x in best[1]], round(best[0], 3))
    c = best[1]; fine = [-0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75]
    for dx, dy, dz in itertools.product(fine, fine, fine):
        t = c + np.array([dx, dy, dz]); sc = score(t) + 0.05 * float(t @ t)
        if sc < best[0]: best = (sc, t)
    def dump(t, tag):
        for s_ in 'RL':
            pts, palm = HP[s_]
            row = [round(sdist(p - t) - r, 2) for p, r in pts]
            print('DUMP', tag, s_, 'clearance(d-r) per pt:', row, 'palm d:', round(sdist(palm - t), 2))
    dump(np.zeros(3), 't0'); dump(best[1], 'best')
    print('SHIFT_BASE', round(score(np.zeros(3)), 3), 'BEST', [round(x, 2) for x in best[1]], round(best[0], 3))
    json.dump({'t_world': best[1].tolist(), 'score0': score(np.zeros(3)), 'score': best[0]}, open(D + r'\pistol_shift_%s.json' % TAG, 'w')); sys.exit(0)

for s in HANDS:
    for f in ('Index', 'Middle', 'Ring', 'Little'):
        Jn = chain(s, f); n = flex_normal(Jn)
        if n is None:
            for g in ('Middle', 'Ring', 'Index', 'Little'):
                n = flex_normal(chain(s, g))
                if n is not None: break
        goal = (f != 'Index'); base = evalc(Jn, goal); bestc = (base[0] * 3 + base[1], (0, 0, 0), base)
        for d1, d2, d3 in itertools.product(STEP, STEP, STEP):
            P0 = [x.copy() for x in Jn]; K1 = [P0[0]] + [rot_about(p, n, P0[0], math.radians(d1)) for p in P0[1:]]
            K2 = K1[:2] + [rot_about(p, n, K1[1], math.radians(d2)) for p in K1[2:]]; K3 = K2[:3] + [rot_about(K2[3], n, K2[2], math.radians(d3))]
            pen, gap = evalc(K3, goal); sc = pen * 3 + gap + 0.0004 * (d1 * d1 + d2 * d2 + d3 * d3) / 10
            if sc < bestc[0]: bestc = (sc, (d1, d2, d3), (pen, gap))
        loc = {}
        for jn in ('Finger1', 'Finger2', 'Finger3'):
            bn = '%s%s_%s' % (f, jn, s); loc[bn] = (qmat(BQ[bn]).T @ n).tolist()
        dqs = {'%s%s_%s' % (f, jn, s): qaa(loc['%s%s_%s' % (f, jn, s)], d).tolist() for jn, d in zip(('Finger1', 'Finger2', 'Finger3'), bestc[1])}
        R['fingers'][s + f] = {'dq': dqs, 'delta_deg': bestc[1], 'before': [round(base[0], 2), round(base[1], 2)], 'after': [round(bestc[2][0], 2), round(bestc[2][1], 2)], 'axis_world': n.tolist(), 'axis_local': loc}
        print(s + f, bestc[1], 'before', [round(x, 2) for x in base], 'after', [round(x, 2) for x in bestc[2]])

def tchain(s):
    Jn = [B['Thumb%d_%s' % (i, s)] for i in range(3)]; d2 = qmat(BQ['Thumb2_%s' % s]) @ np.array([0, -1.0, 0]); return Jn + [Jn[2] + d2 * 2.0]
TSTEP = [-20, 0, 15, 30, 45]; ASTEP = [-30, -15, 0, 15, 30]
for s in HANDS:
    Jn = tchain(s); n = flex_normal(Jn)
    if n is None: n = np.cross(Jn[1] - Jn[0], np.array([0, 0, 1.0])); n /= np.linalg.norm(n)
    dirv = (Jn[3] - Jn[0]); m = np.cross(n, dirv); m /= np.linalg.norm(m)
    def thumb_eval(K):
        pen = 0.0
        for k in range(3):
            for t in (0.0, 0.5, 1.0): pen += max(0.0, RAD[k] - sdist(K[k] + (K[k + 1] - K[k]) * t))
        gap = max(0.0, sdist(K[3]) - (RAD[2] + 0.25)) + 0.5 * max(0.0, sdist(K[2]) - (RAD[1] + 0.4))
        return pen, gap
    base = thumb_eval(Jn); bestt = (base[0] * 3 + base[1], (0, 0, 0, 0), base)
    for a, d0, d1, d2_ in itertools.product(ASTEP, TSTEP, TSTEP, TSTEP):
        P = [rot_about(x, m, Jn[0], math.radians(a)) for x in Jn]; n2 = np.array(rot_about(n, m, np.zeros(3), math.radians(a)))
        K1 = [P[0]] + [rot_about(p, n2, P[0], math.radians(d0)) for p in P[1:]]
        K2 = K1[:2] + [rot_about(p, n2, K1[1], math.radians(d1)) for p in K1[2:]]
        K3 = K2[:3] + [rot_about(K2[3], n2, K2[2], math.radians(d2_))]
        pen, gap = thumb_eval(K3); sc = pen * 3 + gap + 0.0004 * (a * a + d0 * d0 + d1 * d1 + d2_ * d2_) / 10
        if sc < bestt[0]: bestt = (sc, (a, d0, d1, d2_), (pen, gap))
    a, d0, d1, d2_ = bestt[1]
    # 로컬 델타: Thumb0 = Q(m_local,a) * Q(n_local,d0), Thumb1 = Q(n_local,d1), Thumb2 = Q(n_local,d2)
    ml = qmat(BQ['Thumb0_%s' % s]).T @ m
    dq = {}
    for i, d in zip((0, 1, 2), (d0, d1, d2_)):
        bn = 'Thumb%d_%s' % (i, s); nl = qmat(BQ[bn]).T @ n
        q = qaa(nl, d)
        if i == 0: q = qmul(qaa(ml, a), q)
        dq[bn] = q.tolist()
    R['fingers'][s + 'Thumb'] = {'dq': dq, 'delta_deg': bestt[1], 'before': [round(base[0], 2), round(base[1], 2)], 'after': [round(bestt[2][0], 2), round(bestt[2][1], 2)]}
    print(s + 'Thumb', bestt[1], 'before', [round(x, 2) for x in base], 'after', [round(x, 2) for x in bestt[2]])
json.dump(R, open(D + r'\pistol_grip_firm_%s.json' % TAG, 'w'), indent=1); print('GRIP_FIRM_OK')
