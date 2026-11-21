"""blender -b --python de_mp40_mag.py : MP40 원본의 자체 탄창(Mag)을 정리본(SM_DE_mp40) 좌표로 옮겨 하우징에 끼움 (2026-11-21)
 원본 MP40.fbx 에는 탄창(Mag, 정점 378)과 탄(bullet)이 총 옆에 45°로 따로 놓여 있어 de_weapons_build.py 가 뺐음.
 그래서 지금까지 MP40 은 MP38 탄창을 옮겨 썼는데, 위치가 달라 재장전 때 엉뚱한 곳에 꽂혔음(사용자 지적).
 1) de_weapons_build.py 의 mp40 정리 변환(최장축 -> Y, 둘째 -> Z, 실제 길이 0.833m, 가운데 맞춤)을 총 부품만으로 똑같이 다시 계산해 탄창에 적용
    (검증: 다시 만든 총 경계 상자 = load_weapon('mp40') 경계 상자)
 2) 탄창 자체 축(주성분): 긴 축 -> 위(+Z, 탄 쪽이 위), 중간 축 -> 앞뒤(Y), 짧은 축 -> 좌우(X). 탄 머리 쪽이 총구(-Y)
 3) 하우징 입구(정리본 총의 하우징 아래 끝 단면) 가운데에 맞추고, 탄창 위끝을 총열 축 아래 1.3cm(MP38 탄창과 같은 깊이)까지 밀어 넣음
 -> FBX/Weapons/SM_DE_mp40_mag.fbx(m), Data/de_mp40_mag.json"""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpvm_lib as L
SRC = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany\mp40\source\MP40_unzipped\MP40\MP40.fbx'
OUTF = os.path.join(L.D, 'FBX', 'Weapons', 'SM_DE_mp40_mag.fbx'); os.makedirs(os.path.dirname(OUTF), exist_ok=True)
BORE_Z = 5.7; XC = -0.34; DEPTH_BELOW_BORE = 1.3
OUT = {}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=False)
def world_pts(o): return np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
objs = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
gun_parts = [o for n, o in objs.items() if n not in ('Mag', 'bullet')]
G = np.vstack([world_pts(o) for o in gun_parts]); MG = world_pts(objs['Mag']); BL = world_pts(objs['bullet'])
# 1) 정리 변환 재현
size = G.max(0) - G.min(0); order = np.argsort(-size); ax_long, ax_mid, ax_short = order
R = np.zeros((3, 3)); R[1, ax_long] = 1; R[2, ax_mid] = 1; R[0, ax_short] = 1
if np.linalg.det(R) < 0: R[0, ax_short] = -1
def tf(P, R=R): return P @ R.T
G1 = tf(G); s = 0.833 / (G1.max(0) - G1.min(0))[1]; G1 *= s; c = (G1.max(0) + G1.min(0)) / 2; G1 -= c
def to_native(P): return (tf(P) * s - c) * 100.0   # cm
Gn = G1 * 100.0
ref = L.load_weapon('mp40'); RP = np.array([v.co[:] for v in ref.data.vertices])
OUT['check_bbox_err_cm'] = float(np.abs(np.vstack([Gn.min(0), Gn.max(0)]) - np.vstack([RP.min(0), RP.max(0)])).max())
OUT['scale'] = float(s)
assert OUT['check_bbox_err_cm'] < 0.05, OUT
M = to_native(MG); B = to_native(BL)
# 2) 탄창 축
cm = M.mean(0); U, S_, Vt = np.linalg.svd(M - cm, full_matrices=False)
long_ax, mid_ax, short_ax = Vt[0], Vt[1], Vt[2]
if np.dot(B.mean(0) - cm, long_ax) < 0: long_ax = -long_ax          # 탄 쪽 = 위
bc = B.mean(0); Ub, Sb, Vb = np.linalg.svd(B - bc, full_matrices=False); bax = Vb[0]
proj = (B - bc) @ bax; lo_end = B[proj < np.percentile(proj, 15)]; hi_end = B[proj > np.percentile(proj, 85)]
rad = lambda E: np.linalg.norm((E - E.mean(0)) - np.outer((E - E.mean(0)) @ bax, bax), axis=1).mean()
tip_dir = bax if rad(hi_end) < rad(lo_end) else -bax                  # 탄두(뾰족한 쪽) 방향 = 총구 쪽
if np.dot(tip_dir, mid_ax) > 0: mid_ax = -mid_ax                       # mid_ax 가 뒤(+Y)를 향하게 -> 탄두는 -Y
short_ax = np.cross(mid_ax, long_ax)                                    # 오른손 좌표: X = Y x Z
Rm = np.vstack([short_ax, mid_ax, long_ax])                             # 원 좌표 -> (X, Y, Z)
Mr = (M - cm) @ Rm.T
ext = Mr.max(0) - Mr.min(0); OUT['mag_size_cm'] = ext.round(2).tolist()
# 3) 하우징 입구: 정리본 총에서 탄창 하우징 아래 끝 단면
band = RP[(RP[:, 1] > -18) & (RP[:, 1] < -8) & (np.abs(RP[:, 0] - XC) < 2.5)]
hb = band[:, 2].min(); rim = band[band[:, 2] < hb + 0.6]
hx, hy = (rim[:, 0].min() + rim[:, 0].max()) / 2, (rim[:, 1].min() + rim[:, 1].max()) / 2
OUT['housing'] = {'bottom_z': round(float(hb), 2), 'center_xy': [round(float(hx), 2), round(float(hy), 2)], 'rim_size': (rim.max(0) - rim.min(0)).round(2).tolist()[:2]}
top = Mr[:, 2].max(); t = np.array([hx, hy, BORE_Z - DEPTH_BELOW_BORE - top])
# 위끝 단면 가운데를 하우징 가운데에
topsec = Mr[Mr[:, 2] > top - 0.8]; t[0] -= (topsec[:, 0].min() + topsec[:, 0].max()) / 2; t[1] -= (topsec[:, 1].min() + topsec[:, 1].max()) / 2
Mf = Mr + t
OUT['mag_bbox_cm'] = [Mf.min(0).round(2).tolist(), Mf.max(0).round(2).tolist()]
# 메시 쓰기(정점 순서 유지, 좌표만 교체)
mag = objs['Mag']; me = mag.data.copy(); mesh_world = Matrix.Identity(4)
for v, p in zip(me.vertices, Mf / 100.0): v.co = Vector(p.tolist())
ob = bpy.data.objects.new('SM_DE_mp40_mag', me); bpy.context.scene.collection.objects.link(ob)
# 면 방향 확인: 회전 행렬 행렬식 음수면 면 뒤집힘
if np.linalg.det(R) * np.linalg.det(Rm) < 0:
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free(); OUT['flipped'] = True
for m in list(me.materials): pass
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.export_scene.fbx(filepath=OUTF, use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True, mesh_smooth_type='FACE', path_mode='STRIP', add_leaf_bones=False, bake_anim=False)
json.dump(OUT, open(os.path.join(L.D, 'Data', 'de_mp40_mag.json'), 'w'), indent=1)
print('MP40_MAG', json.dumps(OUT))
