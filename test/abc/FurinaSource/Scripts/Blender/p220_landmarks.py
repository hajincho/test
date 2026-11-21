"""blender -b --python p220_landmarks.py -- <포즈 태그(p..)> : P220 프레임/슬라이드(UCX 제외)를 프레임 로컬(UE: X 총구, Y 오른쪽, Z 위)로 옮겨 그립 단면 등을 출력 -> Data/p220_landmarks.json"""
import bpy, json, sys, itertools
import numpy as np
A_ = sys.argv[sys.argv.index('--') + 1:]; PT = A_[0]
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
P = json.load(open(D + r'\Data\lyra_fp_arms_pose_%s.json' % PT, encoding='utf-8')); SM = P['samples'][4]; FR = SM['FurinaPistolFrame']
bpy.ops.wm.read_factory_settings(use_empty=True)
before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=D + r'\Data\p220_export\SM_P220_Frame.fbx')
objs = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before and bpy.data.objects[k].type == 'MESH' and not k.startswith('UCX_')]
V = np.vstack([(np.array([v.co[:] for v in o.data.vertices]) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]) * 100 for o in objs])
bmin = np.array(FR['bmin']); bmax = np.array(FR['bmax']); bb = None
for perm in itertools.permutations(range(3)):
    for sg in itertools.product((1, -1), repeat=3):
        a = V[:, list(perm)] * np.array(sg); off = bmin - a.min(0); err = np.abs((a + off).max(0) - bmax).sum()
        if bb is None or err < bb[0]: bb = (err, perm, sg, off)
L = V[:, list(bb[1])] * np.array(bb[2]) + bb[3]
R = {'bbox': [L.min(0).tolist(), L.max(0).tolist()], 'slices': [], 'rays': []}
from mathutils import Vector
from mathutils.bvhtree import BVHTree
F = []; off = 0
for o in objs:
    F += [[off + i for i in pl.vertices] for pl in o.data.polygons]; off += len(o.data.vertices)
T = BVHTree.FromPolygons([Vector(x) for x in L], F)
def hits(o, d):
    out = []; o = Vector(o); d = Vector(d).normalized()
    for _ in range(60):
        h = T.ray_cast(o, d)
        if h[0] is None: break
        out.append(round(float((h[0] - Vector(o)).dot(d)) + (out[-1] if False else 0), 2)); o = h[0] + d * 1e-3
    return out
for z in np.arange(-8.5, 5.01, 0.5):
    for y in (0.2,):
        hx = []; o = Vector((-12.0, y, z)); d = Vector((1, 0, 0))
        for _ in range(60):
            h = T.ray_cast(o, d)
            if h[0] is None: break
            hx.append(round(h[0].x, 2)); o = h[0] + d * 1e-3
        hy = []; o = Vector((-1.0, -5.0, z)); d = Vector((0, 1, 0))
        for _ in range(20):
            h = T.ray_cast(o, d)
            if h[0] is None: break
            hy.append(round(h[0].y, 2)); o = h[0] + d * 1e-3
        R['rays'].append({'z': round(float(z), 2), 'x_hits': hx, 'y_hits_at_x-1': hy})
        print('RAY z %5.1f  x %s   y(x=-1) %s' % (z, hx, hy))
for z in np.arange(-8.5, 5.01, 0.5):
    m = np.abs(L[:, 2] - z) < 0.25
    if not m.any(): continue
    xs = np.sort(L[m, 0]); ys = L[m, 1]
    # X 구간을 0.4 cm 이상 비면 분리 (그립 / 방아쇠울 / 앞부분)
    segs = []; s0 = xs[0]; prev = xs[0]
    for x in xs[1:]:
        if x - prev > 0.4: segs.append([round(float(s0), 2), round(float(prev), 2)]); s0 = x
        prev = x
    segs.append([round(float(s0), 2), round(float(prev), 2)])
    R['slices'].append({'z': round(float(z), 2), 'x_segs': segs, 'y': [round(float(ys.min()), 2), round(float(ys.max()), 2)]})
json.dump(R, open(D + r'\Data\p220_landmarks.json', 'w'), indent=1)
for s in R['slices']: print('Z %5.1f  x %s  y %s' % (s['z'], s['x_segs'], s['y']))
