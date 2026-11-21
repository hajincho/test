"""blender -b --python pistol_grip_pose.py -- <side_probe 태그> [뷰=left]
 오른손이 권총 그립을 '망치 쥐기'로 감싸도록 총의 6자유도(손 기준 위치+회전)를 구한다. (손/손가락 포즈는 고정 = 소총 그립을 쥐던 손)
 원리: 손가락 굽힘축 n(중지/약지/새끼 평균) = 그립 축, 손바닥 점이 뒷면(backstrap)에 닿고 손가락 마디가 앞면을 감싸며 엄지는 왼쪽 면.
 점수 = 침투*3 + 접촉 간격(PIP/DIP/끝 -> 표면 반경+0.25) + 손바닥 접촉(두께 1.2) + 방향 항(손바닥이 그립 '밑면(바닥)'에 닿으면 큰 벌점, 뒷면이면 보상)
 탐색: 초기값 = 축 정렬(g->±n, 뒷면->손바닥) 후보들 + 각 후보 좌표 하강. 출력: Data/pistol_grip_pose_<태그>.json  {vars: {FurinaPFLocX...RotR}, score, T_world}
 총 이동 T: 메시' = Rm (메시 - c) + c + t,  c = 손바닥 점."""
import bpy, json, sys, itertools, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
A = sys.argv[sys.argv.index('--') + 1:]; TAG = A[0]; VIEW = A[1] if len(A) > 1 else 'left'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
J = json.load(open(D + r'\lyra_pistol_side_probe_%s.json' % TAG)); sh = [s for s in J['shots'] if s['name'] == VIEW][0]; B = {k: np.array(v) for k, v in sh['bones'].items()}; BQ = sh['bone_q']
PV = J['pf_vars']
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
Rm = np.eye(3); tt = np.zeros(3); CP = np.zeros(3)
def to_mesh(p): return Rm.T @ (p - CP - tt) + CP      # 손 점 -> 원래 메시 좌표계
def sdist_n(p):
    q = Vector(to_mesh(p)); hit = tree.find_nearest(q)
    if hit[0] is None: return 99.0, np.zeros(3)
    d = hit[3]; votes = 0
    for dr in DIRS:
        n = 0; o = q.copy()
        for _ in range(40):
            h = tree.ray_cast(o, dr)
            if h[0] is None: break
            n += 1; o = h[0] + dr * 1e-4
        votes += n % 2
    nrm = Rm @ np.array(hit[1])   # 메시 표면 법선(바깥)을 월드로
    return (-d if votes >= 2 else d), nrm
LEN3 = {'Index': 1.98, 'Middle': 2.0, 'Ring': 1.9, 'Little': 1.5}; RAD = (0.8, 0.65, 0.5)
s_ = 'R'
def chain(f):
    Jn = [B['%sFinger%d_%s' % (f, i, s_)] for i in (1, 2, 3)]; d3 = qmat(BQ['%sFinger3_%s' % (f, s_)]) @ np.array([0, -1.0, 0]); return Jn + [Jn[2] + d3 * LEN3[f]]
def flex_normal(Jn):
    n = np.cross(Jn[1] - Jn[0], Jn[2] - Jn[1]) + np.cross(Jn[2] - Jn[1], Jn[3] - Jn[2]); return n
CH = {f: chain(f) for f in ('Index', 'Middle', 'Ring', 'Little')}
THJ = [B['Thumb%d_R' % i] for i in range(3)]; d2 = qmat(BQ['Thumb2_R']) @ np.array([0, -1.0, 0]); THJ.append(THJ[2] + d2 * 2.0)
wr = B['Right-wrist']; f1m = np.mean([CH[f][0] for f in ('Middle', 'Ring', 'Little')], axis=0); PALM = wr * 0.45 + f1m * 0.55
nsum = sum(flex_normal(CH[f]) for f in ('Middle', 'Ring', 'Little')); nsum /= np.linalg.norm(nsum)
tips = np.mean([CH[f][3] for f in ('Middle', 'Ring', 'Little')], axis=0)
CP[:] = PALM
# 그립 축(프레임 메시 PCA 중 아래 40%) 과 기준 방향(총구 방향 = 슬라이드+프레임 장축)
tfF = sh['tf']['frame']; Vf = V0
z_lo = np.percentile(Vf @ np.array([0, 0, 1.0]), 40)
gr = Vf[(Vf @ np.array([0, 0, 1.0])) < z_lo]
# 현재 총의 위/앞 방향(월드): 프레임 장축은 PCA, 위쪽은 +Z(월드), 그립 축 = 프레임 아래쪽 점들의 주성분
def pca_axis(P):
    c = P.mean(0); u, s, vt = np.linalg.svd(P - c, full_matrices=False); return vt[0], c
mu_all = np.vstack([V0, V1]); ax_long, c_all = pca_axis(mu_all)
if ax_long @ np.array([1.0, 0, 0]) < 0: ax_long = -ax_long        # 총구 방향(월드 +X 쪽)
ax_grip, c_grip = pca_axis(gr)
if ax_grip @ np.array([0, 0, 1.0]) < 0: ax_grip = -ax_grip         # 그립 위쪽
print('INIT grip_axis', ax_grip.round(3), 'muzzle', ax_long.round(3), 'n_flex', nsum.round(3))
def rot_from_to(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b
    if np.linalg.norm(v) < 1e-8: return np.eye(3) if c > 0 else rot_axis(np.cross(a, [1, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1, 0]), math.pi)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K * (1 / (1 + c))
def rot_axis(ax, ang):
    ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K
# 점수
GRIPLEN = 7.0
def score():
    pen = 0.0; gap = 0.0
    for f in ('Index', 'Middle', 'Ring', 'Little'):
        K = CH[f]
        for k in range(3):
            for t in (0.0, 0.5, 1.0):
                d, _ = sdist_n(K[k] + (K[k + 1] - K[k]) * t); pen += max(0.0, RAD[k] - d)
        if f != 'Index':
            for p, r in ((K[1], RAD[1]), (K[2], RAD[1]), (K[3], RAD[2])):
                d, _ = sdist_n(p); gap += max(0.0, d - (r + 0.25))
    for k in range(3):
        for t in (0.0, 0.5, 1.0):
            d, _ = sdist_n(THJ[k] + (THJ[k + 1] - THJ[k]) * t); pen += max(0.0, RAD[min(k, 2)] - d)
    dT, _ = sdist_n(THJ[3]); gap += 0.5 * max(0.0, dT - (RAD[2] + 0.4))
    dP, nP = sdist_n(PALM); sc = pen * 3 + gap + 1.0 * abs(dP - 1.2)
    # 손바닥 방향: 접촉 법선(바깥) 이 총 '뒤쪽' 이어야 함 (총구 -ax_long 방향), 아래쪽(= 밑면) 이면 벌점
    down = -(Rm @ np.array([0, 0, 1.0])); back = -(Rm @ ax_long)
    if np.linalg.norm(nP) > 0:
        sc += 3.0 * max(0.0, nP @ down - 0.3) + 2.0 * (1.0 - max(-1.0, min(1.0, nP @ (-back) * -1.0 + 0.0)))   # nP 가 back 쪽을 향할수록 좋음
    return sc, pen, gap, dP, nP
def set_T(R_, t_):
    global Rm, tt
    Rm = R_; tt = t_
# 초기값: 총을 '소총 컴포넌트에 대해 3인칭 기본 배치'(회전 yaw90, 위치 (0,-4.27,0.63)) 로 -> 소총을 쥐던 손과 같은 정렬. 이후 작은 회전/이동만 탐색.
Rz90 = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1.0]])
Rf_ = qmat(sh['tf']['frame']['q']); pf_ = np.array(sh['tf']['frame']['loc']); Rr_ = qmat(sh['tf']['rifle']['q']); pr_ = np.array(sh['tf']['rifle']['loc'])
Rf_t = Rr_ @ Rz90; pf_t = pr_ + Rr_ @ np.array([0, -4.27, 0.63])
Rm0 = Rf_t @ Rf_.T; t0 = pf_t - CP - Rm0 @ (pf_ - CP)
R_TP = Rm0.copy()
set_T(Rm0, t0); best = (score()[0], Rm0.copy(), t0.copy())
def ang_from_tp(R_):
    M = R_ @ R_TP.T; c = (np.trace(M) - 1) / 2; return math.degrees(math.acos(max(-1.0, min(1.0, c))))
print('INIT(TP aligned) score', round(best[0], 2))
cur = (best[0] + 0.0, best[1], best[2])
step_t = 1.0; step_r = 12.0
for it in range(6):
    improved = True
    while improved:
        improved = False
        moves = []
        for ax in range(3):
            for sg in (1, -1):
                d = np.zeros(3); d[ax] = sg * step_t; moves.append(('t', cur[1], cur[2] + d))
                a = np.zeros(3); a[ax] = 1; moves.append(('r', rot_axis(a, math.radians(sg * step_r)) @ cur[1], cur[2]))
        for kind, R_, t_ in moves:
            if ang_from_tp(R_) > 25.0: continue
            set_T(R_, t_); sc = score()[0] + 0.01 * ang_from_tp(R_) ** 2
            if sc < cur[0] - 1e-6: cur = (sc, R_.copy(), t_.copy()); improved = True
    step_t *= 0.5; step_r *= 0.5
    print('ITER', it, round(cur[0], 3))
set_T(cur[1], cur[2]); fin = score(); print('ANGLE from TP rel (deg)', round(ang_from_tp(Rm), 1)); print('FINAL score', round(fin[0], 3), 'pen', round(fin[1], 3), 'gap', round(fin[2], 3), 'palm_d', round(fin[3], 3), 'palm_n', fin[4].round(2))
# T(월드) = 회전 Rm 에 대해 c 기준 + t.  프레임 월드 변환 M_f(회전 Rf, 위치 pf) -> M_f' = T o M_f
tf = sh['tf']; Rf = qmat(tf['frame']['q']); pf = np.array(tf['frame']['loc']); Rr = qmat(tf['rifle']['q']); pr = np.array(tf['rifle']['loc'])
Rf2 = Rm @ Rf; pf2 = Rm @ (pf - CP) + CP + tt
# 상대 변환: rel = rifle^-1 o frame
def rel(Rr_, pr_, Rf_, pf_): return Rr_.T @ Rf_, Rr_.T @ (pf_ - pr_)
Rrel0, prel0 = rel(Rr, pr, Rf, pf); Rrel1, prel1 = rel(Rr, pr, Rf2, pf2)
def to_quat(Rm_):
    t = np.trace(Rm_)
    if t > 0: s = math.sqrt(t + 1) * 2; w = 0.25 * s; x = (Rm_[2, 1] - Rm_[1, 2]) / s; y = (Rm_[0, 2] - Rm_[2, 0]) / s; z = (Rm_[1, 0] - Rm_[0, 1]) / s
    elif Rm_[0, 0] > Rm_[1, 1] and Rm_[0, 0] > Rm_[2, 2]: s = math.sqrt(1 + Rm_[0, 0] - Rm_[1, 1] - Rm_[2, 2]) * 2; w = (Rm_[2, 1] - Rm_[1, 2]) / s; x = 0.25 * s; y = (Rm_[0, 1] + Rm_[1, 0]) / s; z = (Rm_[0, 2] + Rm_[2, 0]) / s
    elif Rm_[1, 1] > Rm_[2, 2]: s = math.sqrt(1 + Rm_[1, 1] - Rm_[0, 0] - Rm_[2, 2]) * 2; w = (Rm_[0, 2] - Rm_[2, 0]) / s; x = (Rm_[0, 1] + Rm_[1, 0]) / s; y = 0.25 * s; z = (Rm_[1, 2] + Rm_[2, 1]) / s
    else: s = math.sqrt(1 + Rm_[2, 2] - Rm_[0, 0] - Rm_[1, 1]) * 2; w = (Rm_[1, 0] - Rm_[0, 1]) / s; x = (Rm_[0, 2] + Rm_[2, 0]) / s; y = (Rm_[1, 2] + Rm_[2, 1]) / s; z = 0.25 * s
    return [x, y, z, w]
def quat_to_rpy(q):   # UE FRotator(Pitch,Yaw,Roll) from quaternion (UE 정의)
    x, y, z, w = q; SP = 2.0 * (w * y - z * x)   # 주의: UE 는 SingularityTest = Z*X - W*Y
    sing = z * x - w * y; YawY = 2.0 * (w * z + x * y); YawX = 1.0 - 2.0 * (y * y + z * z); T = 0.4999995
    if sing < -T: pitch = -90.0; yaw = math.degrees(math.atan2(YawY, YawX)); roll = -yaw - math.degrees(2.0 * math.atan2(x, w))
    elif sing > T: pitch = 90.0; yaw = math.degrees(math.atan2(YawY, YawX)); roll = yaw - math.degrees(2.0 * math.atan2(x, w))
    else:
        pitch = math.degrees(math.asin(2.0 * sing)); yaw = math.degrees(math.atan2(YawY, YawX)); roll = math.degrees(math.atan2(-2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y)))
    return pitch, yaw, roll
q1 = to_quat(Rrel1); p_, y_, r_ = quat_to_rpy(q1); q0 = to_quat(Rrel0); p0, y0, r0 = quat_to_rpy(q0)
out = {'tag': TAG, 'score': fin[0], 'pen': fin[1], 'gap': fin[2], 'palm_d': fin[3], 'vars': {'FurinaPFLocX': float(prel1[0]), 'FurinaPFLocY': float(prel1[1]), 'FurinaPFLocZ': float(prel1[2]), 'FurinaPFRotP': p_, 'FurinaPFRotY': y_, 'FurinaPFRotR': r_},
       'vars_check_current': {'loc': prel0.tolist(), 'rot': [p0, y0, r0], 'probe_vars': PV}, 'T': {'Rm': Rm.tolist(), 't': tt.tolist(), 'c': CP.tolist()}}
json.dump(out, open(D + r'\pistol_grip_pose_%s.json' % TAG, 'w'), indent=1); print('GRIP_POSE_OK', json.dumps(out['vars']), 'CHECK', json.dumps(out['vars_check_current']))
