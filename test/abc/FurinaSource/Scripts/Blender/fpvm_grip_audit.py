"""blender -b --python fpvm_grip_audit.py -- <SK 이름(SK_FPVM_ 뒤)> <클립 이름(AS_FPVM_ 뒤)> [render]
1인칭 뷰모델의 손-총 정합 측정(2026-11-22). 내보낸 FBX/FPVM/SK_FPVM_<SK>.fbx 에 AS_FPVM_<클립>.fbx 동작을 걸어 프레임마다:
 - 손가락별(엄지~새끼, 가운데·끝마디 정점) 총 표면까지 최소 거리(gap, 떠 있음)와 총 안으로 파고든 최대 깊이(pen)
 - 손바닥(손목 뼈 정점) gap/pen
 - 손목의 총(VM_Gun 뼈) 기준 위치·회전 흔들림(프레임 간 최대 편차) = 손이 총 위에서 미끄러지는 정도
 손 전체가 총에서 5cm 넘게 떨어진 손(쉬는 왼손 등)은 'free' 로 표시하고 판정에서 뺌. 판정 기준: gap ≤ 1.0cm, pen ≤ 1.0cm, 흔들림 ≤ 1.0cm.
 render: 첫 프레임에서 잡은 손마다 6방향(총 기준 위·아래·왼·오른·앞·뒤) 정사영 -> Data/audit_<SK>_<손>_<방향>.png
결과: Data/grip_audit_<SK>__<클립>.json"""
import bpy, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, R'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Scripts/Blender')
from fpvm_grip import sdist   # 6방향 광선 안/밖(면 법선은 모델마다 뒤집혀 있어 못 믿음)
R0 = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
A = sys.argv[sys.argv.index('--') + 1:]; SK, CLIP = A[0], A[1]; RENDER = 'render' in A[2:]
HAND = next((x.split('=')[1] for x in A[2:] if x.startswith('hand=')), 'Body')   # hand=Arms_Infantry 등: 병과 팔 측정
FINGERS = ['Thumb', 'IndexFinger', 'MiddleFinger', 'RingFinger', 'LittleFinger']
SIDES = {'R': 'Right', 'L': 'Left'}


def fb(side, f):
    return ['%s%d_%s' % (f, i, side) for i in ((0, 1, 2) if f == 'Thumb' else (1, 2, 3))]


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=R0 + rf'\FBX\FPVM\SK_FPVM_{SK}.fbx')
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
hand = next(o for o in meshes if o.name.startswith(HAND))
guns = [o for o in meshes if o is not hand and not o.name.startswith('Arms_') and not o.name.startswith('Body') and not any(k in o.name.lower() for k in ('round', 'bullet', 'case', 'loose', 'shell'))]
for o in meshes:
    if o is not hand and (o.name.startswith('Arms_') or o.name.startswith('Body')): o.hide_render = True; o.hide_viewport = True
before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=R0 + rf'\FBX\FPVM\AS_FPVM_{CLIP}.fbx')
src = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
act = src.animation_data.action
for o in [o for o in bpy.data.objects if o not in before and o is not src]: bpy.data.objects.remove(o, do_unlink=True)
src.hide_viewport = True; src.hide_render = True
ORDER = [b.name for b in arm.data.bones if b.name in src.pose.bones]   # 부모 먼저(bones 순서)


def copy_pose():
    """클립 뼈대의 월드 행렬을 그대로 메시 뼈대에 옮김(두 FBX 기준 자세가 달라도 맞음)"""
    bpy.context.view_layer.update(); W = {n: src.matrix_world @ src.pose.bones[n].matrix for n in ORDER}
    inv = arm.matrix_world.inverted()
    for n in ORDER: arm.pose.bones[n].matrix = inv @ W[n]; bpy.context.view_layer.update()


def goto(fr):
    bpy.context.scene.frame_set(fr); copy_pose()


f0, f1 = [int(round(x)) for x in act.frame_range]
NF = int(next((x.split('=')[1] for x in A[2:] if x.startswith('frames=')), '8'))   # 시각 수(기본 8)
frames = sorted(set([f0] + [int(round(f0 + (f1 - f0) * k / max(1, NF - 1))) for k in range(1, NF)]))

# 손 정점 묶음(지배 가중치)
gi = {g.index: g.name for g in hand.vertex_groups}
dom = {}
for v in hand.data.vertices:
    if v.groups:
        g = max(v.groups, key=lambda x: x.weight); dom[v.index] = gi.get(g.group)
sets = {}
for s in SIDES:
    for f in FINGERS:
        b = fb(s, f); sets[(s, f + '_mid')] = [i for i, n in dom.items() if n == b[1]]; sets[(s, f + '_tip')] = [i for i, n in dom.items() if n == b[2]]   # 가운데·끝마디 따로
    sets[(s, 'Palm')] = [i for i, n in dom.items() if n == '%s wrist' % SIDES[s]]

def world_verts(o):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    co = np.array([o.matrix_world @ v.co for v in me.vertices]); oe.to_mesh_clear(); return co

def gun_bvh():
    dg = bpy.context.evaluated_depsgraph_get(); V, P = [], []
    for o in guns:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); base = len(V)
        V += [tuple(o.matrix_world @ v.co) for v in me.vertices]; P += [tuple(base + i for i in p.vertices) for p in me.polygons]; oe.to_mesh_clear()
    return BVHTree.FromPolygons(V, P)

res = {'sk': SK, 'clip': CLIP, 'frames': frames, 'per_frame': []}
wr_hist = {s: [] for s in SIDES}
for fr in frames:
    goto(fr)
    bvh = gun_bvh(); H = world_verts(hand); row = {'frame': fr}
    gunM = arm.matrix_world @ arm.pose.bones['VM_Gun'].matrix
    for s in SIDES:
        pb = arm.pose.bones['%s wrist' % SIDES[s]]; rel = gunM.inverted() @ (arm.matrix_world @ pb.matrix)
        wr_hist[s].append((np.array(rel.translation) * 100, rel.to_quaternion()))
        allv = [i for k, v in sets.items() if k[0] == s for i in v]
        dmin = min((bvh.find_nearest(Vector(H[i]))[3] for i in allv[::7]), default=1e9) * 100
        if dmin > 5.0: row[s] = 'free'; continue
        d = {}
        for part in [f + t for f in FINGERS for t in ('_mid', '_tip')] + ['Palm']:
            gap, pen = 1e9, 0.0
            for i in sets[(s, part)]:
                sd = sdist(bvh, Vector(H[i]))
                if sd < 0: pen = max(pen, -sd)
                else: gap = min(gap, sd)
            d[part] = {'gap_cm': round(gap * 100, 2) if gap < 1e8 else None, 'pen_cm': round(pen * 100, 2)}
            if pen > 0: d[part]['gap_cm'] = 0.0
        row[s] = d
    res['per_frame'].append(row)
drift = {}
for s, hst in wr_hist.items():
    P = np.array([h[0] for h in hst]); q0 = hst[0][1]
    drift[s] = {'pos_cm': round(float(np.linalg.norm(P - P.mean(0), axis=1).max()), 2),
                'rot_deg': round(max(math.degrees(q0.rotation_difference(h[1]).angle) for h in hst), 2)}
res['wrist_drift_vs_gun'] = drift
# 요약: 프레임 중 최악
summ = {}
for row in res['per_frame']:
    for s in SIDES:
        if row.get(s) == 'free' or s not in row: continue
        for part, v in row[s].items():
            k = s + '_' + part; cur = summ.setdefault(k, {'gap_max': 0.0, 'pen_max': 0.0})
            if v['gap_cm'] is not None: cur['gap_max'] = max(cur['gap_max'], v['gap_cm'])
            cur['pen_max'] = max(cur['pen_max'], v['pen_cm'])
res['worst'] = summ
def _exempt(k):   # 방아쇠 검지: 끝마디가 방아쇠에 닿아 있으면 가운데 마디는 방아쇠울 안 허공이 정상
    return k == 'R_IndexFinger_mid' and summ.get('R_IndexFinger_tip', {}).get('gap_max', 9) <= 1.0 and summ[k]['pen_max'] <= 1.0
res['fail'] = sorted([k for k, v in summ.items() if (v['gap_max'] > 1.0 or v['pen_max'] > 1.0) and not _exempt(k)] + [s + '_drift' for s, v in drift.items() if v['pos_cm'] > 1.0 and any(r.get(s) not in (None, 'free') for r in res['per_frame'])])

if RENDER:
    goto(frames[0])
    for m in bpy.data.materials: m.diffuse_color = (0.95, 0.72, 0.6, 1) if ('Skin' in m.name or 'Outfit' in m.name) else (0.25, 0.27, 0.3, 1)
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
    sc.render.resolution_x = sc.render.resolution_y = 600; sc.world = bpy.data.worlds.new('w')
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.2; cam.data.clip_end = 5
    gunM = arm.matrix_world @ arm.pose.bones['VM_Gun'].matrix; R3 = gunM.to_3x3().normalized()
    gx, gy, gz = [(R3 @ Vector(v)).normalized() for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
    views = {'left': (gx, gz), 'right': (-gx, gz), 'top': (gz, -gy), 'bottom': (-gz, -gy), 'front': (-gy, gz), 'back': (gy, gz)}
    H = world_verts(hand); files = []
    for s in SIDES:
        if res['per_frame'][0].get(s) == 'free': continue
        idx = [i for k, v in sets.items() if k[0] == s for i in v]; c = Vector(H[idx].mean(0))
        for nm, (d, up) in views.items():
            z = d.normalized(); x = up.cross(z).normalized(); y = z.cross(x)
            cam.matrix_world = Matrix((x, y, z)).transposed().to_4x4(); cam.location = c + d * 0.8
            sc.render.filepath = R0 + rf'\Data\audit_{SK}_{HAND}_{s}_{nm}.png'; bpy.ops.render.render(write_still=True); files.append(sc.render.filepath)
    res['renders'] = files
json.dump(res, open(R0 + rf'\Data\grip_audit_{SK}__{CLIP}__{HAND}.json', 'w'), indent=1)
print('GRIP_AUDIT', SK, CLIP, HAND, 'drift', drift, 'fail', res['fail'])
print('WORST', json.dumps(summ))
