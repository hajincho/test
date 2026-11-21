"""blender -b --python pistol_fit_fbx_grip.py -- <side_probe 태그> [뷰=left]
 Armpist.fbx(실제 권총 FP 애니)의 오른손 관절 위치(Data/pistol_fbx_bounds.json) 를 P220 메시 좌표로 옮겨 '목표 관절 위치' 를 만들고,
 Furina 오른손(현재 포즈: 잠금 상수)이 그 위치에 가도록 손 강체 변환 G(회전+이동, 손목 기준) 와 손가락 굽힘 Δ 를 최소제곱으로 푼다.  총은 월드에 고정.
 대응: 손목=Hand_R 머리, MCP=Finger1 머리(.004 꼬리), PIP=Finger2 머리, DIP=Finger3 머리, 끝=Finger3 머리+방향*길이 / FBX 마지막 마디 꼬리.  (FBX 손이 더 커서 MCP/PIP 가중치를 높게)
 출력: Data/pistol_fit_fbx_<태그>.json {G: {Rm, t, c}, finger_dq, err, targets_world}"""
import bpy, json, sys, itertools, math
import numpy as np
A_ = sys.argv[sys.argv.index('--') + 1:]; TAG = A_[0]; VIEW = A_[1] if len(A_) > 1 else 'left'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
J = json.load(open(D + r'\lyra_pistol_side_probe_%s.json' % TAG)); sh = [s for s in J['shots'] if s['name'] == VIEW][0]; B = {k: np.array(v) for k, v in sh['bones'].items()}; BQ = sh['bone_q']
FB = json.load(open(D + r'\pistol_fbx_bounds.json', encoding='utf-8')); FBb = FB['bones']
bpy.ops.wm.read_factory_settings(use_empty=True)
def load(nm):
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=D + r'\p220_export\%s.fbx' % nm)
    V = []
    for k in bpy.data.objects.keys():
        if k in before or bpy.data.objects[k].type != 'MESH': continue
        o = bpy.data.objects[k]; M = np.array(o.matrix_world); co = np.array([v.co[:] for v in o.data.vertices]); V.append((co @ M[:3, :3].T + M[:3, 3]) * 100.0)
    return np.vstack(V)
def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
Pf = load('SM_P220_Frame'); Ps = load('SM_P220_Slide')
# P220(Blender 좌표) -> UE 로컬 -> 월드 (이전 스크립트와 같은 경계 맞춤)
tfF = sh['tf']['frame']; bmin = np.array(tfF['bmin']); bmax = np.array(tfF['bmax']); best = None
for perm in itertools.permutations(range(3)):
    for sg in itertools.product((1, -1), repeat=3):
        a = Pf[:, list(perm)] * np.array(sg); off = bmin - a.min(0); err = np.abs((a + off).max(0) - bmax).sum()
        if best is None or err < best[0]: best = (err, perm, sg, off)
err, perm, sg, off = best
def p220_to_world(p):
    loc = np.array(p)[list(perm)] * np.array(sg) + off
    return (loc * np.array(tfF['scale'])) @ qmat(tfF['q']).T + np.array(tfF['loc'])
# Armpist -> P220(Blender) : 회전 24개 + 이동 (프레임 bbox 중심 + 슬라이드 상대 위치로 선택)
Ab = {'f': (np.array(FB['frame']['min']), np.array(FB['frame']['max'])), 's': (np.array(FB['slide']['min']), np.array(FB['slide']['max']))}
Afc = (Ab['f'][0] + Ab['f'][1]) / 2; Asc = (Ab['s'][0] + Ab['s'][1]) / 2
Pfc = (Pf.min(0) + Pf.max(0)) / 2; Psc = (Ps.min(0) + Ps.max(0)) / 2
rots = []
for perm2 in itertools.permutations(range(3)):
    for sg2 in itertools.product((1, -1), repeat=3):
        M = np.zeros((3, 3))
        for i, j in enumerate(perm2): M[i, j] = sg2[i]
        if np.linalg.det(M) > 0: rots.append(M)
bestr = None
for M in rots:
    ext = np.abs(M @ (Ab['f'][1] - Ab['f'][0])); pext = Pf.max(0) - Pf.min(0)
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
print('RIGID cost', round(cost(P1), 2), ' per-joint err(cm):', {k: round(float(np.linalg.norm(P1[k] - TW[k])), 1) for k in ['wrist', 'Index_MCP', 'Little_MCP', 'Index_PIP', 'Middle_PIP', 'Thumb1', 'Thumb_tip']})
json.dump({'tag': TAG, 'view': VIEW, 'Rm': Rk.tolist(), 't': tC.tolist(), 'c': C0.tolist(), 'targets_world': {k: v.tolist() for k, v in TW.items()}, 'furina_after_rigid': {k: v.tolist() for k, v in P1.items()}}, open(D + r'\pistol_fit_fbx_%s.json' % TAG, 'w'), indent=1)
print('FIT_FBX_OK')
