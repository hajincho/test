"""손가락 쥐기 - 피부(메시) 기준(2026-11-22).
예전 fpvm_lib2.grip_fingers 는 뼈 선(반지름 0.55cm 캡슐)만 보고 첫 관절부터 하나씩 굽히다 '어느 마디든 닿으면' 멈춤
 -> 손끝이 먼저 닿으면 나머지 관절이 펴진 채 남아 손가락이 총 옆으로 곧게 뻗고(흐느적), 실제 피부는 0.4~1.5cm 총 안으로 들어감.
여기서는 그 손가락의 실제 피부 정점(선형 블렌드 스키닝을 numpy 로 직접 계산)을 세 관절 각도 조합마다 움직여
 - 마디마다 총 표면까지 최소 부호 거리 g_k (안/밖은 6방향 광선이 모두 3cm 안에서 막히면 '안' - 면 법선 방향은 모델마다 뒤집혀 있어 쓰지 않음)
 - 비용 = 50*(파고듦-0.1cm)+ + Σ w_k*g_k(떠 있음) + 자연스러운 굽힘(끝마디≈0.7*가운데마디) 약한 가중
 를 최소로 하는 (a1,a2,a3) 를 거친 격자 -> 세밀 좌표 하강으로 찾음. 펴진 손에서 그 자세까지 가는 길에 총을 뚫고 지나가는 해는 버림.
targets={손가락: (월드 점, 가중)} 이면 그 손가락 끝마디 패드(끝마디 60%)를 점으로 끌어당기고 앞 두 마디의 '떠 있음'은 따지지 않음(방아쇠 검지)."""
import bpy, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
import fpvm_lib as L

DIRS = [Vector(v) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]


def sdist(bvh, p, near=0.03, rng=0.03):
    """부호 거리(m). 표면 3cm 안쪽 점만 6방향 광선으로 안/밖 판정."""
    loc, nrm, _, d = bvh.find_nearest(p)
    if loc is None: return 1.0
    if d < near:
        for dv in DIRS:
            if bvh.ray_cast(p + dv * 1e-5, dv, rng)[0] is None: return d
        return -d
    return d


def body_of(arm):
    """푸리나 팔 메시: 이 아마추어로 변형되고 손가락 정점 그룹이 있는 메시(병과 팔 Arms_* 제외)"""
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name.startswith('Arms_') or 'IndexFinger1_R' not in o.vertex_groups: continue
        if any(m.type == 'ARMATURE' and m.object == arm for m in o.modifiers): return o
    return None


def _np(M): return np.array(M, dtype=float)


def spread_axis(fax_b):
    """첫마디 좌우 벌림 축(뼈 로컬: 길이 축 y × 굽힘 축) - fpvm_pistols2 와 같은 정의"""
    return Vector((0, 1, 0)).cross(Vector(fax_b)).normalized()


class Finger:
    """한 손가락의 피부 정점과 세 뼈 FK(관절 각도 -> 정점 월드 좌표)."""

    def __init__(self, arm, body, s, f, fax, per_phal=45):
        self.bns = L.fbones(s, f); self.pbs = [arm.pose.bones[b] for b in self.bns]; self.fax = [Vector(fax[b]) for b in self.bns]
        self.abd = spread_axis(fax[self.bns[0]]); self.spread = 0.0
        for pb in self.pbs: pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion()
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); be = body.evaluated_get(dg); me = be.to_mesh(); mw = body.matrix_world
        gidx = {body.vertex_groups[b].index: k for k, b in enumerate(self.bns) if b in body.vertex_groups}
        rows, P, Wt = [], [], []
        for v in body.data.vertices:
            tot = sum(g.weight for g in v.groups); w = [0.0, 0.0, 0.0]
            for g in v.groups:
                if g.group in gidx: w[gidx[g.group]] += g.weight
            if tot <= 0 or sum(w) / tot < 0.3: continue
            rows.append(v.index); P.append(tuple(mw @ me.vertices[v.index].co)); Wt.append([x / tot for x in w])
        be.to_mesh_clear()
        P = np.array(P); Wt = np.array(Wt); ph = Wt.argmax(1)
        keep = []
        for k in range(3):
            ids = np.where(ph == k)[0]; keep += list(ids[::max(1, len(ids) // per_phal)])
        keep = np.array(sorted(keep), dtype=int)
        self.P = P[keep]; self.W = Wt[keep]; self.ph = ph[keep]; self.Ph = np.c_[self.P, np.ones(len(self.P))]
        self.M0 = [_np(arm.matrix_world @ pb.matrix) for pb in self.pbs]; self.M0i = [np.linalg.inv(M) for M in self.M0]
        self.L3 = np.array(list((arm.matrix_world @ self.pbs[2].matrix).inverted() @ (arm.matrix_world @ self.pbs[2].head.lerp(self.pbs[2].tail, 0.6))) + [1.0])
        self.Ltip = np.array(list((arm.matrix_world @ self.pbs[2].matrix).inverted() @ (arm.matrix_world @ self.pbs[2].tail)) + [1.0])

    def mats(self, a):
        Ms = []; prev = None
        for k in range(3):
            q = Quaternion(self.fax[k], math.radians(a[k]))
            if k == 0 and self.spread: q = Quaternion(self.abd, math.radians(self.spread)) @ q
            R = np.eye(4); R[:3, :3] = _np(q.to_matrix())
            base = self.M0[k] if prev is None else prev @ self.M0i[k - 1] @ self.M0[k]
            prev = base @ R; Ms.append(prev)
        return Ms

    def verts(self, a):
        Ms = self.mats(a); out = self.P.copy()
        for k in range(3):
            T = Ms[k] @ self.M0i[k]; out += self.W[:, k:k + 1] * ((self.Ph @ T.T)[:, :3] - self.P)
        return out, Ms

    def pad(self, Ms): return (Ms[2] @ self.L3)[:3]


def _eval(F, bvh, a, w, tgt, pen_cap=None):
    V, Ms = F.verts(a); g = [1e9, 1e9, 1e9]
    for p, k in zip(V, F.ph):
        d = sdist(bvh, Vector(p)) * 100
        if d < g[k]: g[k] = d
        if pen_cap is not None and d < -pen_cap: return 1e9, g
    pen = max(0.0, -min(g)); c = 50.0 * max(pen - 0.1, 0.0)
    if tgt is None: c += sum(wk * min(max(gk, 0.0), 4.0) for wk, gk in zip(w, g))
    else:
        c += w[2] * min(max(g[2], 0.0), 4.0) + tgt[1] * np.linalg.norm(F.pad(Ms) - np.array(tgt[0])) * 100
        if len(tgt) > 2:   # 손끝이 목표 면을 넘어 반대편으로 나가면 벌점(0.4cm 넘는 만큼)
            over = float(np.dot((Ms[2] @ F.Ltip)[:3] - np.array(tgt[0]), np.array(tgt[2]))) * 100; c += 5.0 * max(over - 0.4, 0.0)
    c += 0.004 * abs(a[2] - 0.7 * a[1])
    return c, g


def _path_ok(F, bvh, a, n=4, cap=0.5):
    for k in range(1, n):
        V, _ = F.verts([x * k / n for x in a])
        for p in V[::2]:
            if sdist(bvh, Vector(p)) * 100 < -cap: return False
    return True


def solve_finger(F, bvh, lim, thumb=False, tgt=None, step=8):
    w = (0.2, 0.6, 1.0) if thumb else (0.5, 0.8, 1.2)
    if tgt is not None:   # 방아쇠 검지: 먼저 뼈만으로(피부 무시) 패드가 목표에 가장 가까운 벌림 각을 고름
        best = None
        for sp in range(-50, 51, 5):   # 검지 벌림(뿌리 관절 옆으로 + 손 비틀림 몫까지)
            F.spread = float(sp)
            for a1 in range(-16, int(lim[0]) + 1, 8):
                for a2 in range(0, int(lim[1]) + 1, 10):
                    a3 = min(0.7 * a2, lim[2]); d = np.linalg.norm(F.pad(F.mats((a1, a2, a3))) - np.array(tgt[0]))
                    if best is None or d < best[0]: best = (d, sp)
        F.spread = float(best[1])
    cands = []
    for a1 in np.arange(-16 if tgt is not None else 0, lim[0] + 0.1, step):
        for a2 in np.arange(0, lim[1] + 0.1, step):
            for a3 in np.arange(0, lim[2] + 0.1, step):
                if not thumb and abs(a3 - 0.7 * a2) > 30: continue
                c, g = _eval(F, bvh, (a1, a2, a3), w, tgt, pen_cap=1.0)
                if c < 1e8: cands.append((c, (float(a1), float(a2), float(a3))))
    cands.sort(key=lambda x: x[0]); best = None
    for c, a in cands[:12]:
        if _path_ok(F, bvh, a): best = (c, list(a)); break
    if best is None: best = (cands[0][0], list(cands[0][1])) if cands else (0.0, [0.0, 0.0, 0.0])
    c, a = best
    lo = [-16.0 if tgt is not None else 0.0, 0.0, 0.0]   # 방아쇠 검지는 첫마디 약간 젖힘 허용(권총과 같게)
    nv = 4 if tgt is not None else 3   # 방아쇠 검지는 벌림(F.spread, ±30°)도 같이 다듬음
    for st in (4.0, 2.0, 1.0):
        improved = True
        while improved:
            improved = False
            for j in range(nv):
                for sg in (-1, 1):
                    if j == 3:
                        old_sp = F.spread; F.spread = min(max(old_sp + sg * st, -50.0), 50.0); cb, _ = _eval(F, bvh, a, w, tgt)
                        if cb < c - 1e-4: c, improved = cb, True
                        else: F.spread = old_sp
                        continue
                    b = list(a); b[j] = min(max(b[j] + sg * st, lo[j]), lim[j]); cb, _ = _eval(F, bvh, b, w, tgt)
                    if cb < c - 1e-4: c, a, improved = cb, b, True
    _, g = _eval(F, bvh, a, w, tgt); d = {'cost': round(c, 3), 'gap_cm': [round(x, 2) for x in g]}
    if tgt is not None: d['spread'] = F.spread; d['pad_miss_cm'] = round(float(np.linalg.norm(F.pad(F.verts(a)[1]) - np.array(tgt[0]))) * 100, 2)
    return [round(x, 1) for x in a], d


LAST = {}


def grip_fingers_mesh(arm, s, fax, bvh, limits=None, skip=(), preset=None, targets=None, body=None):
    """반환 {뼈: 각도(°)} (fpvm_lib2.grip_fingers 와 같은 꼴). 진단은 LAST[s]."""
    body = body or body_of(arm); lim = limits or {'Thumb': (35, 45, 50), 'default': (85, 100, 75)}
    if bpy.context.object and bpy.context.object.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    for f in L.FINGERS:
        for b in L.fbones(s, f):
            pb = arm.pose.bones[b]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion()
    res = {}; diag = {}
    for f in L.FINGERS:
        bns = L.fbones(s, f)
        if f in skip: res.update({b: 0.0 for b in bns}); continue
        if preset and f in preset: res.update(dict(zip(bns, preset[f]))); continue
        F = Finger(arm, body, s, f, fax); tg = (targets or {}).get(f)
        lm = lim.get(f, lim['default'])
        if f == 'Thumb': lm = (max(lm[0], 35), max(lm[1], 45), max(lm[2], 50))   # 엄지가 반대편까지 감싸게(파고듦은 비용이 막음)
        else: lm = (max(lm[0], 95), max(lm[1], 105), max(lm[2], 80))   # 뿌리 관절 85° 에 걸려 새끼·약지가 덜 감기던 것(실제 굽힘 90~100°)
        a, d = solve_finger(F, bvh, lm, thumb=(f == 'Thumb'), tgt=tg); res.update(dict(zip(bns, a))); diag[f] = d
        if F.spread: res[bns[0] + '@spread'] = F.spread
    import fpvm_lib2; fpvm_lib2.apply_fingers(arm, fax, res)
    bpy.context.view_layer.update(); LAST[s] = diag; print('GRIP_MESH', s, json.dumps(diag)); print('GRIP_ANG', s, json.dumps(res)); return res


def trigger_target(arm, s, bvh, G, fwd=(0.0, -1.0, 0.0), radius_cm=9.0, step_cm=0.35, pad_r_cm=0.75):
    """방아쇠울 안 방아쇠 앞면의 검지 패드 목표(월드). G = 무기 원래 좌표(cm) -> 월드(m) 행렬, fwd = 원래 좌표의 총구 방향.
    검지 뿌리(IndexFinger1 머리) 둘레 radius 안 격자 점 중 '방아쇠울 구멍'(위·아래·앞·뒤 광선은 6cm 안에서 막히고 좌우 광선은 둘 다 빠져나감)을 모으고,
    그중 뒤쪽 광선이 pad_r 근처에서 막히는(= 방아쇠 앞면에 붙은) 점들 가운데 가장 앞쪽 무리의 중앙 높이 점. 반환 (점, 진단)"""
    R3 = G.to_3x3(); Gi = G.inverted()
    ax_x = (R3 @ Vector((1, 0, 0))).normalized(); fw = (R3 @ Vector(fwd)).normalized(); up = (R3 @ Vector((0, 0, 1))).normalized()
    mcp = arm.matrix_world @ arm.pose.bones['IndexFinger1_%s' % s].head; c = Gi @ mcp; r = radius_cm
    def hit(p, d, lim): h = bvh.ray_cast(p + d * 1e-5, d, lim)[0]; return None if h is None else (h - p).length
    holes = []
    ys = np.arange(c.y - r, c.y + r, step_cm); zs = np.arange(c.z - r, c.z + r, step_cm)
    for y in ys:
        for z in zs:
            for x in (0.0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5):   # 총 가운데 면이 원래 좌표 x=0 이 아닌 모델(케이 98k 0.65)
                p = G @ Vector((x, y, z))
                if (p - mcp).length * 100 > r: break
                if hit(p, ax_x, 0.04) is not None or hit(p, -ax_x, 0.04) is not None: continue
                du, dd = hit(p, up, 0.06), hit(p, -up, 0.06); df, db = hit(p, fw, 0.06), hit(p, -fw, 0.06)
                if None in (du, dd, df, db): continue
                holes.append((p, df * 100, db * 100, du * 100, dd * 100)); break
    if not holes: return None, {'holes': 0}
    face = [h for h in holes if h[2] < pad_r_cm + 0.6]
    if not face: return None, {'holes': len(holes), 'face': 0}
    fmax = max(h[0].dot(fw) for h in face); front = [h for h in face if h[0].dot(fw) > fmax - 0.012]
    p = min(front, key=lambda h: (h[0] - mcp).length)[0]   # 방아쇠 앞면 중 검지 뿌리에서 가장 가까운 점(손이 손잡이 아래쪽을 쥔 기관단총도 닿게)
    side = ax_x if (p - mcp).dot(ax_x) > 0 else -ax_x   # 손에서 총 가운데로 가는 옆 방향(넘어가면 벌점)
    return (p, side), {'holes': len(holes), 'face': len(face), 'native_cm': [round(v, 2) for v in (Gi @ p)], 'mcp_native_cm': [round(v, 2) for v in c], 'tip_native_cm': [round(v, 2) for v in (Gi @ (arm.matrix_world @ arm.pose.bones['IndexFinger3_%s' % s].tail))]}
