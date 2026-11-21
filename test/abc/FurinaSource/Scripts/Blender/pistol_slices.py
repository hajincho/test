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

print('SLICES (old rifle coords: x left, y fwd, z up) frame verts')
for zi in [-7.5,-6.5,-5.5,-4.5,-3.5,-2.5,-1.5,-0.5,0.5,1.5,2.5,3.5]:
    m = np.abs(FV[:, 2] - zi) < 0.3
    if m.sum() == 0: print(zi, 'none'); continue
    a = FV[m]; ys = np.sort(a[:, 1]); 
    # y 분포를 2 cm 구간으로 나눠 x 범위 출력
    out = []
    for y0 in range(-19, 2, 2):
        mm = (a[:, 1] >= y0) & (a[:, 1] < y0 + 2)
        if mm.sum(): out.append((y0, round(float(a[mm, 0].min()), 1), round(float(a[mm, 0].max()), 1)))
    print(zi, 'n', int(m.sum()), out)
