"""blender -b --python fpvm_g43.py -- <pose|anim|export> [옵션 json] : Gewehr 43 1인칭 뷰모델(푸리나 팔 + 총 한 몸 스켈레탈)
 근거: Motion/DE_FP_MOTION_RESEARCH.md 2절. 사용자 지시: 탄창 교환 대신 '5발 클립 두 개를 연속으로' 장전.
   - 10발 탄창을 빼지 않고 5발 클립으로 채우도록 설계(Wikipedia G43), 볼트 캐리어에 홀드오픈 걸쇠(espeholt), 장전 손잡이는 왼쪽,
   - 클립 두 개로 10발(G41 선례), 장전 뒤 장전 손잡이를 살짝 당겼다 놓아 닫음(Forgotten Weapons G41(W)). Kar98k 와 달리 볼트가 닫히며 클립을 밀어내지 않으므로 빈 클립은 손으로 뽑아 버림.
 총 원본 좌표(cm): 총구 -Y, 위 +Z, 총의 오른쪽 -X. 총열 축 (x 0, z 5.67). 재질 하나(Gewehr43) -> 부품은 연결 성분 경계로 분리:
   캐리어(y 0.35~9.6, 위쪽) + 왼쪽 장전 손잡이(1.35, 9.18, 8.45) + 오른쪽 걸쇠 + 볼트(y 9.8~16.1) = VM_Carrier(뒤로 9.3cm 미끄럼)
 클립: 열린 캐리어 앞면(y 9.65) 바로 앞에 클립 판(y 9.2~9.6), 탄은 탄창 입구(y -1~8.6) 위.
 클립(30fps): Idle 4.0, Fire 0.30(반자동: 반동 + 캐리어 왕복), Reload 5.9(왼손 장전 손잡이로 열기 -> 클립1 꽂고 눌러 넣고 뽑아 버림 -> 클립2 같은 방식 -> 왼손으로 살짝 당겼다 놓아 닫기)
 결과 -> Data/fpvm_g43.json, FBX/FPVM/SK_FPVM_G43.fbx"""
import bpy, bmesh, sys, json, math, os
sys.path.insert(0, r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Scripts\Blender')
import numpy as np
from mathutils import Matrix, Vector, Quaternion
import fpvm_lib as L, fpvm_lib2 as L2
from fpvm_receiver_interior import add_existing_optic, add_receiver_interior, export_mesh_only
from fpvm_loose_round import build_timeline, export_animations, one_clip
A = sys.argv[sys.argv.index('--') + 1:]; STAGE = A[0]; OPT = json.loads(A[1]) if len(A) > 1 else {}
D = L.D; OUT = {'stage': STAGE}; FPS = 30; KEY = 'G43'
BORE = (0.0, 5.67); KNOB = (1.35, 9.18, 8.45); TRAVEL = OPT.get('travel', 9.3)
CLIP_IN = (0.0, 5.5, 8.45); PUSH = 5.6
R_CONTACT = OPT.get('r_contact', [-10.0, 28.5, 1.0])
GUN_POS = OPT.get('gun_pos', [29.0, -9.0, -11.2]); GUN_ROT = OPT.get('gun_rot', [2.5, 4.0, -3.0]); YL = OPT.get('yL', -4.0)   # 2026-11-21: 오른손목이 어깨에서 17cm 이상, 왼손이 탄창 가운데 아래. 예전 18.5
CLAV = {'L': [-10.73, 9.89, -16.11], 'R': [-17.46, -9.78, -17.09]}; REACH = OPT.get('reach', 37.0)
POLE = {'R': Vector((-0.12, -0.10, -0.15)), 'L': Vector((-0.10, 0.12, -0.15))}
arm, body, info = L.load_arms('a1', 0); OUT['arms'] = info; arm.name = 'Armature'
OUT['clavicle_err_cm'] = L2.pose_clavicles(arm, CLAV)
OUT['sleeves_folded'] = L2.fold_sleeves(arm)   # 소매 날개 접기(손 가림 방지), 아래에서 휴식 자세로 굳힘
bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = body; body.select_set(True)
if body.data.shape_keys: body.shape_key_clear()
for mod in list(body.modifiers):
    if mod.type == 'ARMATURE': bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = arm; arm.select_set(True)
bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.armature_apply(selected=False); bpy.ops.object.mode_set(mode='OBJECT')
_m = body.modifiers.new('Armature', 'ARMATURE'); _m.object = arm
for _uv in list(body.data.uv_layers)[1:]: body.data.uv_layers.remove(_uv)   # 팔 메시 UV 1개만(무기 메시와 UV 채널 수를 맞춤: UE 합칠 때 무기 UV 가 어긋나던 문제)
gun = L.load_weapon('g43')
if GUN_POS[0] is None:
    sh0 = arm.matrix_world @ arm.pose.bones['Left arm'].head
    for px in np.arange(45.0, 10.0, -0.5):
        Gt = L.gun_native_to_cam([px, GUN_POS[1], GUN_POS[2]], *GUN_ROT); w = Gt @ Vector((0.0, YL, 2.0)) + Vector((-0.005, 0.03, -0.035))
        if (w - sh0).length * 100 <= REACH: GUN_POS[0] = float(px); break
OUT['gun_pos'] = GUN_POS[:]; OUT['gun_rot'] = GUN_ROT[:]
if 'yL' not in OPT:   # 왼손: 어깨에서 REACH 안에 닿는 가장 앞쪽 아래면(케이 98k: 탄창 바닥판 앞 / G43: 탄창 아래)
    _sh = arm.matrix_world @ arm.pose.bones['Left arm'].head; _G = L.gun_native_to_cam(GUN_POS, *GUN_ROT)
    for _y in [v * 0.5 for v in range(-20, 41)]:
        _w = _G @ Vector((BORE[0], _y, 1.0)) + Vector((-0.005, 0.03, -0.045))
        if (_w - _sh).length * 100 <= REACH: YL = _y; break
OUT['yL'] = YL
# ---- 연결 성분으로 캐리어 떼기
def split_comps(g, name, pred):
    bm = bmesh.new(); bm.from_mesh(g.data); bm.verts.ensure_lookup_table(); lab = [-1] * len(bm.verts); comps = []
    for v in bm.verts:
        if lab[v.index] >= 0: continue
        st = [v]; lab[v.index] = len(comps); idx = []
        while st:
            x = st.pop(); idx.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if lab[y.index] < 0: lab[y.index] = len(comps); st.append(y)
        comps.append(idx)
    co = np.array([v.co[:] for v in bm.verts]); take = set(); picked = []
    for ci, idx in enumerate(comps):
        P = co[idx]; lo, hi = P.min(0), P.max(0)
        if pred(lo, hi, len(idx)): take.add(ci); picked.append([lo.round(2).tolist(), hi.round(2).tolist()])
    bm.free(); vt = lambda f: lab[f.vertices[0]] in take
    return L.split_by(g, name, lambda m, c, _s=set(): False) if not take else _split_faces(g, name, take, lab), picked
def _split_faces(g, name, take, lab):
    bm = bmesh.new(); bm.from_mesh(g.data); bm.faces.ensure_lookup_table(); sel = [f for f in bm.faces if lab[f.verts[0].index] in take]; ids = set(f.index for f in sel)
    me2 = g.data.copy(); bm2 = bmesh.new(); bm2.from_mesh(me2); bm2.faces.ensure_lookup_table()
    bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in ids], context='FACES'); bm2.to_mesh(me2); bm2.free()
    bmesh.ops.delete(bm, geom=sel, context='FACES'); bm.to_mesh(g.data); bm.free()
    o = bpy.data.objects.new(name, me2); bpy.context.scene.collection.objects.link(o); o.matrix_world = g.matrix_world.copy(); return o, len(ids)
(carrier, ncar), picked = split_comps(gun, 'W_carrier', lambda lo, hi, n: (lo[1] >= 0.3 and hi[1] <= 9.7 and lo[2] >= 5.8 and hi[2] <= 9.1) or (lo[1] >= 9.8 and hi[1] <= 16.1 and lo[2] >= 7.0 and hi[2] <= 7.7))
OUT['carrier'] = {'faces': ncar, 'parts': picked}
clip = L.load_weapon('mauser_clip')
for m in clip.data.materials:
    if m: m.name = {'Material': 'Clip_Steel', '6.5': 'Clip_Projectile', 'case': 'Clip_Case'}.get(m.name.split('.')[0] if m.name.startswith('Material') else m.name, m.name)
rounds, nr = L.split_by(clip, 'W_rounds', lambda m, c: m in ('Clip_Case', 'Clip_Projectile'))
G0 = L.gun_native_to_cam(GUN_POS, *GUN_ROT); C0 = G0 @ Matrix.Translation(CLIP_IN)
for o in (gun, carrier): o.matrix_world = G0
for o in (clip, rounds): o.matrix_world = C0
bpy.context.view_layer.update()
def nat(p, M=None): return (M or G0) @ Vector(p)
def dirn(d, M=None): return ((M or G0).to_3x3() @ Vector(d)).normalized()
def ray(bvh, o_native, d_native, M=None):
    M = M or G0; o = M @ Vector(o_native); d = (M.to_3x3() @ Vector(d_native)).normalized(); return bvh.ray_cast(o, d, 2.0)[0]
bvh_all = L2.bvh_of([gun, carrier])
# ---- 손 상태
E = L2.setup_ik(arm); ax = {s: L.hand_axes(arm, s) for s in 'LR'}; fax = {s: L.finger_axes(arm, s, ax[s]) for s in 'LR'}
def solve_place(s, contact, f, p, along=0.45, off=1.6): return L2.place_hand(arm, E, s, ax[s], contact, f, p, palm_off_cm=off, along=along, elbow_hint_m=contact + POLE[s])
def wrist_world(s):   # 실제 손목 뼈 머리 위치(IK 목표 위치를 쓰면 IK 가 덜 닿을 때 재생 시 수 cm 어긋났음) + 목표 회전
    bpy.context.view_layer.update(); return Matrix.LocRotScale((arm.matrix_world @ arm.pose.bones['%s wrist' % L2.SIDE[s]].head).copy(), E['T_' + s].rotation_quaternion.copy(), None)
ST = {}
_h = bvh_all.ray_cast(G0 @ Vector(R_CONTACT), dirn((1, 0, 0)), 2.0); rc = _h[0]; fR = dirn((0.15, -0.65, -0.75)); pR = (-_h[1]).normalized()   # 손바닥 = 닿는 면의 반대 법선(면에 평평하게)
OUT['R_grip'] = solve_place('R', rc, fR, pR); OUT['R_grip']['pole'] = L2.calib_pole(arm, E, 'R', E['T_R'].location.copy(), rc + POLE['R']); solve_place('R', rc, fR, pR)
OUT.setdefault('seat_cm', {})['R_GRIP'] = L2.seat_hand(arm, body, E, 'R', ax['R'], bvh_all)   # 손바닥을 총 표면에 붙임(떠 있던 문제)
ST['R_GRIP'] = {'ref': 'gun', 'W': wrist_world('R'), 'fing': L2.grip_fingers(arm, 'R', fax['R'], bvh_all, r_cm=0.55, limits={'Thumb': (20, 25, 25), 'default': (85, 100, 75)})}
_h = bvh_all.ray_cast(G0 @ Vector((BORE[0], YL, -15.0)), dirn((0, 0, 1)), 2.0); lc = _h[0]; fL = dirn((-1.0, -0.25, 0.15)); pL = (-_h[1]).normalized(); lc2 = lc - fL * 0.015
OUT['L_grip'] = solve_place('L', lc2, fL, pL); OUT['L_grip']['pole'] = L2.calib_pole(arm, E, 'L', E['T_L'].location.copy(), lc2 + POLE['L']); solve_place('L', lc2, fL, pL)
OUT.setdefault('seat_cm', {})['L_GRIP'] = L2.seat_hand(arm, body, E, 'L', ax['L'], bvh_all)   # 손바닥을 총 표면에 붙임(떠 있던 문제)
ST['L_GRIP'] = {'ref': 'gun', 'W': wrist_world('L'), 'fing': L2.grip_fingers(arm, 'L', fax['L'], bvh_all, r_cm=0.55, limits={'Thumb': (15, 20, 20), 'default': (85, 100, 75)})}
YLR = OPT.get('yLR', max(-2.0, YL))   # 장전 중 왼손: 탄창 바로 앞 아래(총을 받침)
lcr = ray(bvh_all, (BORE[0], YLR, -15.0), (0, 0, 1)) - fL * 0.015
OUT['L_reload'] = solve_place('L', lcr, fL, pL)
OUT.setdefault('seat_cm', {})['L_RELOAD'] = L2.seat_hand(arm, body, E, 'L', ax['L'], bvh_all)   # 손바닥을 총 표면에 붙임(떠 있던 문제)
ST['L_RELOAD'] = {'ref': 'gun', 'W': wrist_world('L'), 'fing': L2.grip_fingers(arm, 'L', fax['L'], bvh_all, r_cm=0.55, limits={'Thumb': (15, 20, 20), 'default': (85, 100, 75)})}
shR = arm.matrix_world @ arm.pose.bones['Right arm'].head; shL = arm.matrix_world @ arm.pose.bones['Left arm'].head
def fset(v, s='R'): return {b: a for f, vals in v.items() for b, a in zip(L.fbones(s, f), vals)}
PINCH = {'Thumb': (20, 30, 25), 'IndexFinger': (55, 65, 45), 'MiddleFinger': (70, 85, 60), 'RingFinger': (75, 90, 60), 'LittleFinger': (75, 90, 60)}
CLIP_F = fset({'Thumb': (15, 20, 15), 'IndexFinger': (35, 40, 30), 'MiddleFinger': (70, 85, 60), 'RingFinger': (75, 90, 60), 'LittleFinger': (80, 90, 60)})
PF = fset({'Thumb': (0, 5, 5), 'IndexFinger': (70, 90, 60), 'MiddleFinger': (75, 95, 60), 'RingFinger': (80, 95, 60), 'LittleFinger': (80, 95, 60)})
# 왼손 장전 손잡이(총의 왼쪽 +X): 엄지-검지로 집기
CHF = fset(PINCH, 'L'); K = nat(KNOB); H = L2.hand_local(arm, 'L', fax['L'], CHF); plL = ax['L']['p_local']; flL = ax['L']['f_local']
Wch, OUT['L_ch'] = L2.search_hand(H, 'pinch', K, bvh_all, shL, excl=(K, 0.016), prefer=[(plL, dirn((-1, 0, -0.3)), 0.6), (flL, dirn((-0.3, -1, 0)), 0.4)])
ST['L_CH'] = {'ref': 'carrier', 'W': Wch, 'fing': CHF}
bvh_gc = L2.bvh_of([gun, carrier, clip, rounds]); pl = ax['R']['p_local']; fl = ax['R']['f_local']
CT = nat((0.0, 3.9, 3.2), C0); H = L2.hand_local(arm, 'R', fax['R'], CLIP_F)
Wc, OUT['R_clip'] = L2.search_hand(H, 'pinch', CT, bvh_gc, shR, excl=(CT, 0.015), prefer=[(pl, dirn((1, 0, 0)), 0.4), (fl, dirn((0, -0.3, -1)), 0.4)])
ST['R_CLIP'] = {'ref': 'cliph', 'W': Wc, 'fing': CLIP_F}
target = nat((0.0, 2.6, 3.4 + 0.45), C0); H = L2.hand_local(arm, 'R', fax['R'], PF)
Wp2, OUT['R_push'] = L2.search_hand(H, 'thumb_tip', target, bvh_gc, shR, excl=(target, 0.012), prefer=[(pl, dirn((0.8, 0, -0.6)), 0.4), (fl, dirn((0.3, -1, -0.5)), 0.3)])
ST['R_PUSH'] = {'ref': 'rounds', 'W': Wp2, 'fing': PF}
Wpouch = Matrix.LocRotScale(Vector((0.02, -0.24, -0.40)), L.wrist_rot_for(ax['R'], Vector((0.6, 0.3, 0.2)), Vector((0.0, 0.3, 1.0))).to_quaternion(), None)
ST['R_POUCH'] = {'ref': 'cam', 'W': Wpouch, 'fing': CLIP_F}
# ---- 뼈
def bone_at(name, parent, head_native, M):
    h = M @ Vector(head_native); t = M @ (Vector(head_native) + Vector((0, -5.0, 0))); L.add_bone(arm, name, parent, h, t)
bone_at('VM_Gun', 'Hips', (0, 0, 0), G0); bone_at('VM_Carrier', 'VM_Gun', (0.0, 9.0, 7.5), G0)
bone_at('VM_Clip', 'VM_Gun', (0, 0, 0), C0); bone_at('VM_Rounds', 'VM_Clip', (0, 0, 0), C0)
for o, b in ((gun, 'VM_Gun'), (carrier, 'VM_Carrier'), (clip, 'VM_Clip'), (rounds, 'VM_Rounds')): L.bind_rigid(arm, o, b)
receiver_interior = add_receiver_interior(KEY, arm, G0)
if STAGE in ('meshfix', 'zf4'):
    carrier.data.materials.clear()
    carrier.data.materials.append(bpy.data.materials['Gewehr43'])
    meshes = (body, gun, carrier, clip, rounds, receiver_interior)
    suffix = 'Interior'
    if STAGE == 'zf4':
        meshes += (add_existing_optic('g43_zf4', arm, G0),)
        suffix = 'ZF4'
    export_mesh_only(D + r'\FBX\FPVM\SK_FPVM_G43_' + suffix + '.fbx', arm, meshes)
    raise SystemExit(0)
REST = {b.name: b.matrix_local.copy() for b in arm.data.bones}
# ---- 운동학
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def seg(t, t0, t1): return ease((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)
def lin(t, t0, t1): return min(max((t - t0) / (t1 - t0), 0.0), 1.0)
def gun_delta(back=0.0, up=0.0, pitch=0.0, roll=0.0, yaw=0.0, side=0.0):
    pv = G0 @ Vector((0.0, 40.0, 0.0))
    R = Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(-pitch), 4, 'Y') @ Matrix.Rotation(math.radians(roll), 4, 'X')
    return Matrix.Translation(Vector((-back, side, up)) / 100.0) @ Matrix.Translation(pv) @ R @ Matrix.Translation(-pv)
def frames(st):
    Gw = st['D'] @ G0; Cw = st.get('Cw') or (Gw @ Matrix.Translation(CLIP_IN))
    return {'gun': Gw, 'carrier': Gw @ Matrix.Translation((0, st['s'], 0)), 'clip': Cw, 'cliph': st.get('Ch') or Cw, 'rounds': Cw @ Matrix.Translation((0, 0, -st['push'])), 'cam': Matrix.Identity(4)}
REF0 = frames({'D': Matrix.Identity(4), 's': 0, 'push': 0})
REL = {k: REF0[v['ref']].inverted() @ v['W'] for k, v in ST.items()}
def hand_world(key, F): return F[ST[key]['ref']] @ REL[key]
def blend_W(Wa, Wb, x, lift=0.0):
    la, ra, _ = Wa.decompose(); lb, rb, _ = Wb.decompose(); l = la.lerp(lb, x) + Vector((0, 0, lift * math.sin(math.pi * x)))
    return Matrix.LocRotScale(l, ra.slerp(rb, x), None)
def blend_f(fa, fb, x): return {b: fa.get(b, 0.0) * (1 - x) + fb.get(b, 0.0) * x for b in set(fa) | set(fb)}
S01 = Matrix.Scale(0.01, 4)
def tl_idle(t):
    ph = 2 * math.pi * t / 4.0
    return {'D': gun_delta(up=0.25 * math.sin(ph), pitch=0.25 * math.sin(ph + 0.6), roll=0.15 * math.sin(ph * 0.5)), 's': 0, 'push': 0, 'R': ('R_GRIP', 'R_GRIP', 0, 0), 'clip_vis': 0, 'rounds_vis': 0}
def tl_fire(t):   # 반자동: 반동 + 캐리어 왕복(0.01~0.10초)
    k = seg(t, 0.0, 0.04) * (1 - seg(t, 0.04, 0.25)); s = TRAVEL * (lin(t, 0.01, 0.05) if t < 0.05 else 1 - lin(t, 0.05, 0.10))
    return {'D': gun_delta(back=2.0 * k, up=0.6 * k, pitch=2.5 * k), 's': s, 'push': 0, 'R': ('R_GRIP', 'R_GRIP', 0, 0), 'clip_vis': 0, 'rounds_vis': 0}
# 장전 시간표(초)
CY = [dict(pouch=(0.30, 0.80), vis=0.60, guide=(0.80, 1.30), insert=(1.30, 1.45), toPush=(1.45, 1.60), push=(1.60, 2.05), toClip=(2.05, 2.25), lift=(2.25, 2.45), toss=(2.45, 2.70)),
      dict(pouch=(2.45, 2.95), vis=2.80, guide=(2.95, 3.45), insert=(3.45, 3.60), toPush=(3.60, 3.75), push=(3.75, 4.20), toClip=(4.20, 4.40), lift=(4.40, 4.60), toss=(4.60, 4.85))]
REL_T = {'tilt': (0.0, 0.40, 5.30, 5.85), 'toCH': (0.10, 0.40), 'open': (0.40, 0.55), 'chOff': (0.55, 0.85), 'toCH2': (4.70, 4.98), 'nudge': (4.98, 5.08), 'close': (5.08, 5.15), 'chOff2': (5.18, 5.55), 'toGrip': (4.60, 5.05)}
def tl_reload(t):
    T = REL_T; c = seg(t, T['tilt'][0], T['tilt'][1]) * (1 - seg(t, T['tilt'][2], T['tilt'][3]))
    D_ = gun_delta(**{k: v * c for k, v in RELOAD_D.items()}); Gw = D_ @ G0
    s = TRAVEL * seg(t, *T['open']) if t < T['nudge'][0] else (TRAVEL + 0.5 * seg(t, *T['nudge']) if t < T['close'][0] else (TRAVEL + 0.5) * (1 - lin(t, *T['close'])))
    # 왼손: 손받침 -> 장전 손잡이(열기) -> 받침 -> 장전 손잡이(살짝 당겼다 놓기) -> 손받침
    if t < T['open'][1]: Lh = ('L_GRIP', 'L_CH', seg(t, *T['toCH']))
    elif t < T['toCH2'][0]: Lh = ('L_CH', 'L_RELOAD', seg(t, *T['chOff']))
    elif t < T['close'][1]: Lh = ('L_RELOAD', 'L_CH', seg(t, *T['toCH2']))
    else: Lh = ('L_CH', 'L_GRIP', seg(t, *T['chOff2']))
    st = {'D': D_, 's': s, 'L': Lh, 'push': 0.0, 'clip_vis': 0, 'rounds_vis': 0}
    cy = CY[0] if t < CY[1]['pouch'][0] + 0.25 else CY[1]
    Cin = Gw @ Matrix.Translation(CLIP_IN); Cabove = Gw @ Matrix.Translation(Vector(CLIP_IN) + Vector((0, 0, 3.0)))
    Cpouch = ST['R_POUCH']['W'] @ (REF0['clip'].inverted() @ ST['R_CLIP']['W']).inverted()
    def lifted(x): return Gw @ Matrix.Translation(Vector(CLIP_IN) + Vector((0, 0, 4.0 * x)))
    if t < cy['guide'][0]: Cw = Cpouch
    elif t < cy['insert'][0]: Cw = blend_W(Cpouch, Cabove, seg(t, *cy['guide']), lift=0.04) @ S01
    elif t < cy['insert'][1]: Cw = blend_W(Cabove, Cin, seg(t, *cy['insert'])) @ S01
    elif t < cy['lift'][0]: Cw = Cin
    elif t < cy['toss'][0]: Cw = lifted(seg(t, *cy['lift']))
    else:
        x = seg(t, *cy['toss']); Cw = lifted(1.0) @ Matrix.Translation(Vector((-10.0 * x, 3.0 * x, 8.0 * x - 10.0 * x * x))) @ Matrix.Rotation(math.radians(-120 * x), 4, 'Y')
    Ch = lifted(1.0) if t >= cy['toss'][0] else Cw   # 던진 뒤에는 손 기준을 던진 순간 위치로 고정
    st['Cw'] = Cw; st['Ch'] = Ch
    st['clip_vis'] = 1 if cy['vis'] <= t < cy['toss'][1] else 0
    st['push'] = PUSH * seg(t, *cy['push']); st['rounds_vis'] = 1 if cy['vis'] <= t < cy['push'][1] else 0
    # 오른손
    if t < CY[0]['pouch'][1] and t < CY[0]['guide'][0]: R = ('R_GRIP', 'R_POUCH', seg(t, *CY[0]['pouch']), 4.0)
    elif t < cy['toPush'][0] and t >= cy['guide'][0]: R = ('R_CLIP', 'R_CLIP', 0, 0)
    elif cy['toPush'][0] <= t < cy['toClip'][0]: R = ('R_CLIP', 'R_PUSH', seg(t, *cy['toPush']), 1.0)
    elif cy['toClip'][0] <= t < cy['toss'][0]: R = ('R_PUSH', 'R_CLIP', seg(t, *cy['toClip']), 1.0)
    elif cy is CY[0] and t >= CY[0]['toss'][0]: R = ('R_CLIP', 'R_POUCH', seg(t, *CY[1]['pouch']), 4.0)
    elif cy is CY[1] and t < CY[1]['guide'][0]: R = ('R_CLIP', 'R_POUCH', seg(t, *CY[1]['pouch']), 4.0)
    else: R = ('R_CLIP', 'R_GRIP', seg(t, *T['toGrip']), 3.0)
    st['R'] = R; return st
def view_ang(p): return math.degrees(math.atan2(-p.y, max(p.x, 1e-3))), math.degrees(math.atan2(p.z, max(p.x, 1e-3)))
best = None
for fw in (0, 3, 6, 9, 12):
    for sd in (0, 3, 6, 9):
        for up in (-12, -8, -4, 0, 4):
            for rl in (10, 18, 26):
                for pt in (-6, 0, 6):
                    for yw in (-8, 0, 8):
                        Dt = gun_delta(back=-fw, side=sd, up=up, pitch=pt, roll=rl, yaw=yw)
                        F = frames({'D': Dt, 's': TRAVEL, 'push': 0}); wl = hand_world('L_RELOAD', F).translation; wr = hand_world('R_PUSH', F).translation; wc = hand_world('L_CH', F).translation
                        if (wl - shL).length * 100 > 37.5 or (wr - shR).length * 100 > 37.5 or (wc - shL).length * 100 > 37.5: continue
                        g = F['gun'] @ Vector(CLIP_IN) + (F['gun'].to_3x3() @ Vector((0, 0, 3.0))); hg, vg = view_ang(g); hw, vw = view_ang(wr)
                        v = abs(hg - 12) + abs(vg + 14) + max(0, abs(vw) - 24) + max(0, abs(hw) - 34) + max(0, vw + 4) + 2 * max(0, 22 - wr.length * 100) + 2 * max(0, 25 - g.length * 100)
                        cost = v + 0.04 * (fw + sd + abs(up) + rl * 0.3 + abs(pt) * 0.3 + abs(yw) * 0.3)
                        if best is None or cost < best[0]: best = (cost, dict(back=-fw, side=sd, up=up, pitch=pt, roll=rl, yaw=yw), round(v, 2), [round(hg, 1), round(vg, 1), round(hw, 1), round(vw, 1)])
RELOAD_D = OPT.get('reload_d') or (best[1] if best else dict(back=-6, side=6, up=-4, pitch=0, roll=18, yaw=0))
OUT['reload_pose'] = {'delta': RELOAD_D, 'cost': best[2] if best else None, 'hv': best[3] if best else None}
CLIPS = {'Idle': (tl_idle, 4.0), 'Fire': (tl_fire, 0.30), 'Reload': (tl_reload, 5.9)}
# ---- 적용/굽기
PB = arm.pose.bones
for pb in PB: pb.rotation_mode = 'QUATERNION'
def set_rigid(name, Xw, Xw0, vis=1):
    M = Xw @ Xw0.inverted() @ REST[name]
    if not vis: M = M @ Matrix.Scale(0.001, 4)
    PB[name].matrix = M
def apply_state(st):
    F = frames(st)
    set_rigid('VM_Gun', F['gun'], REF0['gun']); bpy.context.view_layer.update()
    set_rigid('VM_Carrier', F['carrier'], REF0['carrier']); set_rigid('VM_Clip', F['clip'], REF0['clip'], st['clip_vis']); bpy.context.view_layer.update()
    set_rigid('VM_Rounds', F['rounds'], REF0['rounds'], st['rounds_vis'] and st['clip_vis'])
    a, b, x, lift = st['R']; Wr = blend_W(hand_world(a, F), hand_world(b, F), x, lift / 100.0)
    la, lb, lx = st.get('L', ('L_GRIP', 'L_GRIP', 0.0)); Wl = blend_W(hand_world(la, F), hand_world(lb, F), lx, 0.02)
    for s, W in (('R', Wr), ('L', Wl)):
        l, r, _ = W.decompose(); E['T_' + s].location = l; E['T_' + s].rotation_quaternion = r; E['P_' + s].location = l + POLE[s]
    bpy.context.view_layer.update()
    for s, W in (('R', Wr), ('L', Wl)):
        for _ in range(3):
            err = W.translation - (arm.matrix_world @ PB['%s wrist' % L2.SIDE[s]].head)
            if err.length < 2e-4: break
            E['T_' + s].location = E['T_' + s].location + err; bpy.context.view_layer.update()
    L2.apply_fingers(arm, fax['R'], blend_f(ST[a]['fing'], ST[b]['fing'], x)); L2.apply_fingers(arm, fax['L'], blend_f(ST[la]['fing'], ST[lb]['fing'], lx)); bpy.context.view_layer.update()
def record(): return {pb.name: arm.convert_space(pose_bone=pb, matrix=pb.matrix, from_space='POSE', to_space='LOCAL').copy() for pb in PB}
CONS = [c for pb in PB for c in pb.constraints]
def bake_clip(name, fn, dur):
    n = int(round(dur * FPS)); rec = []
    for c in CONS: c.mute = False
    for f in range(n + 1): apply_state(fn(f / FPS)); rec.append(record())
    for c in CONS: c.mute = True
    act = bpy.data.actions.new('FPVM_%s_%s' % (KEY, name)); arm.animation_data_create(); arm.animation_data.action = act
    for f, Rr in enumerate(rec):
        for pb in PB:
            pb.matrix_basis = Rr[pb.name]
            for path in ('location', 'rotation_quaternion', 'scale'): pb.keyframe_insert(path, frame=f + 1, group=pb.name)
    act.use_fake_user = True; return act, n
def shot(name, fn, t, views=('fp', 'side'), look=(0.12, -0.05, -0.12), scale=0.9):
    for c in CONS: c.mute = False
    apply_state(fn(t)); return L2.render_views(D + r'\Data\fpvm_g43_%s' % name, views=views, look=look, scale=scale)
for m in bpy.data.materials:
    m.diffuse_color = (0.85, 0.7, 0.62, 1) if 'Skin' in m.name else (0.25, 0.3, 0.55, 1) if 'Outfit' in m.name else (0.75, 0.6, 0.25, 1) if m.name in ('Clip_Case', 'Clip_Projectile') else (0.45, 0.33, 0.22, 1)
carrier.data.materials.clear(); cm = bpy.data.materials.get('Gewehr43')
if cm: carrier.data.materials.append(cm)
if STAGE == 'roundclips':
    clips = {f'Loose{i}': build_timeline(tl_reload, G0, CLIP_IN, i, .80, 4.7, 5.9) for i in (1, 2, 3, 4, 6, 7, 8, 9)}
    clips['Clip5'] = one_clip(tl_reload)
    export_animations(D, 'G43', arm, E, clips, bake_clip, FPS)
    raise SystemExit(0)
if STAGE == 'grip':   # 손 위치 확대(오른손 손잡이 / 왼손 앞받침)
    R_ = []
    for nm, pt in (('gripR', rc), ('gripL', lc)):
        st0 = tl_idle(0.0); R_ += shot(nm, tl_idle, 0.0, ('side', 'left', 'top', 'front'), look=tuple(pt), scale=0.22)
    OUT['renders'] = R_; OUT['gap_after_apply'] = {s_: L2.palm_gap(arm, body, s_, ax[s_], bvh_all) for s_ in 'RL'}
if STAGE == 'pose':
    OUT['renders'] = shot('pose', tl_idle, 0.0, ('fp', 'side', 'top', 'front'))
elif STAGE == 'close':   # 왼손 장전 손잡이 확대(왼쪽에서): 열기 / 닫기 직전
    R = []
    for nm, t in (('ch_open', 0.50), ('ch_nudge', 5.05), ('ch_off', 0.9)):
        st = tl_reload(t); F = frames(st); kk = F['gun'] @ Vector(KNOB); R += shot(nm, tl_reload, t, ('left', 'top'), look=tuple(kk), scale=0.35)
    OUT['renders'] = R
elif STAGE in ('anim', 'export'):
    if STAGE == 'anim' or OPT.get('shots'):
        R = []
        for nm, fn, t in (('fire', tl_fire, 0.05), ('rl_open', tl_reload, 0.55), ('rl_pouch', tl_reload, 0.80), ('rl_guide1', tl_reload, 1.40), ('rl_push1', tl_reload, 2.00), ('rl_lift1', tl_reload, 2.45),
                          ('rl_toss1', tl_reload, 2.62), ('rl_push2', tl_reload, 4.10), ('rl_close', tl_reload, 5.10), ('rl_end', tl_reload, 5.6)):
            R += shot(nm, fn, t)
        OUT['renders'] = R
    if STAGE == 'export':
        bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1.0
        acts = {}
        for nm, (fn, dur) in CLIPS.items(): a, n = bake_clip(nm, fn, dur); acts[nm] = {'action': a.name, 'frames': n + 1}
        OUT['actions'] = acts
        for pb in PB:
            for c in list(pb.constraints): pb.constraints.remove(c)
        for e in list(E.values()): bpy.data.objects.remove(e)
        arm.animation_data.action = bpy.data.actions[acts['Idle']['action']]
        os.makedirs(D + r'\FBX\FPVM', exist_ok=True); fn = D + r'\FBX\FPVM\SK_FPVM_%s.fbx' % KEY
        bpy.ops.object.select_all(action='DESELECT')
        for o in (arm, body, gun, carrier, clip, rounds, receiver_interior): o.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.export_scene.fbx(filepath=fn, use_selection=True, object_types={'ARMATURE', 'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True, add_leaf_bones=False,
                                 bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
                                 mesh_smooth_type='FACE', path_mode='STRIP', armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X')
        OUT['fbx'] = fn; OUT['fps'] = FPS
        for _nm, _info in acts.items():   # 클립마다 따로(UE 에서 기존 스켈레톤에 애니만 다시 가져오기용)
            _a = bpy.data.actions[_info['action']]; arm.animation_data.action = _a; _s0, _s1 = _a.frame_range
            bpy.context.scene.frame_start = round(_s0); bpy.context.scene.frame_end = round(_s1)
            bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
            bpy.ops.export_scene.fbx(filepath=D + r'\FBX\FPVM\AS_FPVM_%s_%s.fbx' % ('G43', _nm), use_selection=True, object_types={'ARMATURE'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                                     add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0,
                                     armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X')
OUT['mats'] = sorted({m.name for o in (body, gun, carrier, clip, rounds) for m in o.data.materials if m})
json.dump(OUT, open(D + r'\Data\fpvm_g43.json', 'w'), indent=1, default=str)
print('FPVM_OK', json.dumps({k: OUT.get(k) for k in ('gun_pos', 'carrier', 'R_grip', 'L_grip', 'L_ch', 'R_clip', 'R_push', 'reload_pose', 'actions')})[:1500])
