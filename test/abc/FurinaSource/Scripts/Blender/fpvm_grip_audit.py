"""blender -b --python fpvm_grip_audit.py -- <SK 이름(SK_FPVM_ 뒤)> <클립 이름(AS_FPVM_ 뒤)> [render]
1인칭 뷰모델의 손-총 정합 측정(2026-11-22). 내보낸 FBX/FPVM/SK_FPVM_<SK>.fbx 에 AS_FPVM_<클립>.fbx 동작을 걸어 프레임마다:
 - 손가락별(엄지~새끼, 가운데·끝마디 정점) 총 표면까지 최소 거리(gap, 떠 있음)와 총 안으로 파고든 최대 깊이(pen)
 - 손바닥(손목 뼈 정점) gap/pen
 - 손목의 총(VM_Gun 뼈) 기준 위치·회전 흔들림(프레임 간 최대 편차) = 손이 총 위에서 미끄러지는 정도
 손 전체가 총에서 5cm 넘게 떨어진 손(쉬는 왼손 등)은 'free' 로 표시하고 판정에서 뺌. 판정 기준: gap ≤ 1.0cm, pen ≤ 1.0cm, 흔들림 ≤ 1.0cm.
 render: 첫 프레임에서 잡은 손마다 6방향(총 기준 위·아래·왼·오른·앞·뒤) 정사영 -> Data/audit_<SK>_<손>_<방향>.png
결과: Data/grip_audit_<SK>__<클립>__<손>.json. out=<폴더>로 결과 위치를 바꿀 수 있다.
 wrist: Robin 피부의 손목 단면 최소 폭과 아래팔-손 각도를 따로 측정한다.
 motion: 클립 전체 프레임에서 각도, 가속도, 가속도 변화율을 측정한다.
 inspect=R|L|RL: 손을 여섯 방향에서 캡처하고 표면 교차를 기록한다.
 align=R|L: 기존 스킨과 소품 표면을 기준으로 파지를 다시 계산한다.
 preserve_handle: align에서 손바닥과 손가락이 원래 손잡이 높이를 벗어나지 않도록 한다.
 times=0,0.8,1.2: inspect의 시각(초). prop=VM_Mag: 움직이는 소품만 검사한다.
 fbx=<폴더>: 내보낸 후보 FBX를 프로젝트 원본과 별도로 검사한다."""
import bpy, sys, json, math, os
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fpvm_grip import sdist   # 6방향 광선 안/밖(면 법선은 모델마다 뒤집혀 있어 못 믿음)
R0 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # 2026-11-23: 프로젝트 이동
A = sys.argv[sys.argv.index('--') + 1:]; SK, CLIP = A[0], A[1]; RENDER = 'render' in A[2:]
HAND = next((x.split('=')[1] for x in A[2:] if x.startswith('hand=')), 'Body')   # hand=Arms_Infantry 등: 병과 팔 측정
OUT = next((x.split('=', 1)[1] for x in A[2:] if x.startswith('out=')), os.path.join(R0, 'Data'))
FBX = next((x.split('=', 1)[1] for x in A[2:] if x.startswith('fbx=')), os.path.join(R0, 'FBX', 'FPVM'))
FINGERS = ['Thumb', 'IndexFinger', 'MiddleFinger', 'RingFinger', 'LittleFinger']
SIDES = {'R': 'Right', 'L': 'Left'}


def fb(side, f):
    return ['%s%d_%s' % (f, i, side) for i in ((0, 1, 2) if f == 'Thumb' else (1, 2, 3))]


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(FBX, f'SK_FPVM_{SK}.fbx'))
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
hand = next(o for o in meshes if o.name.startswith(HAND))
guns = [o for o in meshes if o is not hand and not o.name.startswith('Arms_') and not o.name.startswith('Body') and not any(k in o.name.lower() for k in ('round', 'bullet', 'case', 'loose', 'shell'))]
for o in meshes:
    if o is not hand and (o.name.startswith('Arms_') or o.name.startswith('Body')): o.hide_render = True; o.hide_viewport = True
before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=os.path.join(FBX, f'AS_FPVM_{CLIP}.fbx'))
src = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
act = src.animation_data.action
for o in [o for o in bpy.data.objects if o not in before and o is not src]: bpy.data.objects.remove(o, do_unlink=True)
src.hide_render = True
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

def wrist_width(points, edges, elbow, wrist):
    axis = (wrist - elbow).normalized()
    normal = np.array(axis)
    u = np.array(axis.orthogonal().normalized())
    v = np.cross(normal, u)
    directions = np.arange(48) * math.pi / 48
    projection_axes = np.cos(directions)[:, None] * u + np.sin(directions)[:, None] * v
    edge_ends = points[edges]
    widths = []
    for offset in (0.008, 0.016):
        center = np.array(wrist - axis * offset)
        distance = (edge_ends - center) @ normal
        crossing = (distance[:, 0] < 0) != (distance[:, 1] < 0)
        a, b = distance[crossing].T
        segments = edge_ends[crossing]
        cut = segments[:, 0] + (segments[:, 1] - segments[:, 0]) * (a / (a - b))[:, None]
        cut = cut[np.linalg.norm(cut - center, axis=1) < 0.045]
        width = np.ptp(cut @ projection_axes.T, axis=0).min() if len(cut) >= 6 else None
        widths.append(round(float(width) * 100, 3) if width is not None else None)
    return widths


def audit_wrist():
    skin = next(i for i, material in enumerate(hand.data.materials) if material and material.name == 'CARobin_Mat18')
    skin_edges = {edge for face in hand.data.polygons if face.material_index == skin for edge in face.edge_keys}
    rest_points = np.array([hand.matrix_world @ vertex.co for vertex in hand.data.vertices])
    edges = {}
    reference = {}
    result = {'sk': SK, 'clip': CLIP, 'offset_from_wrist_cm': [0.8, 1.6],
              'reference_width_cm': reference, 'per_frame': []}

    for side, label in SIDES.items():
        elbow, wrist = (arm.matrix_world @ arm.data.bones[f'{label} {joint}'].head_local for joint in ('elbow', 'wrist'))
        local_edges = [edge for edge in skin_edges if min(np.linalg.norm(rest_points[i] - np.array(wrist)) for i in edge) < 0.08]
        edges[side] = np.array(local_edges, dtype=int).reshape(-1, 2)
        reference[side] = wrist_width(rest_points, edges[side], elbow, wrist)

    for frame in frames:
        goto(frame)
        points = world_verts(hand)
        row = {'frame': frame}
        for side, label in SIDES.items():
            elbow, wrist, knuckle = (arm.matrix_world @ arm.pose.bones[bone].head
                                      for bone in (f'{label} elbow', f'{label} wrist', f'MiddleFinger1_{side}'))
            width = wrist_width(points, edges[side], elbow, wrist)
            bend = math.degrees((wrist - elbow).angle(knuckle - wrist))
            row[side] = {'width_cm': width, 'bend_deg': round(bend, 2),
                         'width_ratio': [round(w / rest, 3) if w is not None and rest else None
                                         for w, rest in zip(width, reference[side])]}
        result['per_frame'].append(row)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'wrist_audit_{SK}__{CLIP}.json')
    with open(path, 'w', encoding='utf-8') as result_file:
        json.dump(result, result_file, indent=1)
    print('WRIST_AUDIT', SK, CLIP, len(frames), 'frames')


def audit_motion():
    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    joint_frames = {side: [] for side in SIDES}
    angles = {side: {'elbow': [], 'wrist': [], **{finger: [] for finger in FINGERS}} for side in SIDES}
    for frame in range(f0, f1 + 1):
        scene.frame_set(frame)
        for side, label in SIDES.items():
            points = [src.matrix_world @ src.pose.bones[f'{label} {joint}'].head for joint in ('arm', 'elbow', 'wrist')]
            joint_frames[side].append(points)
            upper = points[1] - points[0]
            forearm = points[2] - points[1]
            middle = src.matrix_world @ src.pose.bones[f'MiddleFinger1_{side}'].head
            angles[side]['elbow'].append(math.degrees(upper.angle(forearm, 0.0)))
            angles[side]['wrist'].append(math.degrees(forearm.angle(middle - points[2], 0.0)))
            for finger in FINGERS:
                bones = [src.pose.bones[name] for name in fb(side, finger)]
                axes = [(b.tail - b.head).normalized() for b in bones]
                angles[side][finger].append(max(math.degrees(a.angle(b, 0.0)) for a, b in zip(axes, axes[1:])))
    result = {'sk': SK, 'clip': CLIP, 'fps': round(fps, 3), 'frames': f1 - f0 + 1}
    for side, samples in joint_frames.items():
        positions = np.array(samples, dtype=float)
        acceleration = np.linalg.norm(np.diff(positions, n=2, axis=0) * fps ** 2, axis=2)
        jerk = np.linalg.norm(np.diff(positions, n=3, axis=0) * fps ** 3, axis=2)
        motion = {}
        for index, joint in enumerate(('shoulder', 'elbow', 'wrist')):
            motion[joint] = {'span_cm': round(float(np.linalg.norm(np.ptp(positions[:, index], axis=0))) * 100, 2),
                             'acceleration_p95_m_s2': round(float(np.percentile(acceleration[:, index], 95)), 2) if len(acceleration) else None,
                             'jerk_p95_m_s3': round(float(np.percentile(jerk[:, index], 95)), 2) if len(jerk) else None}
        result[side] = {'motion': motion,
                        'angle_max_deg': {joint: round(max(values), 2) for joint, values in angles[side].items()},
                        'angle_peak_frames': {joint: f0 + int(np.argmax(values)) for joint, values in angles[side].items()}}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f'motion_audit_{SK}__{CLIP}.json'), 'w', encoding='utf-8') as result_file:
        json.dump(result, result_file, indent=1)
    print('MOTION_AUDIT', SK, CLIP, result['frames'])


if 'motion' in A[2:]:
    audit_motion()
if 'wrist' in A[2:]:
    audit_wrist()
if ('motion' in A[2:] or 'wrist' in A[2:]) and 'contact' not in A[2:]:
    sys.exit(0)


def gun_bvh():
    dg = bpy.context.evaluated_depsgraph_get(); V, P = [], []
    for o in guns:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); base = len(V)
        V += [tuple(o.matrix_world @ v.co) for v in me.vertices]; P += [tuple(base + i for i in p.vertices) for p in me.polygons]; oe.to_mesh_clear()
    return BVHTree.FromPolygons(V, P)

def fit_support_fingers(fingers, side):
    """손목을 고정하고 손가락 굴곡을 조금 바꿔 정지 자세를 측정한다."""
    import fpvm_lib as rig

    goto(frames[0])
    bvh = gun_bvh()
    axes = rig.finger_axes(arm, side, rig.hand_axes(arm, side))
    result = {}
    for finger in fingers:
        names = fb(side, finger)
        bones = [arm.pose.bones[name] for name in names]
        original = [bone.matrix_basis.copy() for bone in bones]
        sections = [sets[(side, finger + suffix)] for suffix in ('_mid', '_tip')]
        if not all(sections):
            continue

        spread_axis = Vector((0, 1, 0)).cross(axes[names[0]]).normalized()

        def evaluate(offsets, spread=0):
            for index, (bone, matrix, offset) in enumerate(zip(bones, original, offsets)):
                location, rotation, scale = matrix.decompose()
                if index == 0 and spread:
                    rotation = rotation @ Quaternion(spread_axis, math.radians(spread))
                bone.matrix_basis = Matrix.LocRotScale(location, rotation @ Quaternion(axes[bone.name], math.radians(offset)), scale)
            bpy.context.view_layer.update()
            points = world_verts(hand)
            distances = [[100.0 * sdist(bvh, Vector(points[index])) for index in section] for section in sections]
            return max(max(0.0, min(values)) for values in distances), max(0.0, -min(min(values) for values in distances))

        initial_gap, initial_pen = evaluate((0, 0, 0))
        best = (initial_gap, (0, 0, 0), initial_gap, initial_pen, 0)

        def score(best_fit, offsets, spread=0):
            gap, penetration = evaluate(offsets, spread)
            if penetration > max(0.46, initial_pen + 0.08):
                return best_fit
            cost = gap + 0.2 * max(0.0, penetration - initial_pen) + 0.004 * (abs(spread) + sum(abs(value) for value in offsets))
            return (cost, offsets, gap, penetration, spread) if cost < best_fit[0] else best_fit

        root_range = range(-16, 17, 4) if finger == 'Thumb' else range(-12, 13, 4)
        middle_range = range(-20, 21, 4) if finger == 'Thumb' else range(-12, 13, 4)
        for root in root_range:
            for middle in middle_range:
                best = score(best, (root, middle, middle * 0.60))
        if finger == 'Thumb' and best[2] > 0.7:
            first, second, _ = best[1]
            for spread in range(-24, 25, 6):
                for root in range(max(-16, first - 8), min(16, first + 8) + 1, 4):
                    for middle in range(max(-20, second - 8), min(20, second + 8) + 1, 4):
                        best = score(best, (root, middle, middle * 0.60), spread)
        evaluate((0, 0, 0))
        result[finger] = {'gap_before': round(initial_gap, 3), 'gap_after': round(best[2], 3),
                          'penetration_after': round(best[3], 3), 'degrees': dict(zip(names, best[1]))}
        if best[4]:
            result[finger]['spread'] = {'bone': names[0], 'axis': list(spread_axis), 'degrees': best[4]}

    grip = arm.pose.bones['VM_Gun'].matrix.inverted() @ arm.pose.bones[f'{SIDES[side]} wrist'].matrix
    pose = {'sk': SK, 'side': side, 'grip_location': list(grip.translation), 'grip_rotation': list(grip.to_quaternion()),
            'fingers': result, 'axes': {name: list(axes[name]) for finger in result.values() for name in finger['degrees']}}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f'support_fit_{SK}.json'), 'w', encoding='utf-8') as result_file:
        json.dump(pose, result_file, indent=1)
    print('SUPPORT_FIT', SK, result)


options = dict(arg.split('=', 1) for arg in A[2:] if '=' in arg)
times = [float(value) for value in options.get('times', '0').split(',')]
prop = options.get('prop')
if inspect := options.get('inspect'):
    from fpvm_contact_views import inspect_contacts

    inspect_contacts(SK, CLIP, OUT, arm, hand, guns, dom, goto, (f0, f1), inspect,
                     times, prop)
    sys.exit(0)
if align := options.get('align'):
    from fpvm_contact_fit import fit_contact

    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    witnesses = [min(f1, max(f0, f0 + round(seconds * fps))) for seconds in times]
    seed = None
    if path := options.get('seed'):
        with open(path, encoding='utf-8-sig') as stored_fit:
            seed = json.load(stored_fit)['correction_mm_deg']
    fit_contact(SK, CLIP, OUT, arm, hand, guns, dom, goto, witnesses, align, prop, seed,
                'check_fingers' in A[2:], 'preserve_handle' in A[2:])
    sys.exit(0)


fit = next((arg.split('=', 1)[1] for arg in A[2:] if arg.startswith('fit=')), None)
if fit is not None:
    side = next((arg.split('=', 1)[1] for arg in A[2:] if arg.startswith('side=')), 'L')
    fit_support_fingers(fit.split('+'), side)
    sys.exit(0)


res = {'sk': SK, 'clip': CLIP, 'hand_materials': [m.name for m in hand.data.materials if m],
       'frames': frames, 'per_frame': []}
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

os.makedirs(OUT, exist_ok=True)
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
            sc.render.filepath = os.path.join(OUT, f'audit_{SK}_{HAND}_{s}_{nm}.png'); bpy.ops.render.render(write_still=True); files.append(sc.render.filepath)
    res['renders'] = files
with open(os.path.join(OUT, f'grip_audit_{SK}__{CLIP}__{HAND}.json'), 'w', encoding='utf-8') as result_file:
    json.dump(res, result_file, indent=1)
print('GRIP_AUDIT', SK, CLIP, HAND, 'drift', drift, 'fail', res['fail'])
print('WORST', json.dumps(summ))
