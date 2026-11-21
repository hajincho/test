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

import math
K = json.load(open(D + r'\pistol_roll_constants.json')); Rm = np.array(K['R']); c0 = np.array([0.1, -13.0, -4.0]); t0 = np.array(K['pose'][:3])
FV = (FV - c0) @ Rm.T + c0 + t0; SV = (SV - c0) @ Rm.T + c0 + t0
G = json.load(open(D + r'\lyra_pistol_grip_probe_g15.json')); P['bones'] = G['bones']
allv = np.vstack([FV, SV]); allf = ff + [[i + len(FV) for i in p] for p in sf]
tree = BVHTree.FromPolygons([Vector(x) for x in allv], allf)
DIRS = [Vector((0.31, 0.77, 0.55)).normalized(), Vector((-0.6, 0.2, 0.77)).normalized(), Vector((0.1, -0.9, 0.42)).normalized()]
def sdist(p, off=(0, 0, 0)):
    q = Vector(p) - Vector(off); hit = tree.find_nearest(q)
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
def pts(s):
    W = Vector(B['%s-wrist' % ('Right' if s == 'R' else 'Left')])
    mc = {f: Vector(B['%sFinger1_%s' % (f, s)]) for f in ('Index', 'Middle', 'Ring', 'Little')}; tp = {f: Vector(B['%sFinger3_%s' % (f, s)]) for f in ('Index', 'Middle', 'Ring', 'Little')}
    out = [('palm', (W + sum(mc.values(), Vector()) / 4) / 2, 1.0)]
    for f in mc:
        for t in (0.35, 0.7): out.append(('palm_' + f, W.lerp(mc[f], t), 0.9))
        for t in (0.0, 0.33, 0.66, 1.0): out.append(('fing_' + f, mc[f].lerp(tp[f], t), 0.55))
    th = [Vector(B['Thumb%d_%s' % (i, s)]) for i in range(3)]
    for a, b in zip(th, th[1:]):
        for t in (0.0, 0.5, 1.0): out.append(('thumb', a.lerp(b, t), 0.55))
    return out
def sc(s, off=(0, 0, 0)):
    tot = 0; worst = (0, '')
    for nm, p, r in pts(s):
        d = sdist(p, off); pen = max(0, r - d); tot += pen
        if pen > worst[0]: worst = (round(pen, 2), nm)
    palm = sdist(pts(s)[0][1], off)
    return round(tot, 2), worst, round(palm, 2)
R = {'R': sc('R'), 'L': sc('L')}; print('PEN_G15', R)
best = None
for dx in [x * 0.5 for x in range(-8, 9)]:
    for dy in [x * 0.5 for x in range(-8, 9)]:
        for dz in [x * 0.5 for x in range(-8, 9)]:
            a, w, pm = sc('L', (-dx, -dy, -dz)); cost = a + max(0, pm - 1.5) + 0.02 * (abs(dx) + abs(dy) + abs(dz))
            if best is None or cost < best[0]: best = (round(cost, 2), (dx, dy, dz), a, w, pm)
print('BEST_L_SHIFT (move left hand by)', best)
json.dump({'now': R, 'best_L': best}, open(D + r'\pistol_pen_check_g15.json', 'w'), default=str)
