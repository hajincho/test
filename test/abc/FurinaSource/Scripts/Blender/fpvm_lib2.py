"""fpvm_lib 이어서: 쇄골 자세, IK, 손가락 자동 쥐기, 렌더."""
import bpy, json, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree
import fpvm_lib as L
SIDE = {'L': 'Left', 'R': 'Right'}

def pose_clavicles(arm, targets_cm):
    """targets_cm = {'L': 위팔 머리 목표(cm), 'R': ...}: 쇄골(shoulder) 뼈를 머리 기준으로 돌려 위팔 머리를 목표로."""
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='POSE'); out = {}
    for s, t in targets_cm.items():
        pb = arm.pose.bones['%s shoulder' % SIDE[s]]; h = pb.head.copy(); a = arm.pose.bones['%s arm' % SIDE[s]].head.copy()
        q = (a - h).rotation_difference(Vector(t) / 100.0 - h)
        M = pb.matrix.copy(); R = q.to_matrix().to_4x4(); pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M; bpy.context.view_layer.update()
        out[s] = round((arm.pose.bones['%s arm' % SIDE[s]].head - Vector(t) / 100.0).length * 100, 2)
    bpy.ops.object.mode_set(mode='OBJECT'); return out

def setup_ik(arm):
    """양손: 목표 빈 객체(T_L/T_R, 위치=손목, 회전=손목 뼈 월드 회전), 팔꿈치 방향 빈 객체(P_L/P_R)."""
    E = {}
    for s in ('L', 'R'):
        for nm in ('T_' + s, 'P_' + s):
            e = bpy.data.objects.new(nm, None); bpy.context.scene.collection.objects.link(e); e.empty_display_size = 0.02; E[nm] = e
        e = E['T_' + s]; e.rotation_mode = 'QUATERNION'
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='POSE')
    for s in ('L', 'R'):
        el = arm.pose.bones['%s elbow' % SIDE[s]]; c = el.constraints.new('IK'); c.target = E['T_' + s]; c.pole_target = E['P_' + s]; c.chain_count = 2; c.use_tail = True; c.name = 'FPVM_IK'
        w = arm.pose.bones['%s wrist' % SIDE[s]]; c2 = w.constraints.new('COPY_ROTATION'); c2.target = E['T_' + s]; c2.name = 'FPVM_ROT'
    bpy.ops.object.mode_set(mode='OBJECT'); return E


def key_baked_pose(bone, matrix, frame, previous):
    bone.matrix_basis = matrix
    rotation = bone.rotation_quaternion.copy()
    if bone.name in previous:
        rotation.make_compatible(previous[bone.name])
    bone.rotation_quaternion = rotation
    previous[bone.name] = rotation
    for path in ('location', 'rotation_quaternion', 'scale'):
        bone.keyframe_insert(path, frame=frame, group=bone.name)


def calib_pole(arm, E, s, wrist_m, elbow_hint_m):
    """pole_angle 을 0/90/-90/180 중 팔꿈치가 hint 에 가장 가까운 값으로."""
    c = arm.pose.bones['%s elbow' % SIDE[s]].constraints['FPVM_IK']; E['T_' + s].location = wrist_m; E['P_' + s].location = elbow_hint_m; best = None
    for a in (0, 90, -90, 180):
        c.pole_angle = math.radians(a); bpy.context.view_layer.update(); d = (arm.pose.bones['%s elbow' % SIDE[s]].head - Vector(elbow_hint_m)).length
        if best is None or d < best[0]: best = (d, a)
    c.pole_angle = math.radians(best[1]); bpy.context.view_layer.update(); return best[1]

def place_hand(arm, E, s, axes, contact_m, f_dir, p_dir, palm_off_cm=1.6, along=0.45, elbow_hint_m=None):
    """손바닥 중심이 contact(무기 표면 점)에 닿게 손목 목표를 정함. f=손가락 방향, p=손바닥이 향하는 방향(무기 쪽)."""
    f = Vector(f_dir).normalized(); p = (Vector(p_dir) - Vector(p_dir).dot(f) * f).normalized()
    w = Vector(contact_m) - p * palm_off_cm / 100.0 - f * axes['len_palm'] * along
    E['T_' + s].rotation_quaternion = L.wrist_rot_for(axes, f, p).to_quaternion()
    if elbow_hint_m is not None: E['P_' + s].location = elbow_hint_m
    E['T_' + s].location = w; bpy.context.view_layer.update()
    for _ in range(6):   # IK 끝(팔꿈치 뼈 꼬리)과 손목 머리가 다를 수 있어 목표를 오차만큼 반복 보정
        err = w - (arm.matrix_world @ arm.pose.bones['%s wrist' % SIDE[s]].head)
        if err.length < 1e-4: break
        E['T_' + s].location = E['T_' + s].location + err; bpy.context.view_layer.update()
    reach = (arm.matrix_world @ arm.pose.bones['%s wrist' % SIDE[s]].head - w).length * 100
    return {'wrist_cm': [round(v * 100, 2) for v in w], 'miss_cm': round(reach, 2)}

def bvh_of(objs):
    V, P = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); mw = o.matrix_world; base = len(V)
        V += [tuple(mw @ v.co) for v in me.vertices]; P += [tuple(base + i for i in p.vertices) for p in me.polygons]; oe.to_mesh_clear()
    return BVHTree.FromPolygons(V, P)

def seg_hit(bvh, a, b, r, n=4):
    for k in range(n + 1):
        p = a.lerp(b, k / n); loc, nrm, idx, dist = bvh.find_nearest(p)
        if loc is None: continue
        if dist < r or (p - loc).dot(nrm) < 0 and dist < 3 * r: return True
    return False

def grip_fingers(arm, s, fax, bvh, r_cm=0.75, step=3.0, limits=None, skip=(), preset=None, targets=None):
    """2026-11-22: 손 메시(Body)가 있으면 피부 기준 풀이(fpvm_grip.grip_fingers_mesh)를 씀 - 예전 뼈 선 방식은 손가락이 펴진 채 멈추고 피부가 총에 파고들었음.
    환경변수 FPVM_GRIP_SEG=1 이면 예전 방식.
    """
    import os, fpvm_grip
    if os.environ.get('FPVM_GRIP_SEG') != '1' and fpvm_grip.body_of(arm) is not None:
        return fpvm_grip.grip_fingers_mesh(arm, s, fax, bvh, limits=limits, skip=skip, preset=preset, targets=targets)
    return grip_fingers_seg(arm, s, fax, bvh, r_cm, step, limits, skip, preset)

def grip_fingers_seg(arm, s, fax, bvh, r_cm=0.75, step=3.0, limits=None, skip=(), preset=None):
    """(예전) 손가락을 관절 순서대로 굽혀 무기 표면에 닿기 직전까지. preset={손가락: [각1,각2,각3]} 이면 그 값으로 고정.
    반환: {뼈: 각도(°)}. 회전은 뼈 로컬 축(fax) 기준 쿼터니언으로 pose_bone.rotation_quaternion 에 곱해 넣음."""
    lim = limits or {'Thumb': (35, 45, 50), 'default': (85, 100, 75)}
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='POSE'); res = {}; r = r_cm / 100.0
    for f in L.FINGERS:
        bns = L.fbones(s, f); pbs = [arm.pose.bones[b] for b in bns]
        for pb in pbs: pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion()
        if f in skip: res.update({b: 0.0 for b in bns}); continue
        if preset and f in preset:
            for b, pb, a in zip(bns, pbs, preset[f]): pb.rotation_quaternion = Quaternion(fax[b], math.radians(a)); res[b] = a
            continue
        bpy.context.view_layer.update(); lm = lim.get(f, lim['default'])
        for j in range(3):
            a = 0.0
            while a + step <= lm[j]:
                pbs[j].rotation_quaternion = Quaternion(fax[bns[j]], math.radians(a + step)); bpy.context.view_layer.update()
                hit = any(seg_hit(bvh, arm.matrix_world @ pbs[k].head, arm.matrix_world @ pbs[k].tail, r) for k in range(j, 3))
                if hit: break
                a += step
            pbs[j].rotation_quaternion = Quaternion(fax[bns[j]], math.radians(a)); bpy.context.view_layer.update(); res[bns[j]] = a
    bpy.ops.object.mode_set(mode='OBJECT'); return res

def apply_fingers(arm, fax, angles):
    """angles {뼈: 굽힘 각}; '<뼈>@spread' 키는 그 뼈의 좌우 벌림(굽힘 뒤에 곱함, 2026-11-22 방아쇠 검지)"""
    for b, a in angles.items():
        if '@' in b: continue
        pb = arm.pose.bones[b]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(fax[b], math.radians(a))
    for k, a in angles.items():
        if not k.endswith('@spread') or not a: continue
        b = k[:-7]; pb = arm.pose.bones[b]; ab = Vector((0, 1, 0)).cross(Vector(fax[b])).normalized()
        pb.rotation_quaternion = Quaternion(ab, math.radians(a)) @ pb.rotation_quaternion

def render_views(prefix, fov=85.0, views=('fp', 'side', 'top'), res=(1280, 720), look=None, scale=0.9):
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True
    sc.render.resolution_x, sc.render.resolution_y = res
    cam = bpy.data.objects.get('VMCam')
    if cam is None:
        cd = bpy.data.cameras.new('VMCam'); cam = bpy.data.objects.new('VMCam', cd); sc.collection.objects.link(cam)
    sc.camera = cam; cd = cam.data; files = []
    for v in views:
        if v == 'fp':   # 게임 카메라: 원점, +X 를 봄, 위 +Z. 가로 FOV
            cd.type = 'PERSP'; cd.sensor_fit = 'HORIZONTAL'; cd.angle = math.radians(fov); cd.clip_start = 0.02; cam.location = (0, 0, 0); cam.rotation_euler = (math.radians(90), 0, math.radians(-90))
        elif v == 'side':   # 오른쪽(-Y)에서
            cd.type = 'ORTHO'; cd.ortho_scale = scale; cam.location = ((look or (0.1, 0, -0.12))[0], -1.5, (look or (0.1, 0, -0.12))[2]); cam.rotation_euler = (math.radians(90), 0, 0)
        elif v == 'top':
            cd.type = 'ORTHO'; cd.ortho_scale = scale; cam.location = ((look or (0.1, 0, -0.12))[0], (look or (0.1, 0, -0.12))[1], 1.5); cam.rotation_euler = (0, 0, math.radians(-90))
        elif v == 'front':   # 앞에서 뒤로
            cd.type = 'ORTHO'; cd.ortho_scale = scale * 0.67; cam.location = (1.5, (look or (0.1, 0, -0.12))[1], (look or (0.1, 0, -0.12))[2]); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
        elif v == 'left':   # 왼쪽(+Y)에서
            cd.type = 'ORTHO'; cd.ortho_scale = scale; cam.location = ((look or (0.1, 0, -0.12))[0], 1.5, (look or (0.1, 0, -0.12))[2]); cam.rotation_euler = (math.radians(90), 0, math.radians(180))
        elif v == 'back':   # 뒤에서 앞으로
            cd.type = 'ORTHO'; cd.ortho_scale = scale * 0.67; cam.location = (-1.5, (look or (0.1, 0, -0.12))[1], (look or (0.1, 0, -0.12))[2]); cam.rotation_euler = (math.radians(90), 0, math.radians(-90))
        fn = prefix + '_' + v + '.png'; sc.render.filepath = fn; bpy.ops.render.render(write_still=True); files.append(fn)
    return files

# ------------------------------------------------------------------ 손가락 모양 고정(preset) + 손 방향 탐색(관통 최소)
def hand_local(arm, s, fax, preset, E=None):
    """preset 손가락 각도를 적용한 손의 점들(손목 뼈 로컬 좌표, m). 이름 있는 점: thumb_tip, index_tip, index_mid, pinch(엄지끝-검지중간 중점), palm."""
    apply_fingers(arm, fax, preset); bpy.context.view_layer.update()
    PBs = arm.pose.bones; Wm = arm.matrix_world @ PBs['%s wrist' % SIDE[s]].matrix; Wi = Wm.inverted(); pts = []
    for f in L.FINGERS:
        for bn in L.fbones(s, f):
            pb = PBs[bn]; a = arm.matrix_world @ pb.head; b = arm.matrix_world @ pb.tail
            for k in range(4): pts.append(Wi @ a.lerp(b, k / 3))
    for bn in ('IndexFinger1_%s' % s, 'LittleFinger1_%s' % s):
        h = arm.matrix_world @ PBs[bn].head; w = Wm.translation
        for k in range(1, 4): pts.append(Wi @ w.lerp(h, k / 4))
    tt = Wi @ (arm.matrix_world @ PBs['Thumb2_%s' % s].tail); it = Wi @ (arm.matrix_world @ PBs['IndexFinger3_%s' % s].tail)
    im = Wi @ ((arm.matrix_world @ PBs['IndexFinger2_%s' % s].head).lerp(arm.matrix_world @ PBs['IndexFinger2_%s' % s].tail, 0.5))
    palm = Wi @ ((arm.matrix_world @ PBs['MiddleFinger1_%s' % s].head).lerp(Wm.translation, 0.45))
    return {'pts': pts, 'thumb_tip': tt, 'index_tip': it, 'index_mid': im, 'pinch': (tt + im) / 2, 'palm': palm}
def fib_dirs(n):
    out = []; g = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n; r = math.sqrt(max(0, 1 - z * z)); out.append(Vector((r * math.cos(g * i), r * math.sin(g * i), z)))
    return out
def search_hand(H, key, target, bvh, shoulder, reach_cm=37.0, excl=None, r_cm=0.8, prefer=None, ndir=160, nroll=12):
    """H[key](손목 로컬 점)가 target 에 오게 하는 손목 행렬 중 관통(무기 표면에서 r 안) 최소. excl=(중심, 반지름 m): 그 안의 점은 접촉 허용.
    prefer=(로컬축 벡터, 월드 방향, 가중치): 선호 방향."""
    best = None; r = r_cm / 100.0; o = H[key]
    for d in fib_dirs(ndir):
        base = Vector((0, 1, 0)).rotation_difference(d).to_matrix()
        for k in range(nroll):
            R = base @ Matrix.Rotation(2 * math.pi * k / nroll, 3, 'Y'); t = target - R @ o
            if (t - shoulder).length * 100 > reach_cm: continue
            pen = 0.0
            for p in H['pts']:
                w = R @ p + t
                if excl and (w - excl[0]).length < excl[1]: continue
                loc, nrm, idx, dist = bvh.find_nearest(w)
                if loc is None: continue
                inside = (w - loc).dot(nrm) < 0
                if inside: pen += dist + r
                elif dist < r: pen += (r - dist)
            sc = pen * 100
            if prefer:
                for ax_l, wdir, wt in prefer: sc += wt * (1 - (R @ Vector(ax_l)).normalized().dot(Vector(wdir).normalized()))
            if best is None or sc < best[0]: best = (sc, R.copy(), t.copy(), pen * 100)
    sc, R, t, pen = best
    return Matrix.LocRotScale(t, R.to_quaternion(), None), {'score': round(sc, 3), 'pen_cm': round(pen, 3)}

# ------------------------------------------------------------------ 손바닥 밀착(2026-11-21): 실제 손 피부 정점이 무기 표면에 닿을 때까지 손목 목표를 손바닥 방향으로 이동
def seat_hand(arm, body, E, s, axes, bvh, gap_cm=0.15, iters=8, palm_only=True, palm_r_cm=1.8, max_move_cm=3.0):
    """손바닥 중심 둘레 피부 정점(손목 뼈 가중치>=0.5)의 무기 표면 최소 거리가 gap 이 되도록 IK 목표를 손바닥 방향(p)으로만 이동.
    부호 거리(면 법선으로 안/밖 판정)는 모델 일부 면 법선이 안쪽이라 잘못 '안'으로 읽혀 손을 9cm 밀어냈음 -> 부호 없는 거리 + 다가가기만 + 최대 3cm."""
    side = SIDE[s]; vg = body.vertex_groups.get('%s wrist' % side)
    if vg is None: return None
    gi = vg.index; idx = [v.index for v in body.data.vertices if any(g.group == gi and g.weight >= 0.5 for g in v.groups)]
    d_last = None; moved = 0.0
    for _ in range(iters):
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); be = body.evaluated_get(dg); me = be.to_mesh(); mw = body.matrix_world
        pb = arm.pose.bones['%s wrist' % side]; Wm = arm.matrix_world @ pb.matrix; p = (Wm.to_3x3() @ axes['p_local']).normalized(); wh = Wm.translation
        f = (Wm.to_3x3() @ axes['f_local']).normalized(); c = wh + f * axes['len_palm'] * 0.45; best = None
        for i in idx:
            w = mw @ me.vertices[i].co
            if palm_only and (w - wh).dot(p) < 0: continue
            q = (w - c) - p * (w - c).dot(p)
            if q.length * 100 > palm_r_cm: continue
            loc, nrm, _, dist = bvh.find_nearest(w)
            if loc is None: continue
            if best is None or dist < best: best = dist
        be.to_mesh_clear()
        if best is None: break
        d_last = best * 100; move = best - gap_cm / 100.0
        if move <= 0.0005 or moved >= max_move_cm / 100.0: break
        move = min(move, max_move_cm / 100.0 - moved); moved += move
        E['T_' + s].location = E['T_' + s].location + p * move
    bpy.context.view_layer.update(); return {'gap_cm': round(d_last, 3) if d_last is not None else None, 'moved_cm': round(moved * 100, 2)}

def palm_gap(arm, body, s, axes, bvh, palm_r_cm=1.8):
    """손바닥 중심 둘레 피부 정점의 무기 표면 최소 부호 거리(cm) + 손목 머리 위치(진단용)."""
    side = SIDE[s]; vg = body.vertex_groups.get('%s wrist' % side); gi = vg.index
    idx = [v.index for v in body.data.vertices if any(g.group == gi and g.weight >= 0.5 for g in v.groups)]
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); be = body.evaluated_get(dg); me = be.to_mesh(); mw = body.matrix_world
    pb = arm.pose.bones['%s wrist' % side]; Wm = arm.matrix_world @ pb.matrix; p = (Wm.to_3x3() @ axes['p_local']).normalized(); f = (Wm.to_3x3() @ axes['f_local']).normalized(); wh = Wm.translation
    c = wh + f * axes['len_palm'] * 0.45; best = None; n = 0
    for i in idx:
        w = mw @ me.vertices[i].co
        if (w - wh).dot(p) < 0: continue
        q = (w - c) - p * (w - c).dot(p)
        if q.length * 100 > palm_r_cm: continue
        n += 1; loc, nrm, _, dist = bvh.find_nearest(w)
        sd = dist
        best = sd if best is None or sd < best else best
    be.to_mesh_clear(); return {'gap_cm': round(best * 100, 2) if best is not None else None, 'n': n, 'wrist_cm': [round(v * 100, 1) for v in wh], 'mesh_verts_total': len(me.vertices) if False else None}

def fold_sleeves(arm, fold=-0.9):
    """소매 끝 날개(Sleeve_1..4_L/R)를 아래팔(elbow) 축 쪽으로 접음(fold<0: 팔꿈치 쪽). 1인칭에서 손을 가리던 소매(fp_arms_bake.py 와 같은 방식).
    반환: 접은 뼈 수."""
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='POSE'); n = 0
    for side, sname in (('L', 'Left'), ('R', 'Right')):
        if '%s elbow' % sname not in arm.pose.bones: continue
        ev = Vector(arm.pose.bones['%s elbow' % sname].matrix.col[1][:3]).normalized()
        if fold < 0: ev = -ev
        for k in range(1, 5):
            pb = arm.pose.bones.get('Sleeve_%d_%s' % (k, side))
            if pb is None: continue
            Mx = pb.matrix.copy(); d = Vector(Mx.col[1][:3]).normalized(); axv = d.cross(ev)
            if axv.length < 1e-6: continue
            ang = math.atan2(axv.length, d.dot(ev)) * abs(fold)
            R = Matrix.Rotation(ang, 4, axv.normalized()); h = Mx.translation.copy()
            pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ Mx; bpy.context.view_layer.update(); n += 1
    bpy.ops.object.mode_set(mode='OBJECT'); return n
