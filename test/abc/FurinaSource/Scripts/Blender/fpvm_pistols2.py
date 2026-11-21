"""blender -b --python fpvm_pistols2.py -- <p38|p08|pp> [preview|rlpreview|export|reload_export] [옵션 json]
권총 1인칭 3자세(2026-11-21, 사용자 지정): 비조준 = 한손(낮게), 견착 = 팔을 쭉 뻗고 안쪽으로 20° 기울인 한손, 정조준 = 두 손 + 기계식 조준.
 근거(Motion/DE_FP_MOTION_RESEARCH.md 5-1절): 2차대전기 권총 사격은 한손 위주(Applegate 1943), 두 손 조준 자세는 전후 보급.
 정조준 자세 = 기존 두 손 자세(총 위치 PISTOL_POS) 그대로라 정조준 변환(fpvm_view_alignment.json)은 바뀌지 않음.
재장전(2026-11-21 2차, 고증 — 연구 문서 5-2절): 모델의 실제 탄창 부품(연결 성분)을 VM_Mag 뼈로 떼어 움직임(예전 상자 모양 임시 탄창 대신).
   P38: 손잡이 밑 뒤쪽 '힐(heel) 걸쇠' -> 왼손 엄지로 걸쇠를 밀며 탄창을 아래로 뽑음 -> 새 탄창 -> 손바닥으로 밀어 넣음 -> 슬라이드를 위에서 잡아 당겼다 놓음
   P08: 손잡이 왼쪽 탄창 단추(오른손 엄지) -> 탄창이 빠져 왼손에 떨어짐 -> 새 탄창 -> 토글 손잡이 두 개를 집어 위·뒤로 꺾었다 놓음
   PP : 방아쇠 뒤 왼쪽 탄창 단추(오른손 엄지) -> 탄창이 빠져 왼손에 떨어짐 -> 새 탄창 -> 슬라이드를 위에서 잡아 당겼다 놓음
   구도: 총을 가슴 앞으로 들어 손잡이 밑(탄창 입구)이 화면 가운데 약간 아래에서 보이게(자세 탐색). 2.5초.
 출력 FBX/FPVM: SK_FPVM_<KEY>.fbx + AS_FPVM_<KEY>_<Idle|Fire|IdleS|FireS|IdleA|FireA|Reload|T_HS|T_SH|T_HA|T_AH|T_SA|T_AS>.fbx
 Data/fpvm_<key>_stances.json: 자세별 손목-어깨 거리, 총구 위치(UE 카메라 공간), 탄창·재장전 자세"""
import json, math, sys
from pathlib import Path
import bmesh, bpy
import numpy as np
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fpvm_lib as rig
import fpvm_lib2 as poses
from fpvm_pistols import visual_top, unit_interval, PISTOL_POS

FPS = 30
A = sys.argv[sys.argv.index('--') + 1:]; KEY = A[0]; MODE = A[1] if len(A) > 1 else 'export'; OPT = json.loads(A[2]) if len(A) > 2 else {}
assert KEY in ('p38', 'p08', 'pp')
OUT = {'key': KEY}
# 자세별 총 이동(카메라 공간 cm, 회전 °: 오른손 손잡이 기준). 앞 +x, 왼쪽 +y, 위 +z, pitch + = 총구 위, roll - = 윗면이 왼쪽(안쪽)으로(미리보기로 확인)
STANCE = {
    'H': dict(fwd=-3.5, side=-3.0, up=-1.5, pitch=-6.0, roll=-8.0, yaw=4.0),   # 비조준: 낮게, 몸 쪽으로 당기고 총구 약간 아래, 윗면을 안쪽으로 조금(한손)
    'S': dict(fwd=-0.5, side=2.5, up=-2.0, pitch=0.0, roll=-20.0, yaw=-1.0),  # 견착: 팔을 끝까지 뻗고 총을 안쪽으로 20° 기울임(사용자 지정), 눈높이 조금 아래(한손)
    'A': dict(fwd=0.0, side=0.0, up=0.0, pitch=0.0, roll=0.0, yaw=0.0),       # 정조준: 기존 두 손 자세(정조준 변환과 맞물림)
}
for k, v in OPT.get('stance', {}).items(): STANCE[k].update(v)
KICK = {'H': (7.0, 2.0), 'S': (6.0, 2.2), 'A': (3.2, 1.7)}   # 사격 총구 들림(°)·뒤로 밀림(cm): 한손이 더 크게 튐
TRANS = {('H', 'S'): .20, ('S', 'H'): .20, ('H', 'A'): .25, ('A', 'H'): .25, ('S', 'A'): .22, ('A', 'S'): .22}
# 탄창 = 아래 상자 안에 완전히 들어가고 바닥 근처(zcut 아래)까지 내려오는 연결 성분(정점 좌표가 같으면 한 성분)
MAG_BOX = {'p38': ((-1.2, 1.2, -6.2), (0.8, 7.6, 4.2), -5.0), 'p08': ((-1.2, 0.5, -7.0), (1.1, 10.6, 4.8), -6.0), 'pp': ((-0.9, 1.5, -5.3), (0.7, 6.45, 3.4), -5.0)}
RELEASE = {'p38': 'heel', 'p08': 'button', 'pp': 'button'}
SLIDE_PULL_CM = {'p38': 3.2, 'pp': 2.6}   # P08 은 토글(회전)
RL_LEN = 2.5


def split_magazine(gun, key):
    lo_b, hi_b, zcut = MAG_BOX[key]
    bm = bmesh.new(); bm.from_mesh(gun.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    same = {}
    for v in bm.verts: same.setdefault(tuple(round(c, 3) for c in v.co), []).append(v.index)
    lab = [-1] * len(bm.verts); comps = []
    for v in bm.verts:
        if lab[v.index] >= 0: continue
        st = [v]; lab[v.index] = len(comps); ids = []
        while st:
            x = st.pop(); ids.append(x.index)
            for y in [e.other_vert(x) for e in x.link_edges] + [bm.verts[i] for i in same[tuple(round(c, 3) for c in x.co)]]:
                if lab[y.index] < 0: lab[y.index] = len(comps); st.append(y)
        comps.append(ids)
    co = np.array([v.co[:] for v in bm.verts]); take = set(); boxes = []
    for ci, ids in enumerate(comps):
        P = co[ids]; lo, hi = P.min(0), P.max(0)
        if all(lo[i] >= lo_b[i] for i in range(3)) and all(hi[i] <= hi_b[i] for i in range(3)) and lo[2] < zcut:
            take.add(ci); boxes.append([lo.round(2).tolist(), hi.round(2).tolist(), len(ids)])
    assert take, key
    sel = [f for f in bm.faces if lab[f.verts[0].index] in take]; ids = set(f.index for f in sel)
    me2 = gun.data.copy(); bm2 = bmesh.new(); bm2.from_mesh(me2); bm2.faces.ensure_lookup_table()
    bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in ids], context='FACES')
    bmesh.ops.delete(bm2, geom=[v for v in bm2.verts if not v.link_faces], context='VERTS'); bm2.to_mesh(me2); bm2.free()
    bmesh.ops.delete(bm, geom=sel, context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(gun.data); bm.free()
    mag = bpy.data.objects.new('W_mag', me2); bpy.context.scene.collection.objects.link(mag)
    M = np.array([v.co[:] for v in me2.vertices]); zmin, zmax = M[:, 2].min(), M[:, 2].max()
    bot = M[M[:, 2] < zmin + 1.0].mean(0); topc = M[M[:, 2] > zmax - 1.0].mean(0)
    d_ins = Vector(topc - bot).normalized()   # 꽂는 방향(손잡이 축, 아래 -> 위)
    return mag, Vector(M.mean(0)), Vector(bot), d_ins, {'faces': len(ids), 'parts': boxes, 'bottom': bot.round(2).tolist(), 'd_ins': [round(c, 3) for c in d_ins]}


def main():
    arm, hands, _ = rig.load_arms('a1'); arm.name = 'Armature'
    if hands.data.shape_keys: hands.shape_key_clear()
    for uv in list(hands.data.uv_layers)[1:]: hands.data.uv_layers.remove(uv)
    poses.fold_sleeves(arm)
    gun = rig.load_weapon(KEY); top = visual_top(gun, KEY)
    if KEY == 'p38':   # 원본의 슬라이드(윗몸)가 뒤로 0.83cm 물러나 있던 것 보정(다른 작업분 유지)
        top.data.transform(Matrix.Translation((0, -.83, 0)))
    mag, mag_c, mag_bot, d_ins, OUT['mag'] = split_magazine(gun, KEY)
    transform = rig.gun_native_to_cam(PISTOL_POS, 2.5, 4., -3.)
    for prop in (gun, top, mag): prop.matrix_world = transform
    bpy.context.view_layer.update()
    ik = poses.setup_ik(arm); mesh = poses.bvh_of([gun, top, mag])
    grip_y = {'p38': 5.5, 'p08': 6., 'pp': 4.6}[KEY]
    ax = {s: rig.hand_axes(arm, s) for s in 'LR'}; fax = {s: rig.finger_axes(arm, s, ax[s]) for s in 'LR'}
    controls = {}; WREST = {}   # WREST: 실제 손목 위치(두 손 자세). IK 목표(controls)는 팔 길이 밖일 수 있음(팔을 끝까지 뻗은 자세)
    for side, sign in (('R', 1), ('L', -1)):
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
    grip_one = dict(controls['R'][3])
    for b in rig.fbones('R', 'Thumb'): grip_one[b] = grip_one.get(b, 0.0) + 6.0
    rest_loc = Vector(OPT.get('l_rest', (0.03, 0.13, -0.40)))
    rest_rot = rig.wrist_rot_for(ax['L'], Vector((0.15, -0.1, -1.0)), Vector((0.0, -1.0, 0.1))).to_quaternion()
    def fset(v, s='L'): return {b: a for f, vals in v.items() for b, a in zip(rig.fbones(s, f), vals)}
    RELAX = fset({'Thumb': (10, 15, 10), 'IndexFinger': (20, 25, 15), 'MiddleFinger': (25, 30, 20), 'RingFinger': (30, 35, 20), 'LittleFinger': (30, 35, 20)})
    WRAP = fset({'Thumb': (25, 30, 25), 'IndexFinger': (45, 55, 40), 'MiddleFinger': (50, 60, 45), 'RingFinger': (55, 65, 45), 'LittleFinger': (55, 65, 45)})
    PINCH = fset({'Thumb': (20, 30, 25), 'IndexFinger': (55, 65, 45), 'MiddleFinger': (70, 85, 60), 'RingFinger': (75, 90, 60), 'LittleFinger': (75, 90, 60)})
    L_REST_POLE = Vector((-.10, .12, -.25))
    shR = arm.matrix_world @ arm.pose.bones['Right arm'].head; shL = arm.matrix_world @ arm.pose.bones['Left arm'].head
    ARM = ((arm.pose.bones['Right elbow'].head - arm.pose.bones['Right arm'].head).length + (arm.pose.bones['Right wrist'].head - arm.pose.bones['Right elbow'].head).length) * 100
    OUT['arm_len_cm'] = round(ARM, 1)
    pivot = WREST['R'].copy()
    def rot_about(pv, yaw, pitch, roll):
        R = Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(-pitch), 4, 'Y') @ Matrix.Rotation(math.radians(roll), 4, 'X')
        return Matrix.Translation(pv) @ R @ Matrix.Translation(-pv)
    def stance_D(s, kick=0.0, kick_s=None):
        p = STANCE[s]; kp, kb = KICK[kick_s or s]
        return Matrix.Translation(Vector((p['fwd'] - kb * kick, p['side'], p['up'] + 0.3 * kick)) / 100.0) @ rot_about(pivot, p['yaw'], p['pitch'] + kp * kick, p['roll'])
    def mix(Ma, Mb, x):
        la, ra, _ = Ma.decompose(); lb, rb, _ = Mb.decompose(); return Matrix.LocRotScale(la.lerp(lb, x), ra.slerp(rb, x), None)
    def blend_f(fa, fb, x): return {b: fa.get(b, 0.0) * (1 - x) + fb.get(b, 0.0) * x for b in set(fa) | set(fb)}
    OUT['reach_cm'] = {s: round(((stance_D(s) @ WREST['R']) - shR).length * 100, 1) for s in STANCE}
    # ---- 뼈
    root = transform @ Vector((0, 0, 0)); top_pivot = transform @ Vector((0, 5., 4.)); forward = Vector((.05, 0, 0))
    M0 = Matrix.LocRotScale(transform @ mag_c, transform.to_quaternion(), None)   # 탄창 정지(월드, 크기 1: 보간 때 0.01 배율이 빠져 탄창이 100배로 보였음)
    rig.add_bone(arm, 'VM_Gun', 'Hips', root, root + forward); rig.add_bone(arm, 'VM_Exterior', 'VM_Gun', top_pivot, top_pivot + forward)
    mw = M0.translation; rig.add_bone(arm, 'VM_Mag', 'VM_Gun', mw, mw + forward)
    rig.bind_rigid(arm, gun, 'VM_Gun'); rig.bind_rigid(arm, top, 'VM_Exterior'); rig.bind_rigid(arm, mag, 'VM_Mag')
    for bone in arm.pose.bones: bone.rotation_mode = 'QUATERNION'
    rest = {name: arm.data.bones[name].matrix_local.copy() for name in ('VM_Gun', 'VM_Exterior', 'VM_Mag')}
    constraints = [c for bone in arm.pose.bones for c in bone.constraints]
    # 총구
    P = [v.co for v in gun.data.vertices]; ymin = min(p.y for p in P); sl = [p for p in P if p.y < ymin + 0.3]
    mz = Vector((sum(p.x for p in sl) / len(sl), ymin, sum(p.z for p in sl) / len(sl)))
    wm = transform @ mz; fw = (transform.to_3x3() @ Vector((0, -1, 0))).normalized(); up = (transform.to_3x3() @ Vector((0, 0, 1))).normalized()
    OUT['muzzle'] = {'native_cm': [round(c, 3) for c in mz], 'ue_cam_cm': [wm.x * 100, -wm.y * 100, wm.z * 100], 'ue_fwd': [fw.x, -fw.y, fw.z], 'ue_up': [up.x, -up.y, up.z]}
    # ---- 재장전 손 상태(정지 총 기준으로 구해 둠)
    for c in constraints: c.mute = False
    ins_w = (transform.to_3x3() @ d_ins).normalized()
    MT = transform @ (mag_bot - d_ins * 0.6)
    H = poses.hand_local(arm, 'L', fax['L'], WRAP)
    W_mag0, OUT['L_mag'] = poses.search_hand(H, 'palm', MT, mesh, shL, reach_cm=100, excl=(MT, 0.03), prefer=[(ax['L']['p_local'], ins_w, 0.7), (ax['L']['f_local'], -(transform.to_3x3() @ Vector((1, 0, 0))), 0.3)])
    tv = [v.co for v in top.data.vertices]; tymax = max(v.y for v in tv); tzmax = max(v.z for v in tv)
    grab = Vector((0.0, tymax - (1.2 if KEY == 'p08' else 1.6), tzmax - (0.4 if KEY == 'p08' else 0.8)))
    ST_ = transform @ grab; H2 = poses.hand_local(arm, 'L', fax['L'], PINCH)
    W_slide0, OUT['L_slide'] = poses.search_hand(H2, 'pinch', ST_, mesh, shL, reach_cm=100, excl=(ST_, 0.02), prefer=[(ax['L']['p_local'], -up, 0.6), (ax['L']['f_local'], -(transform.to_3x3() @ Vector((1, 0, 0))), 0.3)])
    POUCH = Matrix.LocRotScale(Vector((0.05, 0.20, -0.42)), rig.wrist_rot_for(ax['L'], Vector((0.6, -0.3, 0.2)), Vector((0.0, -0.3, 1.0))).to_quaternion(), None)

    def slide_M(D, s):   # 슬라이드/토글 당김(0~1) -> 월드 변환(정지 대비)
        if KEY == 'p08': return D @ Matrix.Translation(top_pivot) @ Matrix.Rotation(math.radians(-62 * s), 4, 'Y') @ Matrix.Translation(-top_pivot)
        back = (transform.to_3x3() @ Vector((0, 1, 0))).normalized() * SLIDE_PULL_CM[KEY] / 100.0 * s
        return D @ Matrix.Translation(back)
    def pose_state(D, L_on=0.0, ext=0.0, fing_R=None, L_W=None, fing_L=None, mag_W=None, slide=0.0):
        """D: 총 이동, L_on: 0(쉼)~1(두 손 자세), ext: 사격 슬라이드 0~1, L_W: 왼손목 목표(월드, 주면 우선), mag_W: 탄창 월드(없으면 총 따라감), slide: 장전 당김 0~1"""
        locR, rotR, poleR, gripR = controls['R']; locL, rotL, poleL, gripL = controls['L']
        WR = Matrix.LocRotScale(D @ locR, D.to_quaternion() @ rotR, None)
        wantR = D @ WREST['R']; DBG['wantR'] = wantR
        if L_W is None:
            x = L_on; Won = Matrix.LocRotScale(D @ locL, D.to_quaternion() @ rotL, None)
            la, ra, _ = Matrix.LocRotScale(rest_loc, rest_rot, None).decompose(); lb, rb, _ = Won.decompose()
            bump = Vector((0, 0, .06 * math.sin(math.pi * x))) * (1 if 0 < x < 1 else 0)
            lL = la.lerp(lb, x) + bump; rL = ra.slerp(rb, x); wantL = rest_loc.lerp(D @ WREST['L'], x) + bump; poleUse = poleL * x + L_REST_POLE * (1 - x)
            fL = fing_L or blend_f(RELAX, gripL, x)
        else:
            lL, rL, _ = L_W.decompose(); wantL = lL; poleUse = L_REST_POLE; fL = fing_L or WRAP
        for s, (l, r, pole) in (('R', (WR.translation, WR.to_quaternion(), poleR)), ('L', (lL, rL, poleUse))):
            ik['T_' + s].location = l; ik['T_' + s].rotation_quaternion = r; ik['P_' + s].location = l + pole
        bpy.context.view_layer.update()
        for s, l in (('R', wantR), ('L', wantL)):
            for _ in range(6):
                err = l - (arm.matrix_world @ arm.pose.bones['%s wrist' % poses.SIDE[s]].head)
                if err.length < 2e-4: break
                ik['T_' + s].location = ik['T_' + s].location + err; bpy.context.view_layer.update()
        poses.apply_fingers(arm, fax['R'], fing_R or gripR); poses.apply_fingers(arm, fax['L'], fL)
        arm.pose.bones['VM_Gun'].matrix = D @ rest['VM_Gun']; bpy.context.view_layer.update()
        acc = Matrix.Translation((-.008 * ext, 0, .003 * ext))
        if KEY == 'p08': acc = Matrix.Translation(top_pivot) @ Matrix.Rotation(math.radians(-18 * ext), 4, 'Y') @ Matrix.Translation(-top_pivot)
        S = slide_M(D, slide) if slide > 0 else D @ acc
        arm.pose.bones['VM_Exterior'].matrix = S @ rest['VM_Exterior']
        Mw = mag_W if mag_W is not None else D @ M0
        arm.pose.bones['VM_Mag'].matrix = Mw @ M0.inverted() @ rest['VM_Mag']
        bpy.context.view_layer.update()
    LON = {'H': 0.0, 'S': 0.0, 'A': 1.0}; DBG = {}
    def fingR(s): return controls['R'][3] if s == 'A' else grip_one
    clips = {}
    for s in 'HSA':
        def idle(t, s=s):
            b = math.sin(t / 4 * math.tau); amp = {'H': 1.6, 'S': 1.0, 'A': 1.0}[s]
            pose_state(Matrix.Translation((0, 0, .0016 * amp * b)) @ stance_D(s), LON[s], fing_R=fingR(s))
        def fire(t, s=s):
            k = unit_interval(t, 0, .045) * (1 - unit_interval(t, .05, .24)); pose_state(stance_D(s, k), LON[s], ext=k, fing_R=fingR(s))
        suf = {'H': '', 'S': 'S', 'A': 'A'}[s]
        clips['Idle' + suf] = (idle, 4.0); clips['Fire' + suf] = (fire, .30)
    for (a, b), dur in TRANS.items():
        def tr(t, a=a, b=b, dur=dur):
            x = unit_interval(t, 0, dur); pose_state(mix(stance_D(a), stance_D(b), x), LON[a] * (1 - x) + LON[b] * x, fing_R=fingR(a) if x < .5 else fingR(b))
        clips[f'T_{a}{b}'] = (tr, dur)
    # ---- 재장전 자세 탐색: 손잡이 밑(탄창 입구)이 화면 가운데 약간 아래, 입구가 카메라 쪽, 손이 닿게
    def view_ang(p): return math.degrees(math.atan2(-p.y, max(p.x, 1e-3))), math.degrees(math.atan2(p.z, max(p.x, 1e-3)))
    well = transform @ mag_bot; best = None
    for yw in (20, 35, 50, 65):
        for rl in (-80, -65, -50, -35):
            for pt in (0, 10, 20, 30):
                for sd in (4, 8, 12):
                    for upv in (4, 8, 12):
                        for fwv in (-12, -8, -4):
                            Dt = Matrix.Translation(Vector((fwv, sd, upv)) / 100.0) @ rot_about(pivot, yw, pt, rl)
                            if ((Dt @ WREST['R']) - shR).length * 100 > ARM - 0.3: continue
                            wmg = Dt @ M0 @ M0.inverted() @ W_mag0; wsl = Dt @ W_slide0
                            if (wmg.translation - shL).length * 100 > ARM - 0.3 or (wsl.translation - shL).length * 100 > ARM - 0.3: continue
                            g = Dt @ well; hg, vg = view_ang(g); left = (Dt.to_3x3() @ transform.to_3x3() @ Vector((1, 0, 0))).normalized(); vis = left.dot((-g).normalized())   # 총 왼쪽 면(탄창 단추·힐 걸쇠 쪽)이 카메라 쪽
                            hw, _ = view_ang(Dt @ WREST['R']); cost = abs(hg + 3) + abs(vg + 9) + 30 * max(0, 0.35 - vis) + 3 * max(0, 22 - g.length * 100) + 2 * max(0, hg - (hw - 6))   # 입구가 오른 손목보다 화면 왼쪽(팔에 안 가리게) + 0.05 * (abs(rl) * 0.3 + pt * 0.2 + yw * 0.1)
                            if best is None or cost < best[0]: best = (cost, dict(fwd=fwv, side=sd, up=upv, yaw=yw, pitch=pt, roll=rl), [round(hg, 1), round(vg, 1), round(vis, 2)])
    RLP = OPT.get('rl_pose') or best[1]; OUT['reload_pose'] = {'pose': RLP, 'hv_vis': best[2] if best else None}
    D_RL = Matrix.Translation(Vector((RLP['fwd'], RLP['side'], RLP['up'])) / 100.0) @ rot_about(pivot, RLP['yaw'], RLP['pitch'], RLP['roll'])
    T = {'up': (0.0, .30), 'toMag': (.05, .32), 'out': (.32, .55), 'toPouch': (.55, .95), 'toWell': (.95, 1.38), 'insert': (1.38, 1.52), 'slap': (1.52, 1.60),
         'toSlide': (1.62, 1.88), 'pull': (1.88, 2.02), 'rel': (2.02, 2.07), 'toRest': (2.07, 2.45), 'down': (2.10, 2.50)}
    seg = lambda t, ab: unit_interval(t, *ab)
    def bw(Wa, Wb, x, lift=0.0):
        la, ra, _ = Wa.decompose(); lb, rb, _ = Wb.decompose(); return Matrix.LocRotScale(la.lerp(lb, x) + Vector((0, 0, lift * math.sin(math.pi * x))), ra.slerp(rb, x), None)
    def reload(t):
        k = seg(t, T['up']) * (1 - seg(t, T['down'])); D = mix(stance_D('H'), D_RL, k)
        insw = (D.to_3x3() @ ins_w).normalized(); M_in = D @ M0
        drop = 7.5 / 100.0; M_below = Matrix.Translation(-insw * drop) @ M_in
        M_pouch = POUCH @ (M0.inverted() @ W_mag0).inverted()
        if t < T['out'][0]: Mw = M_in
        elif t < T['out'][1]:
            x = seg(t, T['out']) if RELEASE[KEY] == 'heel' else min(1.0, ((t - T['out'][0]) / 0.12) ** 2)   # 힐 걸쇠: 손으로 뽑음 / 단추: 떨어짐
            Mw = Matrix.Translation(-insw * drop * x) @ M_in
        elif t < T['toPouch'][1]: Mw = bw(M_below, M_pouch, seg(t, T['toPouch']), 0.02)
        elif t < T['toWell'][1]: Mw = bw(M_pouch, M_below, seg(t, T['toWell']), 0.03)
        elif t < T['insert'][1]: Mw = bw(M_below, M_in, seg(t, T['insert']))
        else: Mw = Matrix.Translation(insw * 0.004 * math.sin(math.pi * seg(t, T['slap']))) @ M_in   # 손바닥으로 쳐서 끝까지
        hand_on_mag = Mw @ M0.inverted() @ W_mag0
        catch = Matrix.Translation(-insw * drop) @ (M_in @ M0.inverted() @ W_mag0)   # 단추식: 왼손이 입구 아래서 받음
        rest_W = Matrix.LocRotScale(rest_loc, rest_rot, None)
        s = seg(t, T['pull']) * (1 - min(1.0, max(0.0, (t - T['rel'][0]) / (T['rel'][1] - T['rel'][0]))))
        slide_W = slide_M(D, s) @ W_slide0
        if t < T['toMag'][1]:
            x = seg(t, T['toMag']); target = hand_on_mag if RELEASE[KEY] == 'heel' else catch
            LW = bw(rest_W, target, x, 0.03); fl = blend_f(RELAX, WRAP, x)
        elif t < T['out'][1] and RELEASE[KEY] != 'heel': LW = catch; fl = WRAP   # 단추식: 탄창이 손 위로 떨어질 때까지 손은 입구 아래에서 대기
        elif t < T['toSlide'][0]: LW = hand_on_mag; fl = WRAP
        elif t < T['toSlide'][1]: LW = bw(hand_on_mag, slide_W, seg(t, T['toSlide']), 0.03); fl = blend_f(WRAP, PINCH, seg(t, T['toSlide']))
        elif t < T['toRest'][0]: LW = slide_W; fl = PINCH
        else: x = seg(t, T['toRest']); LW = bw(slide_W, rest_W, x, 0.02); fl = blend_f(PINCH, RELAX, x)
        pose_state(D, L_W=LW, fing_L=fl, fing_R=grip_one, mag_W=Mw, slide=s)
    clips['Reload'] = (reload, RL_LEN)
    OUT['clips'] = {k: v[1] for k, v in clips.items()}
    if MODE in ('preview', 'rlpreview'):
        for m in bpy.data.materials: m.diffuse_color = (0.85, 0.7, 0.62, 1) if 'Skin' in m.name else (0.25, 0.3, 0.55, 1) if 'Outfit' in m.name else (0.3, 0.3, 0.32, 1)
        mag.data.materials.clear(); mm = bpy.data.materials.new('MagPreview'); mm.diffuse_color = (0.75, 0.45, 0.15, 1); mag.data.materials.append(mm)
        R_ = []
        shots = (('H', clips['Idle'][0], 0), ('S', clips['IdleS'][0], 0), ('A', clips['IdleA'][0], 0)) if MODE == 'preview' else \
                tuple((f'rl{int(t * 100):03d}', reload, t) for t in (0.30, 0.45, 0.75, 1.30, 1.55, 1.95, 2.30))
        for nm, fn, t in shots:
            fn(t); R_ += poses.render_views(str(Path(rig.D) / 'Data' / f'fpvm_{KEY}_st_{nm}'), views=('fp', 'side'), look=tuple(transform @ Vector((0, 0, 0))), scale=0.6)
        OUT['renders'] = R_
    else:
        actions = {}
        selected = {'Reload': clips['Reload']} if MODE == 'reload_export' else clips
        for name, (fn, dur) in selected.items():
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
        bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1.0
        bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
        path = Path(rig.D) / 'FBX' / 'FPVM' / f'SK_FPVM_{KEY.upper()}.fbx'
        if MODE == 'export':
            arm.animation_data.action = actions['IdleA']   # 메시 기준 자세 = 정조준(두 손)
            for o in (hands, gun, top, mag): o.select_set(True)
            bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'ARMATURE', 'MESH'}, axis_forward='-Y', axis_up='Z', add_leaf_bones=False,
                                     armature_nodetype='NULL', bake_anim=False, mesh_smooth_type='FACE', path_mode='STRIP')
            bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
        for name, act in actions.items():
            arm.animation_data.action = act; s0, s1 = act.frame_range; bpy.context.scene.frame_start = round(s0); bpy.context.scene.frame_end = round(s1)
            bpy.ops.export_scene.fbx(filepath=str(path.with_name(f'AS_FPVM_{KEY.upper()}_{name}.fbx')), use_selection=True, object_types={'ARMATURE'}, axis_forward='-Y', axis_up='Z',
                                     add_leaf_bones=False, armature_nodetype='NULL', bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.)
        OUT['exported'] = sorted(actions)
    json.dump(OUT, open(Path(rig.D) / 'Data' / f'fpvm_{KEY}_stances.json', 'w'), indent=1, default=str)
    print('FPVM_PISTOL2', json.dumps({k: OUT.get(k) for k in ('mag', 'reload_pose', 'L_mag', 'L_slide', 'exported')})[:1200])


if __name__ == '__main__':
    main()
