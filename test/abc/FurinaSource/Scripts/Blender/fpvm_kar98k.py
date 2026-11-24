"""blender -b --python fpvm_kar98k.py -- <pose|anim|export> [옵션 json] : Kar98k 1인칭 뷰모델(푸리나 팔 + 총 한 몸 스켈레탈)
 근거: Motion/DE_FP_MOTION_RESEARCH.md 1절(교범 순서, 출처 3개 이상, 참고 애니 수치). 참고 zip 의 메시/뼈/키는 쓰지 않음.
 총 원본 좌표(cm): 총구 -Y, 위 +Z, 총의 오른쪽 -X. 볼트 축 (x 0.65, z 6.92). 볼트 = Material_005(회전부: 몸통+손잡이 / 덮개 shroud: 미끄럼만).
 클립 = SM_DE_mauser_clip(5발, 탄 쌓임 z, 탄두 -Y, 클립 판 y 3.7~4.1) -> 뒤 브리지 클립 홈(y 14.3)에 꽂음.
 단계  pose: 대기 자세 정지 렌더 / anim: 클립 3개 만들고 주요 프레임 렌더 / export: anim + FBX(FBX/FPVM/SK_FPVM_Kar98k.fbx)
 클립(30fps): Idle 4.0초(호흡), Fire 1.2초(반동 + 볼트 위-뒤-앞-아래, 1.0~1.4초 = 분당 10~15발 조준 사격), Reload 3.2초(클립 장전 5발).
 결과 수치 -> Data/fpvm_kar98k.json (조준선 점: ADS 정렬용)"""
import bpy, sys, json, math, os
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import numpy as np
from mathutils import Matrix, Vector, Quaternion
import fpvm_lib as L, fpvm_lib2 as L2
from fpvm_receiver_interior import add_existing_optic, add_receiver_interior, export_mesh_only
from fpvm_loose_round import build_timeline, export_animations
A = sys.argv[sys.argv.index('--') + 1:]; STAGE = A[0]; OPT = json.loads(A[1]) if len(A) > 1 else {}
D = L.D; OUT = {'stage': STAGE}; FPS = 30
# ---------------------------------------------------------------- 수치(원본 cm)
BOLT_AX = (0.65, 6.92); SHROUD_Y = 18.37
KNOB = (-2.37, 17.87, 3.56)                 # 볼트 손잡이 공 중심
BOLT_TRAVEL = OPT.get('bolt_travel', 8.8)  # 7.92x57 전장 8.2cm + 여유
BOLT_LIFT = 90.0                           # Mauser 98: 90° 회전 볼트
CLIP_IN = (0.65, 10.4, 9.9)                # 클립 원점 -> 총 원본: 클립 판이 y 14.1~14.5(브리지 앞면 홈), 탄 바닥 z 6.45
PUSH = 5.6                                 # 엄지로 탄을 눌러 넣는 거리
R_CONTACT = OPT.get('r_contact', [-10.0, 29.0, 1.2])
GUN_POS = OPT.get('gun_pos', [32.0, -9.0, -12.5]); GUN_ROT = OPT.get('gun_rot', [2.5, 4.0, -3.0]); YL = OPT.get('yL', -2.0)   # 2026-11-21: 오른손목이 어깨에서 18cm 이상(팔이 접혀 IK 팔꿈치가 뒤집히던 문제). 예전 21
CLAV = {'L': [-10.73, 9.89, -16.11], 'R': [-17.46, -9.78, -17.09]}; REACH = OPT.get('reach', 37.0)
POLE = {'R': Vector((-0.12, -0.10, -0.15)), 'L': Vector((-0.10, 0.12, -0.15))}

arm, body, info = L.load_arms('a1', 0); OUT['arms'] = info; arm.name = 'Armature'
CA = L.class_arm_objects(arm)   # 병과 캐릭터 7종 1인칭 팔(같은 팔 뼈대, 재질 CA<Key>_*): 내보낼 때 함께 선택
bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1.0   # 애니 30fps(기본 24 이면 UE 길이가 1.25배)
OUT['clavicle_err_cm'] = L2.pose_clavicles(arm, CLAV)
OUT['sleeves_folded'] = L2.fold_sleeves(arm)   # 소매 날개 접기(손 가림 방지), 아래에서 휴식 자세로 굳힘
# 쇄골 자세를 휴식 자세로 굳힘(애니 내내 고정): 메시 변형을 먼저 굳히고(모디파이어 적용) 뼈 휴식 자세 갱신 후 모디파이어 다시 연결
L.bake_arms_rest(arm, [body] + CA)   # 푸리나 팔 + 병과 팔 모두 같은 휴식 자세로(2026-11-22)
for _uv in list(body.data.uv_layers)[1:]: body.data.uv_layers.remove(_uv)   # 팔 메시 UV 1개만(무기 메시와 UV 채널 수를 맞춤: UE 합칠 때 무기 UV 가 어긋나던 문제)
gun = L.load_weapon('kar98k')
if GUN_POS[0] is None:
    sh0 = arm.matrix_world @ arm.pose.bones['Left arm'].head
    for px in np.arange(45.0, 10.0, -0.5):
        Gt = L.gun_native_to_cam([px, GUN_POS[1], GUN_POS[2]], *GUN_ROT); w = Gt @ Vector((0.65, YL, 2.2)) + Vector((-0.005, 0.03, -0.035))
        if (w - sh0).length * 100 <= REACH: GUN_POS[0] = float(px); break
OUT['gun_pos'] = GUN_POS[:]; OUT['gun_rot'] = GUN_ROT[:]
if 'yL' not in OPT:   # 왼손: 어깨에서 REACH 안에 닿는 가장 앞쪽 아래면(케이 98k: 탄창 바닥판 앞 / G43: 탄창 아래)
    _sh = arm.matrix_world @ arm.pose.bones['Left arm'].head; _G = L.gun_native_to_cam(GUN_POS, *GUN_ROT)
    for _y in [v * 0.5 for v in range(-20, 41)]:
        _w = _G @ Vector((BOLT_AX[0], _y, 1.0)) + Vector((-0.005, 0.03, -0.045))
        if (_w - _sh).length * 100 <= REACH: YL = _y; break
OUT['yL'] = YL
bolt, nb = L.split_by(gun, 'W_bolt', lambda m, c: m.startswith('Material_005') and (c.y < SHROUD_Y or c.x < -0.7))
shroud, ns = L.split_by(gun, 'W_shroud', lambda m, c: m.startswith('Material_005'))
clip = L.load_weapon('mauser_clip')
for m in clip.data.materials:   # 소총 재질 이름(Material, Material_001...)과 겹치지 않게
    if m: m.name = {'Material': 'Clip_Steel', '6.5': 'Clip_Projectile', 'case': 'Clip_Case'}.get(m.name.split('.')[0] if m.name.startswith('Material') else m.name, m.name)
rounds, nr = L.split_by(clip, 'W_rounds', lambda m, c: m in ('Clip_Case', 'Clip_Projectile'))
G0 = L.gun_native_to_cam(GUN_POS, *GUN_ROT); C0 = G0 @ Matrix.Translation(CLIP_IN)
for o in (gun, bolt, shroud): o.matrix_world = G0
for o in (clip, rounds): o.matrix_world = C0
bpy.context.view_layer.update()
def nat(p, M=None): return (M or G0) @ Vector(p)
bvh_all = L2.bvh_of([gun, bolt, shroud]); bvh_bolt = L2.bvh_of([bolt]); bvh_clip = L2.bvh_of([clip, rounds])
def ray(bvh, o_native, d_native, M=None):
    M = M or G0; o = M @ Vector(o_native); d = (M.to_3x3() @ Vector(d_native)).normalized(); return bvh.ray_cast(o, d, 2.0)[0]
# ---------------------------------------------------------------- 조준선(ADS 정렬): 뒤 가늠자 홈, 앞 가늠쇠 끝(원본)
def top_point(y0, y1, xw=1.2):
    best = None
    for o in (gun,):
        M = o.matrix_world
        for v in o.data.vertices:
            p = v.co
            if y0 <= p.y <= y1 and abs(p.x - 0.65) <= xw and (best is None or p.z > best.z): best = p.copy()
    return best
fs = top_point(-56.0, -48.0, 0.5); rs = top_point(-13.0, -3.5, 0.5)
OUT['sight_native'] = {'front': [round(v, 3) for v in fs], 'rear_top': [round(v, 3) for v in rs]}
# ---------------------------------------------------------------- 손 상태(손목 월드 행렬, 기준 프레임 상대)
E = L2.setup_ik(arm); ax = {s: L.hand_axes(arm, s) for s in 'LR'}; fax = {s: L.finger_axes(arm, s, ax[s]) for s in 'LR'}
def solve_place(s, contact, f, p, along=0.45, off=1.6):
    r = L2.place_hand(arm, E, s, ax[s], contact, f, p, palm_off_cm=off, along=along, elbow_hint_m=contact + POLE[s])
    return r
def dirn(d, M=None): return (( M or G0).to_3x3() @ Vector(d)).normalized()
def wrist_world(s):   # 실제 손목 뼈 머리 위치(IK 목표 위치를 쓰면 IK 가 덜 닿을 때 재생 시 수 cm 어긋났음) + 목표 회전
    bpy.context.view_layer.update(); return Matrix.LocRotScale((arm.matrix_world @ arm.pose.bones['%s wrist' % L2.SIDE[s]].head).copy(), E['T_' + s].rotation_quaternion.copy(), None)
ST = {}
# 오른손 손잡이(개머리 손목 오른쪽 면): 손가락 앞-아래, 손바닥 총 왼쪽
_h = bvh_all.ray_cast(G0 @ Vector(R_CONTACT), dirn((1, 0, 0)), 2.0); rc = _h[0]; fR = dirn((0.15, -0.65, -0.75)); pR = (-_h[1]).normalized()   # 손바닥 = 닿는 면의 반대 법선(면에 평평하게)
OUT['R_grip'] = solve_place('R', rc, fR, pR); OUT['R_grip']['pole'] = L2.calib_pole(arm, E, 'R', E['T_R'].location.copy(), rc + POLE['R']); solve_place('R', rc, fR, pR)
OUT.setdefault('seat_cm', {})['R_GRIP'] = L2.seat_hand(arm, body, E, 'R', ax['R'], bvh_all)   # 손바닥을 총 표면에 붙임(떠 있던 문제)
import fpvm_grip; _trig, OUT['trigger'] = fpvm_grip.trigger_target(arm, 'R', bvh_all, G0)   # 검지 = 방아쇠울 안 방아쇠 앞면(2026-11-22)
ST['R_GRIP'] = {'ref': 'gun', 'W': wrist_world('R'), 'fing': L2.grip_fingers(arm, 'R', fax['R'], bvh_all, r_cm=0.55, limits={'Thumb': (20, 25, 25), 'default': (85, 100, 75)}, targets={'IndexFinger': (_trig[0], 1.0, _trig[1])} if _trig is not None else None)}
OUT['R_grip_fingers'] = fpvm_grip.LAST.get('R')
# 왼손 앞받침(손바닥 위, 손가락이 오른쪽 면을 감쌈). 손바닥 중심을 왼쪽으로 1.5cm 옮겨 손가락 뿌리가 오른쪽 모서리에 오게
_h = bvh_all.ray_cast(G0 @ Vector((BOLT_AX[0], YL, -15.0)), dirn((0, 0, 1)), 2.0); lc = _h[0]; fL = dirn((-1.0, -0.25, 0.15)); pL = (-_h[1]).normalized()
lc2 = lc - fL * 0.015
OUT['L_grip'] = solve_place('L', lc2, fL, pL); OUT['L_grip']['pole'] = L2.calib_pole(arm, E, 'L', E['T_L'].location.copy(), lc2 + POLE['L']); solve_place('L', lc2, fL, pL)
OUT.setdefault('seat_cm', {})['L_GRIP'] = L2.seat_hand(arm, body, E, 'L', ax['L'], bvh_all)   # 손바닥을 총 표면에 붙임(떠 있던 문제)
ST['L_GRIP'] = {'ref': 'gun', 'W': wrist_world('L'), 'fing': L2.grip_fingers(arm, 'L', fax['L'], bvh_all, r_cm=0.55, limits={'Thumb': (15, 20, 20), 'default': (85, 100, 75)})}
YLR = OPT.get('yLR', max(7.0, YL))   # 장전 중 왼손: 탄창 앞쪽 아래로 미끄러져 총을 몸 앞(화면 안)으로 가져옴
lcr = ray(bvh_all, (BOLT_AX[0], YLR, -15.0), (0, 0, 1)) - fL * 0.015
OUT['L_reload'] = solve_place('L', lcr, fL, pL)
OUT.setdefault('seat_cm', {})['L_RELOAD'] = L2.seat_hand(arm, body, E, 'L', ax['L'], bvh_all)   # 손바닥을 총 표면에 붙임(떠 있던 문제)
ST['L_RELOAD'] = {'ref': 'gun', 'W': wrist_world('L'), 'fing': L2.grip_fingers(arm, 'L', fax['L'], bvh_all, r_cm=0.55, limits={'Thumb': (15, 20, 20), 'default': (85, 100, 75)})}
# 오른손 볼트/클립/엄지: 손가락 모양을 먼저 고정하고, 잡는 점이 목표에 오면서 총을 관통하지 않는 손 방향을 탐색(fpvm_lib2.search_hand)
shR = arm.matrix_world @ arm.pose.bones['Right arm'].head
def fset(v): return {b: a for f, vals in v.items() for b, a in zip(L.fbones('R', f), vals)}
BOLT_F = fset({'Thumb': (20, 30, 25), 'IndexFinger': (55, 65, 45), 'MiddleFinger': (70, 85, 60), 'RingFinger': (75, 90, 60), 'LittleFinger': (75, 90, 60)})
CLIP_F = fset({'Thumb': (15, 20, 15), 'IndexFinger': (35, 40, 30), 'MiddleFinger': (70, 85, 60), 'RingFinger': (75, 90, 60), 'LittleFinger': (80, 90, 60)})
PF = fset({'Thumb': (0, 5, 5), 'IndexFinger': (70, 90, 60), 'MiddleFinger': (75, 95, 60), 'RingFinger': (80, 95, 60), 'LittleFinger': (80, 95, 60)})
pl = ax['R']['p_local']; fl = ax['R']['f_local']
K = nat(KNOB); H = L2.hand_local(arm, 'R', fax['R'], BOLT_F)
Wb, OUT['R_bolt'] = L2.search_hand(H, 'pinch', K, bvh_all, shR, excl=(K, 0.017), prefer=[(pl, dirn((1, 0, 0.3)), 0.6), (fl, dirn((0.3, -1, 0)), 0.4)])
ST['R_BOLT'] = {'ref': 'bolt', 'W': Wb, 'fing': BOLT_F}
bvh_gc = L2.bvh_of([gun, bolt, shroud, clip, rounds])
CT = nat((0.0, 3.9, 3.2), C0); H = L2.hand_local(arm, 'R', fax['R'], CLIP_F)
Wc, OUT['R_clip'] = L2.search_hand(H, 'pinch', CT, bvh_gc, shR, excl=(CT, 0.015), prefer=[(pl, dirn((1, 0, 0)), 0.4), (fl, dirn((0, -0.3, -1)), 0.4)])
ST['R_CLIP'] = {'ref': 'clip', 'W': Wc, 'fing': CLIP_F}
target = nat((0.0, 2.6, 3.4 + 0.45), C0); H = L2.hand_local(arm, 'R', fax['R'], PF)
Wp2, OUT['R_push'] = L2.search_hand(H, 'thumb_tip', target, bvh_gc, shR, excl=(target, 0.012), prefer=[(pl, dirn((0.8, 0, -0.6)), 0.4), (fl, dirn((0.3, -1, -0.5)), 0.3)])
ST['R_PUSH'] = {'ref': 'rounds', 'W': Wp2, 'fing': PF}
# 탄입대(화면 아래 오른쪽 밖): 손바닥 위, 클립 쥔 손
Wpouch = Matrix.LocRotScale(Vector((0.02, -0.24, -0.40)), L.wrist_rot_for(ax['R'], Vector((0.6, 0.3, 0.2)), Vector((0.0, 0.3, 1.0))).to_quaternion(), None)
ST['R_POUCH'] = {'ref': 'cam', 'W': Wpouch, 'fing': ST['R_CLIP']['fing']}
OUT['states'] = list(ST)
# ---------------------------------------------------------------- 뼈(무기 부품) + 스키닝
root = 'Hips'
def bone_at(name, parent, head_native, M):
    h = M @ Vector(head_native); t = M @ (Vector(head_native) + Vector((0, -5.0, 0))); L.add_bone(arm, name, parent, h, t)
bone_at('VM_Gun', root, (0, 0, 0), G0); bone_at('VM_Bolt', 'VM_Gun', (BOLT_AX[0], 18.0, BOLT_AX[1]), G0); bone_at('VM_Shroud', 'VM_Gun', (BOLT_AX[0], 18.0, BOLT_AX[1]), G0)
bone_at('VM_Clip', 'VM_Gun', (0, 0, 0), C0); bone_at('VM_Rounds', 'VM_Clip', (0, 0, 0), C0)
for o, b in ((gun, 'VM_Gun'), (bolt, 'VM_Bolt'), (shroud, 'VM_Shroud'), (clip, 'VM_Clip'), (rounds, 'VM_Rounds')): L.bind_rigid(arm, o, b)
receiver_interior = add_receiver_interior('Kar98k', arm, G0)
if STAGE == 'meshfix':
    export_mesh_only(D + r'\FBX\FPVM\SK_FPVM_Kar98k_Interior.fbx', arm, (body, gun, bolt, shroud, clip, rounds, receiver_interior))
    raise SystemExit(0)
if STAGE in ('zf39', 'zf41'):
    optic = add_existing_optic('kar98k_' + STAGE, arm, G0)
    export_mesh_only(D + r'\FBX\FPVM\SK_FPVM_Kar98k_' + STAGE.upper() + '.fbx', arm, (body, gun, bolt, shroud, clip, rounds, receiver_interior, optic))
    raise SystemExit(0)
REST = {b.name: b.matrix_local.copy() for b in arm.data.bones}
# ---------------------------------------------------------------- 운동학
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def seg(t, t0, t1): return ease((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)
def gun_delta(back=0.0, up=0.0, pitch=0.0, roll=0.0, yaw=0.0, side=0.0):
    """카메라 공간 강체 변환(m): 개머리 쪽 피벗(원본 (0.65, 40, 0)) 기준 회전 + 이동(cm)."""
    pv = G0 @ Vector((0.65, 40.0, 0.0))
    R = Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(-pitch), 4, 'Y') @ Matrix.Rotation(math.radians(roll), 4, 'X')
    return Matrix.Translation(Vector((-back, side, up)) / 100.0) @ Matrix.Translation(pv) @ R @ Matrix.Translation(-pv)
def bolt_native(theta, s):
    sgn = OPT.get('lift_sign', 1.0)
    return Matrix.Translation((0, s, 0)) @ Matrix.Translation((BOLT_AX[0], 0, BOLT_AX[1])) @ Matrix.Rotation(math.radians(sgn * theta), 4, 'Y') @ Matrix.Translation((-BOLT_AX[0], 0, -BOLT_AX[1]))
# 손잡이 들기 방향 부호 확인(들면 공이 위로)
k0 = Vector(KNOB); k1 = bolt_native(90, 0) @ k0
if k1.z < k0.z: OPT['lift_sign'] = -1.0
OUT['knob_lifted_native'] = [round(v, 2) for v in (bolt_native(90, 0) @ k0)]
def frames(state):
    """상태 dict -> 기준 프레임 월드 행렬들."""
    Gw = state['D'] @ G0; Bw = Gw @ bolt_native(state['theta'], state['s']); Cw = state.get('Cw') or (Gw @ Matrix.Translation(CLIP_IN))
    Rw = Cw @ Matrix.Translation((0, 0, -state['push']))
    return {'gun': Gw, 'bolt': Bw, 'shroud': Gw @ bolt_native(0, state['s']), 'clip': Cw, 'rounds': Rw, 'cam': Matrix.Identity(4)}
REF0 = frames({'D': Matrix.Identity(4), 'theta': 0, 's': 0, 'push': 0})
REL = {k: REF0[v['ref']].inverted() @ v['W'] for k, v in ST.items()}
def hand_world(key, F): return F[ST[key]['ref']] @ REL[key]
def blend_W(Wa, Wb, x, lift=0.0):
    return L2.blend_hand_motion(Wa, Wb, x, lift)
def blend_f(fa, fb, x): return {b: fa.get(b, 0.0) * (1 - x) + fb.get(b, 0.0) * x for b in set(fa) | set(fb)}
# ---------------------------------------------------------------- 클립 타임라인: 시간 -> (총 변환, 볼트, 손 상태 키 + 섞기 비율, 클립/탄 표시)
def tl_idle(t):
    ph = 2 * math.pi * t / 4.0
    return {'D': gun_delta(up=0.25 * math.sin(ph), pitch=0.25 * math.sin(ph + 0.6), roll=0.15 * math.sin(ph * 0.5)), 'theta': 0, 's': 0, 'push': 0,
            'R': ('R_GRIP', 'R_GRIP', 0, 0), 'clip_vis': 0, 'rounds_vis': 0}
FIRE_T = {'kick': (0.0, 0.05), 'ret': (0.05, 0.30), 'toBolt': (0.06, 0.32), 'lift': (0.32, 0.40), 'pull': (0.40, 0.52), 'push': (0.60, 0.74), 'down': (0.74, 0.82), 'toGrip': (0.82, 1.10), 'cant': (0.10, 0.30, 0.85, 1.10)}
def tl_fire(t):
    T = FIRE_T; k = seg(t, *T['kick']) * (1 - seg(t, *T['ret'])); c = seg(t, T['cant'][0], T['cant'][1]) * (1 - seg(t, T['cant'][2], T['cant'][3]))
    D_ = gun_delta(back=3.0 * k, up=0.8 * k, pitch=3.0 * k, roll=6.0 * c, yaw=1.0 * c)
    th = BOLT_LIFT * seg(t, *T['lift']) * (1 - seg(t, *T['down'])); s = BOLT_TRAVEL * seg(t, *T['pull']) * (1 - seg(t, *T['push']))
    if t < T['toGrip'][0]: R = ('R_GRIP', 'R_BOLT', seg(t, *T['toBolt']), 3.0)
    else: R = ('R_BOLT', 'R_GRIP', seg(t, *T['toGrip']), 2.0)
    return {'D': D_, 'theta': th, 's': s, 'push': 0, 'R': R, 'clip_vis': 0, 'rounds_vis': 0}
REL_T = {'tilt': (0.0, 0.35, 2.80, 3.15), 'toBolt': (0.05, 0.35), 'lift': (0.35, 0.45), 'pull': (0.45, 0.58), 'toPouch': (0.58, 1.05), 'toGuide': (1.05, 1.55), 'insert': (1.55, 1.70),
         'toPush': (1.70, 1.85), 'push': (1.85, 2.35), 'toBolt2': (2.35, 2.55), 'fwd': (2.55, 2.70), 'down': (2.70, 2.78), 'eject': (2.60, 2.85), 'toGrip': (2.78, 3.15)}
def tl_reload(t):
    T = REL_T; c = seg(t, T['tilt'][0], T['tilt'][1]) * (1 - seg(t, T['tilt'][2], T['tilt'][3]))
    D_ = gun_delta(**{k: v * c for k, v in RELOAD_D.items()})   # 장전: 어깨에서 내려 몸 앞으로(클립 홈이 화면 안), 오른쪽으로 기울임
    th = BOLT_LIFT * seg(t, *T['lift']) * (1 - seg(t, *T['down'])); s = BOLT_TRAVEL * seg(t, *T['pull']) * (1 - seg(t, *T['fwd']))
    st = {'D': D_, 'theta': th, 's': s, 'push': PUSH * seg(t, *T['push']), 'clip_vis': 1 if T['toPouch'][0] + 0.25 <= t < T['eject'][1] else 0,
          'rounds_vis': 1 if T['toPouch'][0] + 0.25 <= t < T['fwd'][0] + 0.03 else 0}
    Gw = D_ @ G0; Cin = Gw @ Matrix.Translation(CLIP_IN)
    # 클립 경로: 탄입대(손에 들림) -> 홈 3cm 위 -> 꽂기 -> (볼트 닫힘에 밀려) 위-오른쪽으로 튀어나감
    Wpouch = ST['R_POUCH']['W']; Cpouch = Wpouch @ REL['R_CLIP'].inverted() if False else Wpouch @ (REF0['clip'].inverted() @ ST['R_CLIP']['W']).inverted()
    Cabove = Gw @ Matrix.Translation(Vector(CLIP_IN) + Vector((0, 0, 3.0)))
    if t < T['toGuide'][0]: Cw = Cpouch
    elif t < T['insert'][0]: Cw = blend_W(Cpouch, Cabove, seg(t, *T['toGuide']), lift=0.04) @ Matrix.Scale(0.01, 4)
    elif t < T['eject'][0]: Cw = blend_W(Cabove, Cin, seg(t, *T['insert'])) @ Matrix.Scale(0.01, 4)
    else:
        x = seg(t, *T['eject']); Cw = Gw @ Matrix.Translation(Vector(CLIP_IN) + Vector((-6.0 * x, -2.0 * x, 12.0 * x - 6.0 * x * x))) @ Matrix.Rotation(math.radians(-70 * x), 4, 'Y')
    if t < T['toGuide'][0]: Cw = Cpouch
    st['Cw'] = Cw if Cw.to_scale().x < 0.5 else Cw   # 스케일 0.01 유지
    if t < T['toPouch'][0]: R = ('R_GRIP', 'R_BOLT', seg(t, *T['toBolt']), 3.0)
    elif t < T['toGuide'][0]: R = ('R_BOLT', 'R_POUCH', seg(t, *T['toPouch']), 4.0)
    elif t < T['toPush'][0]: R = ('R_CLIP', 'R_CLIP', 0, 0)
    elif t < T['toBolt2'][0]: R = ('R_CLIP', 'R_PUSH', seg(t, *T['toPush']), 1.0)
    elif t < T['toGrip'][0]: R = ('R_PUSH', 'R_BOLT', seg(t, *T['toBolt2']), 2.5)
    else: R = ('R_BOLT', 'R_GRIP', seg(t, *T['toGrip']), 2.0)
    st['R'] = R; return st
def view_ang(p):   # 카메라 공간 점 -> (가로°, 세로°)
    return math.degrees(math.atan2(-p.y, max(p.x, 1e-3))), math.degrees(math.atan2(p.z, max(p.x, 1e-3)))
shL = arm.matrix_world @ arm.pose.bones['Left arm'].head; shR = arm.matrix_world @ arm.pose.bones['Right arm'].head
best = None
for fw in (0, 3, 6, 9, 12):
    for sd in (0, 3, 6, 9):
        for up in (-12, -8, -4, 0, 4):
            for rl in (10, 18, 26):
                for pt in (-6, 0, 6):
                    for yw in (-8, 0, 8):
                        Dt = gun_delta(back=-fw, side=sd, up=up, pitch=pt, roll=rl, yaw=yw); F = frames({'D': Dt, 'theta': 0, 's': 0, 'push': 0})
                        wl = hand_world('L_RELOAD', F).translation; wr = hand_world('R_PUSH', F).translation
                        if (wl - shL).length * 100 > 37.5 or (wr - shR).length * 100 > 37.5: continue
                        g = F['gun'] @ Vector(CLIP_IN) + (F['gun'].to_3x3() @ Vector((0, 0, 3.0)))
                        hg, vg = view_ang(g); hw, vw = view_ang(wr)
                        v = abs(hg - 12) + abs(vg + OPT.get('guide_down', 4)) + max(0, abs(vw) - 24) + max(0, abs(hw) - 34) + max(0, vw + 4)   # 클립 홈: 오른쪽 12°, 아래 4°(2026-11-21: 아래 14°는 PIE 에서 약 -27°로 화면 아래 끝이라 낱발이 안 보였음) / 손: 화면 안, 가운데보다 아래
                        v += 2 * max(0, 22 - wr.length * 100) + 2 * max(0, 25 - g.length * 100)                           # 손·홈이 카메라에 너무 가깝지 않게
                        cost = v + 0.04 * (fw + sd + abs(up) + rl * 0.3 + abs(pt) * 0.3 + abs(yw) * 0.3)
                        if best is None or cost < best[0]: best = (cost, dict(back=-fw, side=sd, up=up, pitch=pt, roll=rl, yaw=yw), round(v, 2), [round(hg, 1), round(vg, 1), round(hw, 1), round(vw, 1), round(wr.length * 100, 1)])
RELOAD_D = OPT.get('reload_d') or (best[1] if best else dict(back=1.5, side=1.0, up=-9.0, pitch=6.0, roll=14.0, yaw=3.0))
OUT['reload_pose'] = {'delta': RELOAD_D, 'cost': best[2] if best else None, 'guide_hv_wrist_hv_dist': best[3] if best else None}
CLIPS = {'Idle': (tl_idle, 4.0), 'Fire': (tl_fire, 1.2), 'Reload': (tl_reload, 3.2)}
# blend_W 가 스케일을 버리므로 클립 행렬은 위에서 0.01 을 다시 곱함. Cpouch 는 손목 행렬 @ (클립<-손목) 이라 스케일 포함.
# ---------------------------------------------------------------- 포즈 적용(프레임)
PB = arm.pose.bones
for pb in PB: pb.rotation_mode = 'QUATERNION'
def set_rigid(name, Xw, Xw0, vis=1):
    M = Xw @ Xw0.inverted() @ REST[name]
    if not vis: M = M @ Matrix.Scale(0.001, 4)
    PB[name].matrix = M
def apply_state(st):
    F = frames(st)
    set_rigid('VM_Gun', F['gun'], REF0['gun']); bpy.context.view_layer.update()
    set_rigid('VM_Bolt', F['bolt'], REF0['bolt']); set_rigid('VM_Shroud', F['shroud'], REF0['shroud'])
    set_rigid('VM_Clip', F['clip'], REF0['clip'], st['clip_vis']); bpy.context.view_layer.update()
    set_rigid('VM_Rounds', F['rounds'], REF0['rounds'], st['rounds_vis'] and st['clip_vis'])
    a, b, x, lift = st['R']; Wr = blend_W(hand_world(a, F), hand_world(b, F), x, lift / 100.0); la, lb, lx = st.get('L', ('L_GRIP', 'L_GRIP', 0.0)); Wl = blend_W(hand_world(la, F), hand_world(lb, F), lx)
    for s, W in (('R', Wr), ('L', Wl)):
        l, r, _ = W.decompose(); E['T_' + s].location = l; E['T_' + s].rotation_quaternion = r; E['P_' + s].location = l + POLE[s]
    bpy.context.view_layer.update()
    for s, W in (('R', Wr), ('L', Wl)):   # IK 오차 보정
        L2.settle_wrist(arm, E, s, W.translation)
    L2.apply_fingers(arm, fax['R'], blend_f(ST[a]['fing'], ST[b]['fing'], x)); L2.apply_fingers(arm, fax['L'], blend_f(ST[la]['fing'], ST[lb]['fing'], lx)); bpy.context.view_layer.update()
    return F
def record():
    return {pb.name: arm.convert_space(pose_bone=pb, matrix=pb.matrix, from_space='POSE', to_space='LOCAL').copy() for pb in PB}
CONS = [c for pb in PB for c in pb.constraints]
def bake_clip(name, fn, dur):
    n = int(round(dur * FPS)); rec = []
    for c in CONS: c.mute = False
    for f in range(n + 1): apply_state(fn(f / FPS)); rec.append(record())
    for c in CONS: c.mute = True
    act = bpy.data.actions.new('FPVM_Kar98k_' + name); arm.animation_data_create(); arm.animation_data.action = act
    previous = {}
    for f, R in enumerate(rec):
        for pb in PB:
            L2.key_baked_pose(pb, R[pb.name], f + 1, previous)
    act.use_fake_user = True; return act, n
def shot(name, fn, t, views=('fp', 'side'), look=(0.12, -0.05, -0.12), scale=0.9):
    for c in CONS: c.mute = False
    apply_state(fn(t)); return L2.render_views(D + r'\Data\fpvm_k98_%s' % name, views=views, look=look, scale=scale)
for m in bpy.data.materials:
    m.diffuse_color = (0.85, 0.7, 0.62, 1) if 'Skin' in m.name else (0.25, 0.3, 0.55, 1) if 'Outfit' in m.name else (0.45, 0.32, 0.2, 1) if m.name == 'Material_001' else (0.75, 0.6, 0.25, 1) if m.name in ('Clip_Case', 'Clip_Projectile') else (0.35, 0.35, 0.37, 1)
if STAGE == 'roundclips':
    clips = {f'Loose{i}': build_timeline(tl_reload, G0, CLIP_IN, i, 1.04, 2.35, 3.2) for i in (1, 2, 3, 4)}
    export_animations(D, 'Kar98k', arm, E, clips, bake_clip, FPS)
    raise SystemExit(0)
if STAGE == 'dbg':
    for c in CONS: c.mute = False
    st = tl_idle(0.0); F = frames(st); apply_state(st)
    def cm(v): return [round(x * 100, 2) for x in v]
    OUT['dbg'] = {'ST_W_R': cm(ST['R_GRIP']['W'].translation), 'hand_world_R': cm(hand_world('R_GRIP', F).translation), 'T_R': cm(E['T_R'].location),
                  'wrist_R': cm(arm.matrix_world @ PB['Right wrist'].head), 'arm_mw': [list(r) for r in arm.matrix_world], 'D': [list(r) for r in st['D']],
                  'gun_bone': cm(arm.matrix_world @ PB['VM_Gun'].head), 'G0_t': cm(G0.translation), 'cons': [(c.name, c.mute, getattr(c, 'target', None) and c.target.name) for c in CONS]}
if STAGE == 'grip':   # 손 위치 확대(오른손 손잡이 / 왼손 앞받침)
    R_ = []
    for nm, pt in (('gripR', rc), ('gripL', lc)):
        st0 = tl_idle(0.0); R_ += shot(nm, tl_idle, 0.0, ('side', 'left', 'top', 'front'), look=tuple(pt), scale=0.22)
    OUT['renders'] = R_; OUT['gap_after_apply'] = {s_: L2.palm_gap(arm, body, s_, ax[s_], bvh_all) for s_ in 'RL'}
if STAGE == 'pose':
    OUT['renders'] = shot('pose', tl_idle, 0.0, ('fp', 'side', 'top', 'front'))
elif STAGE == 'close':   # 볼트 잡기 확대: 옵션 t(Fire 시간)
    kk = G0 @ Vector(KNOB); OUT['renders'] = shot('close', tl_fire, OPT.get('t', 0.32), ('side', 'top', 'back', 'front'), look=tuple(kk), scale=0.25)
elif STAGE in ('anim', 'export'):
    if STAGE == 'anim' or OPT.get('shots'):
        R = []
        for nm, fn, t in (('fire_kick', tl_fire, 0.04), ('fire_lift', tl_fire, 0.40), ('fire_back', tl_fire, 0.56), ('rel_pouch', tl_reload, 1.05), ('rel_guide', tl_reload, 1.62), ('rel_push', tl_reload, 2.30), ('rel_eject', tl_reload, 2.72)):
            R += shot(nm, fn, t)
        OUT['renders'] = R
    if STAGE == 'export':
        bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1.0   # FBX 가져오기가 장면 fps 를 24 로 바꾸므로 굽기 직전에 다시
        acts = {}
        for nm, (fn, dur) in CLIPS.items(): a, n = bake_clip(nm, fn, dur); acts[nm] = {'action': a.name, 'frames': n + 1}
        OUT['actions'] = acts
        for pb in PB:
            for c in list(pb.constraints): pb.constraints.remove(c)
        for e in list(E.values()): bpy.data.objects.remove(e)
        arm.animation_data.action = bpy.data.actions[acts['Idle']['action']]
        os.makedirs(D + r'\FBX\FPVM', exist_ok=True); fn = D + r'\FBX\FPVM\SK_FPVM_Kar98k.fbx'
        bpy.ops.object.select_all(action='DESELECT')
        for o in (arm, body, gun, bolt, shroud, clip, rounds, receiver_interior): o.select_set(True)
        for o in CA: o.select_set(True)   # 병과 캐릭터 7종 1인칭 팔
        bpy.context.view_layer.objects.active = arm
        bpy.ops.export_scene.fbx(filepath=fn, use_selection=True, object_types={'ARMATURE', 'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True, add_leaf_bones=False,
                                 bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
                                 mesh_smooth_type='FACE', path_mode='STRIP', armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X')
        OUT['fbx'] = fn; OUT['fps'] = FPS
        for _nm, _info in acts.items():   # 클립마다 따로(UE 에서 기존 스켈레톤에 애니만 다시 가져오기용)
            _a = bpy.data.actions[_info['action']]; arm.animation_data.action = _a; _s0, _s1 = _a.frame_range
            bpy.context.scene.frame_start = round(_s0); bpy.context.scene.frame_end = round(_s1)
            bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
            bpy.ops.export_scene.fbx(filepath=D + r'\FBX\FPVM\AS_FPVM_%s_%s.fbx' % ('Kar98k', _nm), use_selection=True, object_types={'ARMATURE'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                                     add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0,
                                     armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X')
OUT['mats'] = sorted({m.name for o in (body, gun, bolt, shroud, clip, rounds) for m in o.data.materials if m})
json.dump(OUT, open(D + r'\Data\fpvm_kar98k.json', 'w'), indent=1, default=str)
print('FPVM_OK', json.dumps({k: OUT.get(k) for k in ('gun_pos', 'R_grip', 'L_grip', 'R_bolt', 'R_clip', 'R_push', 'reload_pose', 'knob_lifted_native', 'sight_native', 'actions')})[:1500])
