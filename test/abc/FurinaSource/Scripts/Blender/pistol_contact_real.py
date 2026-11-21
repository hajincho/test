"""blender -b --python pistol_contact_real.py -- <side_probe 태그> [뷰이름=left]
 PIE 에서 기록한 실제 변환(lyra_pistol_side_probe_<태그>.json 의 tf: 프레임/슬라이드 월드 변환 + 로컬 경계, bones: 손가락 월드 위치)으로 손가락-권총 메시 거리를 정확히 계산한다.
 (이전 파이프라인은 축/스케일을 경계에 맞춰 추정했는데 실제 화면과 어긋났음 -> 여기서는 UE 변환을 그대로 사용)
 메시: Data/p220_export/SM_P220_Frame.fbx, SM_P220_Slide.fbx (Blender 가 0.01 스케일로 읽음 -> x100 = cm).  FBX 축 -> UE 로컬 축은 UE 로컬 경계 상자(tf.bmin/bmax)와 맞춰 순열/부호를 찾는다.
 출력: Data/pistol_contact_real_<태그>.json : 관절별 (메시 표면까지 부호 거리 cm), 손가락별 요약."""
import bpy, json, sys, itertools, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
TAG = sys.argv[sys.argv.index('--') + 1]; VIEW = sys.argv[sys.argv.index('--') + 2] if len(sys.argv) > sys.argv.index('--') + 2 else 'left'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
J = json.load(open(D + r'\lyra_pistol_side_probe_%s.json' % TAG)); sh = [s for s in J['shots'] if s['name'] == VIEW][0]
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
            a = v[:, list(perm)] * np.array(sg); off = bmin - a.min(0); a2 = a + off; err = np.abs(a2.max(0) - bmax).sum()
            if best is None or err < best[0]: best = (err, perm, sg, off)
    err, perm, sg, off = best; local = v[:, list(perm)] * np.array(sg) + off
    M = qmat(tf['q']); S = np.array(tf['scale']); loc = np.array(tf['loc'])
    world = (local * S) @ M.T + loc
    meshes[cn] = (world, f, err)
V0, F0, e0 = meshes['frame']; V1, F1, e1 = meshes['slide']
allv = np.vstack([V0, V1]); allf = F0 + [[i + len(V0) for i in p] for p in F1]
tree = BVHTree.FromPolygons([Vector(x) for x in allv], allf)
DIRS = [Vector((0.31, 0.77, 0.55)).normalized(), Vector((-0.6, 0.2, 0.77)).normalized(), Vector((0.1, -0.9, 0.42)).normalized()]
def sdist(p):
    q = Vector(p); hit = tree.find_nearest(q)
    if hit[0] is None: return 99.0
    d = hit[3]; votes = 0
    for dr in DIRS:
        n = 0; o = q.copy()
        for _ in range(40):
            h = tree.ray_cast(o, dr)
            if h[0] is None: break
            n += 1; o = h[0] + dr * 1e-4
        votes += n % 2
    return -d if votes >= 2 else d
out = {'tag': TAG, 'view': VIEW, 'fit_err': [e0, e1], 'joints': {}}
for bn, P in sh['bones'].items(): out['joints'][bn] = round(sdist(P), 3)
# 손가락 요약
summ = {}
for sd in 'RL':
    for f in ('Index', 'Middle', 'Ring', 'Little'):
        summ['%s_%s' % (sd, f)] = [out['joints'].get('%sFinger%d_%s' % (f, i, sd)) for i in (1, 2, 3)]
    summ['%s_Thumb' % sd] = [out['joints'].get('Thumb%d_%s' % (i, sd)) for i in (0, 1, 2)]
    summ['%s_wrist' % sd] = out['joints'].get('%s-wrist' % ('Right' if sd == 'R' else 'Left'))
out['summary'] = summ
json.dump(out, open(D + r'\pistol_contact_real_%s.json' % TAG, 'w'), indent=1); print('CONTACT_REAL', json.dumps(summ))
