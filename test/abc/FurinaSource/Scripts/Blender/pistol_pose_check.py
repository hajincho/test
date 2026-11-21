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
K = json.load(open(D + r'\pistol_roll_constants.json')); Rm = np.array(K['R']); c = np.array([0.1, -13.0, -4.0]); t = np.array(K['pose'][:3])
FV2 = (FV - c) @ Rm.T + c + t; SV2 = (SV - c) @ Rm.T + c + t
print('predicted frame AABB', FV2.min(0).round(2), FV2.max(0).round(2)); print('predicted slide AABB', SV2.min(0).round(2), SV2.max(0).round(2))
G = json.load(open(D + r'\lyra_pistol_grip_probe_g15.json')); print('probe g15 frame', G['frame']['rifle_min'], G['frame']['rifle_max']); print('probe g15 slide', G['slide']['rifle_min'], G['slide']['rifle_max'])
