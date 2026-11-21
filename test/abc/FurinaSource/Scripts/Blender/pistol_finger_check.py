"""blender.exe -b --python pistol_finger_author.py -- <probe태그>
 1인칭 권총 파지 손가락을 '직접 만든다': 현재 손 뼈 사슬(MCP/PIP/DIP/끝, 소총 컴포넌트 기준 좌표)을 평면 FK 로 마디별 굽힘 증분(Δ MCP, Δ PIP, Δ DIP; 도)만큼 더 굽혀 보고,
 P220 메시(프레임/슬라이드, 1인칭 자세 적용된 상태)에 대한 관통(마디 반경: 근위 0.8 / 중위 0.65 / 말단 0.5 cm)과 접촉(DIP·끝이 표면에서 반경+0.15 이내)을 점수화해 손가락마다 최적 Δ 를 격자 탐색한다.
 입력: Data/lyra_pistol_grip_probe_<태그>.json (bones, bone_q(월드 쿼터니언), bone_lq(부모 기준)), Data/p220_export/*.fbx, Data/pistol_roll_constants.json (총 자세)
 출력: Data/pistol_finger_author_<태그>.json : 뼈별 로컬 굽힘 축(뼈 로컬 좌표)과 Δ(도), 점수 전/후."""
import bpy, json, sys, math, itertools
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
TAG = sys.argv[-1]
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
P = json.load(open(D + '/lyra_pistol_grip_probe_%s.json' % TAG)); B = P['bones']; BQ = P['bone_q']
K = json.load(open(D + '/pistol_roll_constants.json')); Rm = np.array(K['R']); c0 = np.array([0.1, -13.0, -4.0]); t0 = np.array(K['pose'][:3])
G14 = json.load(open(D + '/lyra_pistol_grip_probe_g14.json'))   # 프레임 경계(축 맞춤용, 롤 적용 전)
bpy.ops.wm.read_factory_settings(use_empty=True)
def load(nm):
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=D + r'\p220_export\%s.fbx' % nm)
    V = []; F = []; off = 0
    for k in bpy.data.objects.keys():
        if k in before or bpy.data.objects[k].type != 'MESH': continue
        o = bpy.data.objects[k]; M = np.array(o.matrix_world); co = np.array([v.co[:] for v in o.data.vertices]); w = (co @ M[:3, :3].T + M[:3, 3]) * 100.0
        V.append(w); F += [[off + i for i in p.vertices] for p in o.data.polygons]; off += len(w)
    return np.vstack(V), F
fv, ff = load('SM_P220_Frame'); sv, sf = load('SM_P220_Slide')
fmin = np.array(G14['frame']['rifle_min']); fmax = np.array(G14['frame']['rifle_max']); smin = np.array(G14['slide']['rifle_min']); smax = np.array(G14['slide']['rifle_max'])
best = None
for perm in itertools.permutations(range(3)):
    for sg in itertools.product((1, -1), repeat=3):
        T = lambda v: v[:, list(perm)] * np.array(sg); a = T(fv); b = T(sv); sh = fmin - a.min(0); a2 = a + sh; b2 = b + sh
        err = np.abs(a2.max(0) - fmax).sum() + np.abs(b2.min(0) - smin).sum() + np.abs(b2.max(0) - smax).sum()
        if best is None or err < best[0]: best = (err, perm, sg, sh)
err, perm, sg, sh = best; T = lambda v: v[:, list(perm)] * np.array(sg) + sh
FV = (T(fv) - c0) @ Rm.T + c0 + t0; SV = (T(sv) - c0) @ Rm.T + c0 + t0
allv = np.vstack([FV, SV]); allf = ff + [[i + len(FV) for i in p] for p in sf]
tree = BVHTree.FromPolygons([Vector(x) for x in allv], allf)
DIRS = [Vector((0.31, 0.77, 0.55)).normalized(), Vector((-0.6, 0.2, 0.77)).normalized(), Vector((0.1, -0.9, 0.42)).normalized()]
def sdist(p):
    q = Vector(p); hit = tree.find_nearest(q)
    if hit[0] is None: return 9.0
    d = hit[3]; votes = 0
    for dr in DIRS:
        n = 0; o = q.copy()
        for _ in range(40):
            h = tree.ray_cast(o, dr)
            if h[0] is None: break
            n += 1; o = h[0] + dr * 1e-4
        votes += n % 2
    return -d if votes >= 2 else d
def qmat(q):
    x, y, z, w = q; return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def rot_about(p, a, o, ang):
    a = a / np.linalg.norm(a); v = p - o; c, s = math.cos(ang), math.sin(ang)
    return o + v * c + np.cross(a, v) * s + a * (a @ v) * (1 - c)
LEN3 = {'Index': 1.98, 'Middle': 2.0, 'Ring': 1.9, 'Little': 1.5}
R = {'tag': TAG, 'fingers': {}}
RAD = (0.8, 0.65, 0.5)
def chain(s, f):
    J = [np.array(B['%sFinger%d_%s' % (f, i, s)]) for i in (1, 2, 3)]
    d3 = qmat(BQ['%sFinger3_%s' % (f, s)]) @ np.array([0, -1.0, 0]); tip = J[2] + d3 * LEN3[f]; return J + [tip]
def flex_normal(J):
    n1 = np.cross(J[1] - J[0], J[2] - J[1]); n2 = np.cross(J[2] - J[1], J[3] - J[2]); n = n1 + n2
    return n / np.linalg.norm(n) if np.linalg.norm(n) > 1e-3 else None
def eval_chain(J, tipgoal):
    pen = 0.0; pts = []
    for k in range(3):
        for t in (0.0, 0.5, 1.0): pts.append((J[k] + (J[k + 1] - J[k]) * t, RAD[k]))
    for p, r in pts:
        d = sdist(p); pen += max(0.0, r - d)
    gap = 0.0
    if tipgoal:
        for p, r in ((J[2], RAD[1]), (J[3], RAD[2])): gap += max(0.0, sdist(p) - (r + 0.25))
    return pen, gap

import itertools
rep = {}
for sd in ('R', 'L'):
    for f in ('Index', 'Middle', 'Ring', 'Little'):
        J = chain(sd, f); pen, gap = eval_chain(J, f != 'Index'); rep[sd + f] = [round(pen, 2), round(gap, 2)]
    th = [np.array(B['Thumb%d_%s' % (i, sd)]) for i in range(3)]; d2 = qmat(BQ['Thumb2_%s' % sd]) @ np.array([0, -1.0, 0]); th.append(th[2] + d2 * 2.0)
    rep[sd + 'Thumb'] = [round(eval_chain(th, False)[0], 2), 0]
print('CLEARANCE_G18 (pen, gap)', rep)
json.dump(rep, open(D + '/pistol_finger_clearance_%s.json' % TAG, 'w'))
