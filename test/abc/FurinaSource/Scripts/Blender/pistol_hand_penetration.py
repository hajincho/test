"""blender.exe -b --python pistol_hand_penetration.py -- <probe태그> : 1인칭 권총의 손가락/손바닥이 총 메시를 뚫는지 검사하고, 총(프레임+슬라이드)을 소총 컴포넌트 기준으로 평행이동해 관통이 최소가 되는 위치를 찾는다.
 입력: Data/p220_export/SM_P220_Frame.fbx, SM_P220_Slide.fbx (lyra_export_p220_mesh.py), Data/lyra_pistol_grip_probe_<태그>.json (뼈 위치 + 프레임/슬라이드 경계, 소총 컴포넌트 기준 cm)
 방법: FBX 메시를 프로브의 프레임/슬라이드 경계에 축/부호를 맞춰 소총 기준 좌표로 옮기고, 손 뼈를 따라 점을 촘촘히 뿌려 BVH 로 부호 있는 거리(안쪽 = 음수)를 잰다.
 관통 점수 = sum(max(0, r - d)),  r = 손가락 0.55 / 손바닥 1.0 cm.   -> Data/pistol_hand_penetration_<태그>.json"""
import bpy, json, sys, itertools
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
TAG = sys.argv[-1] if sys.argv[-1] not in ('--',) and not sys.argv[-1].endswith('.py') else 'g14'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
P = json.load(open(D + r'\lyra_pistol_grip_probe_%s.json' % TAG))
bpy.ops.wm.read_factory_settings(use_empty=True)
def load(nm):
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=D + r'\p220_export\%s.fbx' % nm)
    objs = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before and bpy.data.objects[k].type == 'MESH']
    V = []; F = []; off = 0
    for o in objs:
        me = o.data; M = np.array(o.matrix_world)
        co = np.array([v.co[:] for v in me.vertices]); w = (co @ M[:3, :3].T + M[:3, 3]) * 100.0
        V.append(w); F += [[off + i for i in p.vertices] for p in me.polygons]; off += len(w)
    return np.vstack(V), F
fv, ff = load('SM_P220_Frame'); sv, sf = load('SM_P220_Slide')
print('raw frame bbox', fv.min(0), fv.max(0)); print('raw slide bbox', sv.min(0), sv.max(0))
fmin = np.array(P['frame']['rifle_min']); fmax = np.array(P['frame']['rifle_max']); smin = np.array(P['slide']['rifle_min']); smax = np.array(P['slide']['rifle_max'])
def fit():
    best = None
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            T = lambda v: v[:, list(perm)] * np.array(sg)
            a = T(fv); b = T(sv)
            sh = fmin - a.min(0)               # 프레임 경계 최소점 맞춤
            a2 = a + sh; b2 = b + sh
            err = np.abs(a2.max(0) - fmax).sum() + np.abs(b2.min(0) - smin).sum() + np.abs(b2.max(0) - smax).sum()
            if best is None or err < best[0]: best = (err, perm, sg, sh)
    return best
err, perm, sg, sh = fit(); print('axis fit err', err, perm, sg, sh)
T = lambda v: v[:, list(perm)] * np.array(sg) + sh
FV = T(fv); SV = T(sv)
allv = np.vstack([FV, SV]); allf = ff + [[i + len(FV) for i in p] for p in sf]
tree = BVHTree.FromPolygons([Vector(x) for x in allv], allf)
DIRS = [Vector((0.31, 0.77, 0.55)).normalized(), Vector((-0.6, 0.2, 0.77)).normalized(), Vector((0.1, -0.9, 0.42)).normalized()]
import math
from mathutils import Euler, Matrix
PIVOT = Vector((0.1, -13.0, -4.0))
POSE = {'M': Matrix.Identity(3), 't': Vector((0, 0, 0))}
def set_pose(t, rx, ry, rz):
    POSE['M'] = Euler((math.radians(rx), math.radians(ry), math.radians(rz)), 'XYZ').to_matrix(); POSE['t'] = Vector(t)
def sdist(p, off=None):
    q = POSE['M'].transposed() @ (Vector(p) - POSE['t'] - PIVOT) + PIVOT if off is None else Vector(p) - Vector(off)
    hit = tree.find_nearest(q)
    if hit[0] is None: return 9.0
    d = hit[3]; votes = 0
    for dr in DIRS:
        n = 0; o = q.copy()
        for _ in range(60):
            h = tree.ray_cast(o, dr)
            if h[0] is None: break
            n += 1; o = h[0] + dr * 1e-4
        votes += n % 2
    return -d if votes >= 2 else d
B = P['bones']
def pts(hand):
    s = hand; W = Vector(B['%s-wrist' % ('Right' if s == 'R' else 'Left')])
    mc = {f: Vector(B['%sFinger1_%s' % (f, s)]) for f in ('Index', 'Middle', 'Ring', 'Little')}; tp = {f: Vector(B['%sFinger3_%s' % (f, s)]) for f in ('Index', 'Middle', 'Ring', 'Little')}
    out = []
    palm = (W + sum(mc.values(), Vector()) / 4) / 2
    out.append(('palm', palm, 1.0))
    for f in mc:
        for t in (0.35, 0.7): out.append(('palm_' + f, W.lerp(mc[f], t), 0.9))
        for t in (0.0, 0.33, 0.66, 1.0): out.append(('fing_' + f, mc[f].lerp(tp[f], t), 0.55))
    th = [Vector(B['Thumb%d_%s' % (i, s)]) for i in range(3)]
    for a, b in zip(th, th[1:]):
        for t in (0.0, 0.5, 1.0): out.append(('thumb', a.lerp(b, t), 0.55))
    return out
CONTACT = {'palm': 1.5, 'tipMiddle': 1.3, 'tipRing': 1.3, 'tipLittle': 1.3}
def score(hand, off=None):
    tot = 0.0; gap = 0.0; worst = (0, '')
    P_ = pts(hand); tips = {}
    for nm, p, r in P_:
        d = sdist(p, off); pen = max(0.0, r - d); tot += pen
        if pen > worst[0]: worst = (round(pen, 2), nm)
        if nm == 'palm': tips['palm'] = d
    for f in ('Middle', 'Ring', 'Little'):
        tp = Vector(B['%sFinger3_%s' % (f, hand)]); tips['tip' + f] = sdist(tp, off)
    keys = ('palm', 'tipMiddle', 'tipRing', 'tipLittle') if hand == 'R' else ('palm',)
    for k in keys: gap += max(0.0, tips[k] - CONTACT[k])
    return tot + gap, worst, round(tot, 2), round(gap, 2)
R = {'tag': TAG, 'axis': [list(perm), list(sg), [float(x) for x in sh]]}
for hand in ('R', 'L'):
    base, wr, bp, bg = score(hand, (0, 0, 0)); R['base_' + hand] = [round(base, 2), wr, bp, bg]
    best = None
    rng = [x * 0.5 for x in range(-8, 9)]
    for dx in rng:
        for dy in rng:
            for dz in rng:
                s_, w_, sp_, sg_ = score(hand, (dx, dy, dz))
                s_ += 0.02 * (abs(dx) + abs(dy) + abs(dz))     # 작은 이동 선호
                if best is None or s_ < best[0]: best = (s_, (dx, dy, dz), w_, sp_, sg_)
    R['best_' + hand] = [round(best[0], 2), best[1], best[2], best[3], best[4]]
    print(hand, 'base', R['base_' + hand], 'best', R['best_' + hand])

def total(x):
    set_pose(x[:3], x[3], x[4], x[5]); sc = score('R')[0]
    return sc + 0.02 * sum(abs(v) for v in x[:3]) + 0.01 * sum(abs(v) for v in x[3:])
x = list(R['best_R'][1]) + [0.0, 0.0, 0.0]; fx = total(x); steps = [1.0, 1.0, 1.0, 4.0, 4.0, 4.0]; hist = []
for rnd in range(4):
    improved = True
    while improved:
        improved = False
        for i in range(6):
            for sgn in (1, -1):
                y = list(x); y[i] += sgn * steps[i]; fy = total(y)
                if fy < fx - 1e-6: x, fx = y, fy; improved = True
    hist.append([round(fx, 2), [round(v, 2) for v in x]]); steps = [s_ * 0.5 for s_ in steps]
set_pose(x[:3], x[3], x[4], x[5]); fs = score('R')
R['pose_R'] = {'t': [round(v, 2) for v in x[:3]], 'rot_deg_xyz': [round(v, 2) for v in x[3:]], 'score': [round(fx, 2)] + [fs[1], fs[2], fs[3]], 'hist': hist, 'pivot': list(PIVOT)}
print('POSE_R', R['pose_R'])
# 왼손: 오른손 최적 자세를 고정하고 왼손만 평행이동 탐색
def totalL(x):
    set_pose(R['pose_R']['t'], *R['pose_R']['rot_deg_xyz']); 
    ps = pts('L'); tot = 0.0
    for nm, p, r in ps:
        q = Vector(p) + Vector(x)       # 손을 x 만큼 이동 = 총을 -x 이동
        d = sdist(q); tot += max(0.0, r - d)
    qp = Vector(B['Left-wrist']) * 0 + ps[0][1] + Vector(x); gap = max(0.0, sdist(qp) - 1.5)
    return tot + gap + 0.02 * sum(abs(v) for v in x)
xl = [0.0, 0.0, 0.0]; fl = totalL(xl); st = 1.0
for rnd in range(4):
    improved = True
    while improved:
        improved = False
        for i in range(3):
            for sgn in (1, -1):
                y = list(xl); y[i] += sgn * st; fy = totalL(y)
                if fy < fl - 1e-6: xl, fl = y, fy; improved = True
    st *= 0.5
R['shift_L'] = {'dx_dy_dz': [round(v, 2) for v in xl], 'score': round(fl, 2), 'base': round(totalL([0, 0, 0]), 2)}
print('SHIFT_L', R['shift_L'])
json.dump(R, open(D + r'\pistol_hand_penetration_%s.json' % TAG, 'w'), indent=1); print('PEN_OK')
