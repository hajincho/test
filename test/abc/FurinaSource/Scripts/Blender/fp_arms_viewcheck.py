"""blender -b --python fp_arms_viewcheck.py -- <굽기 태그> <포즈 태그(카메라)>
 1인칭 팔 FBX(소총 로컬)를 다시 읽어 상태별 1인칭 카메라(Data/lyra_fp_arms_pose_<포즈 태그>.json 의 hip/ads/shoulder/crouch 표본)에서
 화면 안에 들어오는 정점, 특히 '잘린 끝'(열린 경계 모서리) 정점과 카메라 2 cm 이내 정점을 센다.  -> Data/fp_arms_viewcheck_<굽기>_<포즈>.json"""
import bpy, bmesh, json, sys, math
import numpy as np
A_ = sys.argv[sys.argv.index('--') + 1:]; BT = A_[0]; PT = A_[1]
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
P = json.load(open(D + r'\Data\lyra_fp_arms_pose_%s.json' % PT, encoding='utf-8'))
def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
CAMS = {}
for s in P['samples']:
    st = s.get('state', 'hip')
    Rr = qmat(s['rifle']['q']); tr = np.array(s['rifle']['loc']); Rc = qmat(s['fpcam']['q']); tc = np.array(s['fpcam']['loc'])
    CAMS[st] = {'c': Rr.T @ (tc - tr), 'R': Rr.T @ Rc, 'fov': s.get('fov', 90.0)}   # 카메라 축(소총 로컬): 열 0 = 앞, 1 = 오른쪽, 2 = 위
OUT = {'bake': BT, 'pose': PT, 'cams': {k: {'c': v['c'].tolist(), 'fwd': v['R'][:, 0].tolist(), 'fov': v['fov']} for k, v in CAMS.items()}, 'sides': {}}
ASPECT = 2530 / 1448.0
bpy.ops.wm.read_factory_settings(use_empty=True)
for side in ('L', 'R'):
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=D + r'\FBX\FPArms\SM_FurinaFPArm%s_%s.fbx' % (side, BT))
    ob = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before and bpy.data.objects[k].type == 'MESH'][0]
    me = ob.data; M = np.array(ob.matrix_world)
    co = np.array([v.co[:] for v in me.vertices]); co = co @ M[:3, :3].T + M[:3, 3]; ue = co * np.array([100, -100, 100])
    BKJ = json.load(open(D + r'\Data\fp_arms_bake_%s.json' % BT))
    cut = np.array(BKJ['side_' + side]['cut_ue'])
    ue = np.vstack([ue, cut]); bnd = list(range(len(ue) - len(cut), len(ue)))   # 잘린 끝 정점(굽기 json)
    so = {'nv': len(ue) - len(cut), 'n_boundary_v': len(bnd), 'states': {}}
    for st, cm in CAMS.items():
        rel = (ue - cm['c']) @ cm['R']   # 카메라 로컬 (앞, 오른쪽, 위)
        th = math.tan(math.radians(cm['fov'] / 2)); x = rel[:, 0]
        vis = (x > 2.0) & (np.abs(rel[:, 1]) < th * x) & (np.abs(rel[:, 2]) < th / ASPECT * x)
        near = np.linalg.norm(rel, axis=1) < 6.0
        bv = vis[bnd]
        # 보이는 경계 정점의 화면 위치(정규화 -1..1)
        scr = [[round(float(rel[i, 1] / (th * rel[i, 0])), 3), round(float(rel[i, 2] / (th / ASPECT * rel[i, 0])), 3), round(float(rel[i, 0]), 1)] for i in np.array(bnd)[bv][:12]]
        so['states'][st] = {'vis': int(vis.sum()), 'vis_boundary': int(bv.sum()), 'near6cm': int(near.sum()), 'min_dist': round(float(np.linalg.norm(rel, axis=1).min()), 2), 'boundary_screen_samples': scr}
    OUT['sides'][side] = so
json.dump(OUT, open(D + r'\Data\fp_arms_viewcheck_%s_%s.json' % (BT, PT), 'w'), indent=1)
print('VIEWCHECK_OK')
for side, so in OUT['sides'].items():
    for st, e in so['states'].items(): print(side, st, {k: e[k] for k in ('vis', 'vis_boundary', 'near6cm', 'min_dist')})
