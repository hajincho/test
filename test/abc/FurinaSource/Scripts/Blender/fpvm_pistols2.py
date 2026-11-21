"""blender -b --python fpvm_pistols2.py -- <p38|p08|pp> [preview|export] [옵션 json]
권총 1인칭 3자세(2026-11-21, 사용자 지정): 비조준 = 한손(낮게), 견착 = 팔을 쭉 뻗은 한손, 정조준 = 두 손 + 기계식 조준.
 근거(Motion/DE_FP_MOTION_RESEARCH.md 5-1절): 2차대전기 권총 사격은 한손 위주(Applegate 1943 'Kill or Get Killed', FSA 지향사격: 팔을 굳혀
 뻗고 몸통으로 돌림), 두 손 조준 자세(Weaver 1959, Isosceles 1980년대)는 전후 보급. 게임 요구대로 정조준만 두 손으로 둠.
 정조준 자세 = 기존 두 손 자세(총 위치 PISTOL_POS) 그대로라 정조준 변환(fpvm_view_alignment.json)은 바뀌지 않음.
 출력 FBX/FPVM: SK_FPVM_<KEY>.fbx + AS_FPVM_<KEY>_<Idle|Fire|IdleS|FireS|IdleA|FireA|Reload|T_HS|T_SH|T_HA|T_AH|T_SA|T_AS>.fbx
   Idle/Fire = 비조준(한손). 접미 S = 견착, A = 정조준. T_xy = x 자세에서 y 자세로 가는 전환(0.2~0.25초).
 Data/fpvm_<key>_stances.json: 자세별 손목-어깨 거리(팔 길이 37.5cm 안인지), 총구 위치(UE 카메라 공간, 정지 자세)"""
import json, math, sys
from pathlib import Path
import bmesh, bpy
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fpvm_lib as rig
import fpvm_lib2 as poses
from fpvm_pistols import visual_top, unit_interval, PISTOL_POS

FPS = 30
A = sys.argv[sys.argv.index('--') + 1:]; KEY = A[0]; MODE = A[1] if len(A) > 1 else 'export'; OPT = json.loads(A[2]) if len(A) > 2 else {}
assert KEY in ('p38', 'p08', 'pp')
OUT = {'key': KEY}
REACH = 37.5
# 자세별 총 이동(카메라 공간 cm, 회전 °: 오른손 손잡이 기준). 앞 +x, 왼쪽 +y, 위 +z, pitch + = 총구 위, roll + = 윗면이 왼쪽(안쪽)으로
STANCE = {
    'H': dict(fwd=-3.5, side=-3.0, up=-1.5, pitch=-6.0, roll=10.0, yaw=4.0),   # 비조준: 낮게, 몸 쪽으로 당기고 총구 약간 아래·안쪽으로 기울임(한손)
    'S': dict(fwd=-0.5, side=2.5, up=-2.0, pitch=0.0, roll=0.0, yaw=-1.0),    # 견착: 팔을 끝까지 뻗어(두 손 자세도 이미 팔 길이 끝) 눈높이 조금 아래, 가운데 쪽(한손, 팔 고정)
    'A': dict(fwd=0.0, side=0.0, up=0.0, pitch=0.0, roll=0.0, yaw=0.0),       # 정조준: 기존 두 손 자세(정조준 변환과 맞물림)
}
for k, v in OPT.get('stance', {}).items(): STANCE[k].update(v)
KICK = {'H': (7.0, 2.0), 'S': (6.0, 2.2), 'A': (3.2, 1.7)}   # 사격 총구 들림(°)·뒤로 밀림(cm): 한손이 더 크게 튐
TRANS = {('H', 'S'): .20, ('S', 'H'): .20, ('H', 'A'): .25, ('A', 'H'): .25, ('S', 'A'): .22, ('A', 'S'): .22}


def main():
    arm, hands, _ = rig.load_arms('a1'); arm.name = 'Armature'
    if hands.data.shape_keys: hands.shape_key_clear()
    for uv in list(hands.data.uv_layers)[1:]: hands.data.uv_layers.remove(uv)
    poses.fold_sleeves(arm)
    gun = rig.load_weapon(KEY); top = visual_top(gun, KEY)
    transform = rig.gun_native_to_cam(PISTOL_POS, 2.5, 4., -3.)
    for prop in (gun, top): prop.matrix_world = transform
    bpy.context.view_layer.update()
    ik = poses.setup_ik(arm); mesh = poses.bvh_of([gun, top])
    grip_y = {'p38': 5.5, 'p08': 6., 'pp': 4.6}[KEY]
    ax = {s: rig.hand_axes(arm, s) for s in 'LR'}; fax = {s: rig.finger_axes(arm, s, ax[s]) for s in 'LR'}
    controls = {}; WREST = {}   # WREST: 실제 손목 위치(두 손 자세). IK 목표(controls)는 팔 길이 밖일 수 있음(팔을 끝까지 뻗은 자세)
    for side, sign in (('R', 1), ('L', -1)):   # 두 손 자세(기존과 같은 방법)
        point = transform @ Vector((-sign * 9., grip_y - (0. if side == 'R' else 1.5), -2.2))
        direction = (transform.to_3x3() @ Vector((sign, 0, 0))).normalized()
        contact = mesh.ray_cast(point, direction, .3)[0]
        if contact is None: contact = transform @ Vector((-sign * 1.05, grip_y, -2.2))
        finger_dir = (transform.to_3x3() @ Vector((0, -.48, -.88))).normalized()
        pole = Vector((-.04, -.20 * sign, -.28))
        poses.place_hand(arm, ik, side, ax[side], contact, finger_dir, direction, palm_off_cm=1.35, along=.42, elbow_hint_m=contact + pole)
        poses.calib_pole(arm, ik, side, ik['T_' + side].location, contact + pole)
        poses.seat_hand(arm, hands, ik, side, ax[side], mesh)
        grip = poses.grip_fingers(arm, side, fax[side], mesh, r_cm=0.55, limits={'Thumb': (20, 25, 25), 'default': (76, 90, 64)})
        controls[side] = (ik['T_' + side].location.copy(), ik['T_' + side].rotation_quaternion.copy(), pole, grip)
        WREST[side] = (arm.matrix_world @ arm.pose.bones['%s wrist' % poses.SIDE[side]].head).copy()
    # 한손일 때 오른손 엄지는 손잡이를 감싸게 조금 더(왼손이 받쳐 주지 않음)
    grip_one = dict(controls['R'][3])
    for b in rig.fbones('R', 'Thumb'): grip_one[b] = grip_one.get(b, 0.0) + 6.0
    # 왼손 쉬는 자리(한손 자세): 가슴 왼쪽 아래, 화면 밖. 손가락은 살짝 굽힘
    rest_loc = Vector(OPT.get('l_rest', (0.03, 0.13, -0.40)))
    rest_rot = rig.wrist_rot_for(ax['L'], Vector((0.15, -0.1, -1.0)), Vector((0.0, -1.0, 0.1))).to_quaternion()
    RELAX = {b: a for f, vals in {'Thumb': (10, 15, 10), 'IndexFinger': (20, 25, 15), 'MiddleFinger': (25, 30, 20), 'RingFinger': (30, 35, 20), 'LittleFinger': (30, 35, 20)}.items()
             for b, a in zip(rig.fbones('L', f), vals)}
    L_REST_POLE = Vector((-.10, .12, -.25))
    shR = arm.matrix_world @ arm.pose.bones['Right arm'].head
    pivot = WREST['R'].copy()   # 자세 회전 기준 = 오른손목(손잡이)
    def stance_D(s, kick=0.0, kick_s=None):
        p = STANCE[s]; kp, kb = KICK[kick_s or s]
        R = (Matrix.Rotation(math.radians(p['yaw']), 4, 'Z') @ Matrix.Rotation(math.radians(-(p['pitch'] + kp * kick)), 4, 'Y') @ Matrix.Rotation(math.radians(p['roll']), 4, 'X'))
        return Matrix.Translation(Vector((p['fwd'] - kb * kick, p['side'], p['up'] + 0.3 * kick)) / 100.0) @ Matrix.Translation(pivot) @ R @ Matrix.Translation(-pivot)
    def mix(Ma, Mb, x):
        la, ra, _ = Ma.decompose(); lb, rb, _ = Mb.decompose()
        return Matrix.LocRotScale(la.lerp(lb, x), ra.slerp(rb, x), None)
    def blend_f(fa, fb, x): return {b: fa.get(b, 0.0) * (1 - x) + fb.get(b, 0.0) * x for b in set(fa) | set(fb)}
    # 자세별 손목 거리 확인
    OUT['reach_cm'] = {}
    for s in STANCE:
        w = stance_D(s) @ WREST['R']; OUT['reach_cm'][s] = round((w - shR).length * 100, 1)
    OUT['arm_len_cm'] = round(((arm.pose.bones['Right elbow'].head - arm.pose.bones['Right arm'].head).length + (arm.pose.bones['Right wrist'].head - arm.pose.bones['Right elbow'].head).length) * 100, 1)
    OUT['muzzle'] = {}
    if MODE == 'preview' or MODE == 'export':
        pass
    root = transform @ Vector((0, 0, 0)); top_pivot = transform @ Vector((0, 5., 4.)); forward = Vector((.05, 0, 0))
    rig.add_bone(arm, 'VM_Gun', 'Hips', root, root + forward); rig.add_bone(arm, 'VM_Exterior', 'VM_Gun', top_pivot, top_pivot + forward)
    rig.bind_rigid(arm, gun, 'VM_Gun'); rig.bind_rigid(arm, top, 'VM_Exterior')
    for bone in arm.pose.bones: bone.rotation_mode = 'QUATERNION'
    rest = {name: arm.data.bones[name].matrix_local.copy() for name in ('VM_Gun', 'VM_Exterior')}
    constraints = [c for bone in arm.pose.bones for c in bone.constraints]
    # 총구(원본 cm: 가장 앞 0.3cm 조각의 가운데) -> UE 카메라 공간(정지 = 정조준 자세)
    P = [v.co for v in gun.data.vertices]; ymin = min(p.y for p in P); sl = [p for p in P if p.y < ymin + 0.3]
    mz = Vector((sum(p.x for p in sl) / len(sl), ymin, sum(p.z for p in sl) / len(sl)))
    wm = transform @ mz; fw = (transform.to_3x3() @ Vector((0, -1, 0))).normalized(); up = (transform.to_3x3() @ Vector((0, 0, 1))).normalized()
    OUT['muzzle'] = {'native_cm': [round(c, 3) for c in mz], 'ue_cam_cm': [wm.x * 100, -wm.y * 100, wm.z * 100], 'ue_fwd': [fw.x, -fw.y, fw.z], 'ue_up': [up.x, -up.y, up.z]}

    def pose_state(D, L_on, l_extra=Vector(), kick=0.0, ext=0.0, fing_R=None, fing_L=None):
        """D: 총 이동, L_on: 0(쉼)~1(총에 붙음). ext: 슬라이드 후퇴 0~1"""
        locR, rotR, poleR, gripR = controls['R']; locL, rotL, poleL, gripL = controls['L']
        WR = Matrix.LocRotScale(D @ locR, D.to_quaternion() @ rotR, None)
        Won = Matrix.LocRotScale(D @ locL + l_extra, D.to_quaternion() @ rotL, None); Woff = Matrix.LocRotScale(rest_loc, rest_rot, None)
        la, ra, _ = Woff.decompose(); lb, rb, _ = Won.decompose(); x = L_on
        lL = la.lerp(lb, x) + Vector((0, 0, .06 * math.sin(math.pi * x))) * (1 if 0 < x < 1 else 0); rL = ra.slerp(rb, x)
        wantR = D @ WREST['R']; DBG['wantR'] = wantR; wonL = D @ WREST['L'] + l_extra; wantL = rest_loc.lerp(wonL, x) + Vector((0, 0, .06 * math.sin(math.pi * x))) * (1 if 0 < x < 1 else 0)
        for s, (l, r, pole) in (('R', (WR.translation, WR.to_quaternion(), poleR)), ('L', (lL, rL, poleL * x + L_REST_POLE * (1 - x)))):
            ik['T_' + s].location = l; ik['T_' + s].rotation_quaternion = r; ik['P_' + s].location = l + pole
        bpy.context.view_layer.update()
        for s, l in (('R', wantR), ('L', wantL)):
            for _ in range(6):
                err = l - (arm.matrix_world @ arm.pose.bones['%s wrist' % poses.SIDE[s]].head)
                if err.length < 2e-4: break
                ik['T_' + s].location = ik['T_' + s].location + err; bpy.context.view_layer.update()
        poses.apply_fingers(arm, fax['R'], fing_R or gripR); poses.apply_fingers(arm, fax['L'], fing_L or blend_f(RELAX, gripL, x))
        arm.pose.bones['VM_Gun'].matrix = D @ rest['VM_Gun']; bpy.context.view_layer.update()
        acc = Matrix.Translation((-.008 * ext, 0, .003 * ext))
        if KEY == 'p08': acc = Matrix.Translation(top_pivot) @ Matrix.Rotation(math.radians(-18 * ext), 4, 'Y') @ Matrix.Translation(-top_pivot)
        arm.pose.bones['VM_Exterior'].matrix = D @ acc @ rest['VM_Exterior']; bpy.context.view_layer.update()
    LON = {'H': 0.0, 'S': 0.0, 'A': 1.0}; DBG = {}
    def fingR(s): return controls['R'][3] if s == 'A' else grip_one
    clips = {}
    for s in 'HSA':
        def idle(t, s=s):
            b = math.sin(t / 4 * math.tau); amp = {'H': 1.6, 'S': 1.0, 'A': 1.0}[s]   # 한손 비조준은 조금 더 흔들림
            D = Matrix.Translation((0, 0, .0016 * amp * b)) @ stance_D(s); pose_state(D, LON[s], fing_R=fingR(s))
        def fire(t, s=s):
            k = unit_interval(t, 0, .045) * (1 - unit_interval(t, .05, .24)); pose_state(stance_D(s, k), LON[s], ext=k, fing_R=fingR(s))
        suf = {'H': '', 'S': 'S', 'A': 'A'}[s]
        clips['Idle' + suf] = (idle, 4.0); clips['Fire' + suf] = (fire, .30)
    for (a, b), dur in TRANS.items():
        def tr(t, a=a, b=b, dur=dur):
            x = unit_interval(t, 0, dur); D = mix(stance_D(a), stance_D(b), x)
            pose_state(D, LON[a] * (1 - x) + LON[b] * x, fing_R=fingR(a) if x < .5 else fingR(b))
        clips[f'T_{a}{b}'] = (tr, dur)
    D_RL = Matrix.Translation((0, .015, -.065)) @ Matrix.Translation(root) @ Matrix.Rotation(math.radians(12.), 4, 'Y') @ Matrix.Translation(-root)
    def reload(t):   # 1.8초: 비조준(한손) -> 두 손으로 모아 기울임 -> 왼손이 아래로(탄창) -> 다시 위 -> 비조준
        up_ = unit_interval(t, 0, .30); down = unit_interval(t, 1.40, 1.80); k = up_ * (1 - down)
        D = mix(stance_D('H'), D_RL, k); fetch = unit_interval(t, .35, .65) * (1 - unit_interval(t, .95, 1.30))
        pose_state(D, k, l_extra=Vector((-.025, .025, -.13)) * fetch, fing_R=grip_one if k < .5 else controls['R'][3])
    clips['Reload'] = (reload, 1.8)
    OUT['clips'] = {k: v[1] for k, v in clips.items()}
    if MODE == 'preview':
        for m in bpy.data.materials: m.diffuse_color = (0.85, 0.7, 0.62, 1) if 'Skin' in m.name else (0.25, 0.3, 0.55, 1) if 'Outfit' in m.name else (0.3, 0.3, 0.32, 1)
        for c in constraints: c.mute = False
        R_ = []
        for nm, (fn, t) in (('H', (clips['Idle'][0], 0)), ('S', (clips['IdleS'][0], 0)), ('A', (clips['IdleA'][0], 0)), ('fireH', (clips['Fire'][0], .05)), ('rl', (clips['Reload'][0], .8))):
            fn(t); wR = arm.matrix_world @ arm.pose.bones['Right wrist'].head; g = arm.matrix_world @ arm.pose.bones['VM_Gun'].head
            OUT.setdefault('dbg', {})[nm] = {'wrist_err_cm': round((wR - DBG['wantR']).length * 100, 2), 'gun_head': [round(c * 100, 1) for c in g], 'wrist': [round(c * 100, 1) for c in wR],
                                             'arm_mw_identity': arm.matrix_world == Matrix.Identity(4)}
            R_ += poses.render_views(str(Path(rig.D) / 'Data' / f'fpvm_{KEY}_st_{nm}'), views=('fp', 'side'), look=tuple(transform @ Vector((0, 0, 0))), scale=0.6)
        OUT['renders'] = R_
    else:
        actions = {}
        for name, (fn, dur) in clips.items():
            arm.animation_data_create(); arm.animation_data.action = None
            for c in constraints: c.mute = False
            frames = []
            for f in range(round(dur * FPS) + 1):
                fn(min(dur, f / FPS))
                frames.append({b.name: arm.convert_space(pose_bone=b, matrix=b.matrix, from_space='POSE', to_space='LOCAL').copy() for b in arm.pose.bones})
            for c in constraints: c.mute = True
            act = bpy.data.actions.new(f'FPVM_{KEY.upper()}_{name}'); act.use_fake_user = True; arm.animation_data.action = act
            for f, mats in enumerate(frames, 1):
                for b in arm.pose.bones:
                    b.matrix_basis = mats[b.name]
                    for path in ('location', 'rotation_quaternion', 'scale'): b.keyframe_insert(data_path=path, frame=f, group=b.name)
            actions[name] = act
        for b in arm.pose.bones:
            for c in list(b.constraints): b.constraints.remove(c)
        for h in ik.values(): bpy.data.objects.remove(h)
        arm.animation_data.action = actions['IdleA']   # 메시 기준 자세 = 정조준(두 손)
        bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1.0
        bpy.ops.object.select_all(action='DESELECT')
        for o in (arm, hands, gun, top): o.select_set(True)
        bpy.context.view_layer.objects.active = arm
        path = Path(rig.D) / 'FBX' / 'FPVM' / f'SK_FPVM_{KEY.upper()}.fbx'
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'ARMATURE', 'MESH'}, axis_forward='-Y', axis_up='Z', add_leaf_bones=False,
                                 armature_nodetype='NULL', bake_anim=False, mesh_smooth_type='FACE', path_mode='STRIP')
        for name, act in actions.items():
            arm.animation_data.action = act; s0, s1 = act.frame_range; bpy.context.scene.frame_start = round(s0); bpy.context.scene.frame_end = round(s1)
            bpy.ops.export_scene.fbx(filepath=str(path.with_name(f'AS_FPVM_{KEY.upper()}_{name}.fbx')), use_selection=True, object_types={'ARMATURE'}, axis_forward='-Y', axis_up='Z',
                                     add_leaf_bones=False, armature_nodetype='NULL', bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.)
        OUT['exported'] = sorted(actions)
    json.dump(OUT, open(Path(rig.D) / 'Data' / f'fpvm_{KEY}_stances.json', 'w'), indent=1, default=str)
    print('FPVM_PISTOL2', json.dumps({k: OUT.get(k) for k in ('reach_cm', 'muzzle', 'exported')})[:900])


if __name__ == '__main__':
    main()
