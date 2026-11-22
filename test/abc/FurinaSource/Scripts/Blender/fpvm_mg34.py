"""blender -b --python fpvm_mg34.py -- mg34 <pose|grip|anim|export> : MG34 1인칭(들고 쏘기만, 2026-11-22 사용자 지정: 설치 사격 없이 돌격소총처럼)
 근거: Motion/DE_FP_MOTION_RESEARCH.md 11절(MIS Special Series No.14 1943, TM E9-206A, bergflak 멜빵 허리 사격).
   오른손 = 권총 손잡이(검지 방아쇠), 왼손 = 리시버 앞 총열 덮개 아래 받침(허리 사격). 장전 손잡이 = 오른쪽, 사격 때 움직이지 않음(비왕복).
   재장전 = 50발 탄띠 드럼(Gurttrommel 34) 교체: 드럼 뒤를 앞 고리 축으로 바깥으로 돌려 빼고 -> 새 드럼 앞 끝을 고리에 걸고 뒤를 돌려 끼움
     -> 오른손이 손잡이를 놓고 오른쪽 장전 손잡이를 끝까지 당겼다가 앞으로 -> 손잡이로.
 모델: 정리본 SM_DE_mg34(총구 -Y, 위 +Z, 총의 오른쪽 -X). 드럼('mg 34 mag')과 급탄판 위 짧은 탄띠('p line', 탄)를 W_mag 로 함께.
 출력: FBX/FPVM/SK_FPVM_MG34.fbx + AS_FPVM_MG34_<Idle|Fire|Reload>.fbx, Data/fpvm_mg34.json"""
import bpy, bmesh, sys, json, math, os
sys.path.insert(0, r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Scripts\Blender')
import numpy as np
from mathutils import Matrix, Vector, Quaternion
import fpvm_lib as L, fpvm_lib2 as L2
A = sys.argv[sys.argv.index('--') + 1:]; WK = A[0]; STAGE = A[1] if len(A) > 1 else 'pose'; OPT = json.loads(A[2]) if len(A) > 2 else {}
D = L.D; FPS = 30; KEY = WK.upper(); OUT = {'key': WK, 'stage': STAGE}
# 무기별 수치(정리 후 원본 cm: 총구 -Y, 위 +Z, 총의 오른쪽 -X)
SPEC = {'mg34': dict(grip=(-2.4, 27.5, -4.5), fR=(0.15, -0.74, -0.67), xc=-2.9, bore_z=2.8, ch_box=((-11.6, 21.8, -0.8), (-4.4, 24.4, 2.3)), travel=9.0, rpm=900, cap=50,
                     rear_y=4.5, front_y=(-49.4, -47.4), recv_end=40.0, hold='guard', guard_ahead=-8.4, gun_pos=[36.0, -8.0, -13.0], gun_rot=[4.0, 0.0, -8.0],   # 배치: fpvm_place_search.py(두 손 닿고 드럼·리시버·왼손이 화면 안)
                     fire_len=60.0 / 900,
                     mag_mats=('mg 34 mag', 'p line', '7.92х57 l'), drum_hook=(0.8, 9.8, 1.7), cover_box=((-6.4, 9.8, 4.0), (1.5, 24.0, 8.0)), cover_hinge=(-2.9, 10.0, 5.2), cover_open=85.0)}[WK]
CLAV = {'L': [-10.73, 9.89, -16.11], 'R': [-17.46, -9.78, -17.09]}; REACH = OPT.get('reach', 37.5)
POLE = {'R': Vector((-0.10, -0.12, -0.18)), 'L': Vector((-0.08, 0.14, -0.20))}
# ---- 팔
arm, body, info = L.load_arms('a1', 0); OUT['arms'] = info; arm.name = 'Armature'
CA = L.class_arm_objects(arm)   # 병과 캐릭터 7종 1인칭 팔(같은 팔 뼈대, 재질 CA<Key>_*): 내보낼 때 함께 선택
OUT['clavicle_err_cm'] = L2.pose_clavicles(arm, CLAV); OUT['sleeves'] = L2.fold_sleeves(arm)
L.bake_arms_rest(arm, [body] + CA)   # 푸리나 팔 + 병과 팔 모두 같은 휴식 자세로(2026-11-22)
for _uv in list(body.data.uv_layers)[1:]: body.data.uv_layers.remove(_uv)
# ---- 총(정리) + 부품 분리
gun = L.load_weapon(WK)
def decimate(o, target):
    n = len(o.data.polygons)
    if n <= target: return n
    md = o.modifiers.new('dec', 'DECIMATE'); md.ratio = target / n; bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.ops.object.modifier_apply(modifier=md.name); return len(o.data.polygons)
if SPEC.get('rot180'): gun.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
mats = [m.name if m else '' for m in gun.data.materials]
if SPEC.get('drop_mats'):
    bm = bmesh.new(); bm.from_mesh(gun.data); bmesh.ops.delete(bm, geom=[f for f in bm.faces if mats[f.material_index] in SPEC['drop_mats']], context='FACES'); bm.to_mesh(gun.data); bm.free()
def comps_of(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); lab = [-1] * len(bm.verts); comps = []
    for v in bm.verts:
        if lab[v.index] >= 0: continue
        st = [v]; lab[v.index] = len(comps); idx = []
        while st:
            x = st.pop(); idx.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if lab[y.index] < 0: lab[y.index] = len(comps); st.append(y)
        comps.append(idx)
    co = np.array([v.co[:] for v in bm.verts]); bm.free(); return lab, comps, co
def split_faces(o, name, face_ok):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table(); sel = [f for f in bm.faces if face_ok(f)]; ids = set(f.index for f in sel)
    me2 = o.data.copy(); bm2 = bmesh.new(); bm2.from_mesh(me2); bm2.faces.ensure_lookup_table()
    bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in ids], context='FACES'); bmesh.ops.delete(bm2, geom=[v for v in bm2.verts if not v.link_faces], context='VERTS'); bm2.to_mesh(me2); bm2.free()
    bmesh.ops.delete(bm, geom=sel, context='FACES'); bm.to_mesh(o.data); bm.free()
    p = bpy.data.objects.new(name, me2); bpy.context.scene.collection.objects.link(p); p.matrix_world = o.matrix_world.copy(); return p, len(ids)
lab, comps, co = comps_of(gun)
def comp_sel(pred):
    take = set(ci for ci, idx in enumerate(comps) if pred(co[idx].min(0), co[idx].max(0)))
    return lambda f: lab[f.verts[0].index] in take
# 개머리판 펴기(MP38): Stock_Steel 덩어리를 경첩 수직축 180°
if SPEC.get('unfold'):
    sx, sy = SPEC['unfold']; si = mats.index('Stock_Steel') if 'Stock_Steel' in mats else -1
    bm = bmesh.new(); bm.from_mesh(gun.data); vs = set(v for f in bm.faces if f.material_index == si for v in f.verts)
    R = Matrix.Translation((sx, sy, 0)) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Translation((-sx, -sy, 0))
    for v in vs: v.co = R @ v.co
    bm.to_mesh(gun.data); bm.free(); OUT['unfolded_verts'] = len(vs)
    lab, comps, co = comps_of(gun)
# 탄창
if SPEC.get('mag_mats'):   # MG34: 드럼 + 급탄판 위 짧은 탄띠(재질로)
    _mis = {mats.index(m) for m in SPEC['mag_mats'] if m in mats}
    mag, nmag = split_faces(gun, 'W_mag', lambda f, _m=_mis: f.material_index in _m)
elif SPEC.get('mag_mat'):
    mi = mats.index(SPEC['mag_mat']); zmax = SPEC.get('mag_zmax')
    vmi = {}   # 정점 -> 재질(이 재질을 쓰는 성분만)
    _bm = bmesh.new(); _bm.from_mesh(gun.data)
    for f in _bm.faces:
        for v in f.verts: vmi[v.index] = f.material_index
    _bm.free()
    cand = [ci for ci, idx in enumerate(comps) if vmi.get(idx[0]) == mi and (zmax is None or co[idx][:, 2].min() < zmax)]
    big = max(cand, key=lambda ci: len(comps[ci])); bl, bh = co[comps[big]].min(0), co[comps[big]].max(0)
    mag_take = set(ci for ci in cand if (co[comps[ci]].min(0) >= bl - 0.5).all() and (co[comps[ci]].max(0) <= bh + 0.5).all())   # 가장 큰 탄창 몸통 경계 안의 성분만
    mb = SPEC.get('mag_box')
    def mag_ok(f, _mi=mi, _t=mag_take):
        if f.material_index != _mi: return False
        if mb:   # 다른 부품과 정점이 붙어 있는 모델(MP38): 재질 + 탄창 경계 상자로
            c = f.calc_center_median(); return all(mb[0][i] <= c[i] <= mb[1][i] for i in range(3))
        return lab[f.verts[0].index] in _t
    mag, nmag = split_faces(gun, 'W_mag', mag_ok)
else:   # MP40: 원본 MP40.fbx 의 자체 탄창(de_mp40_mag.py 가 정리본 좌표로 옮겨 하우징 입구 가운데에 끼움). 예전 MP38 탄창은 하우징보다 1.2cm 뒤에 꽂혔음
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=os.path.join(D, 'FBX', 'Weapons', 'SM_DE_mp40_mag.fbx'))
    src = next(bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before and bpy.data.objects[k].type == 'MESH')
    for k in [k for k in bpy.data.objects.keys() if k not in before and bpy.data.objects[k].type != 'MESH']: bpy.data.objects.remove(bpy.data.objects[k])
    bpy.ops.object.select_all(action='DESELECT'); src.select_set(True); bpy.context.view_layer.objects.active = src; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    src.data.transform(Matrix.Scale(100, 4)); src.name = 'W_mag'; mag = src; nmag = len(src.data.polygons)
    if mag.data.materials and gun.data.materials: mag.data.materials[0] = gun.data.materials[0]   # 같은 MP40 재질(같은 텍스처 아틀라스)
OUT['mag_faces'] = nmag
lab, comps, co = comps_of(gun)
(lo_b, hi_b) = SPEC['ch_box']
ch, nch = split_faces(gun, 'W_handle', comp_sel(lambda lo, hi: all(lo[i] >= lo_b[i] and hi[i] <= hi_b[i] for i in range(3))))
OUT['handle_faces'] = nch
# 급탄 덮개(2026-11-22 고증: 드럼을 달 때 덮개를 열고 탄띠 앞 고리들을 급탄판에 놓은 뒤 닫음 - mg42.us 포럼, Athlon, MIS 1943)
CB = SPEC['cover_box']   # 덮개 전체(위에서 본 둥근 뒤끝 판 y 10~23.6, 리시버 윗면 z 4.7 위): 꼭짓점이 모두 영역 안인 면 + 영역 안 성분(리벳 등)
lab, comps, co = comps_of(gun)
_inbox = lambda p: all(CB[0][i] <= p[i] <= CB[1][i] for i in range(3))
_cin = set(ci for ci, idx in enumerate(comps) if all(CB[0][i] - 0.3 <= co[idx][:, i].min() and co[idx][:, i].max() <= CB[1][i] + 0.3 for i in range(3)))
cover, ncov = split_faces(gun, 'W_cover', lambda f: lab[f.verts[0].index] in _cin or all(_inbox(v.co) for v in f.verts)); OUT['cover_faces'] = ncov
_rest = np.array([v.co[:] for v in gun.data.vertices]); _r = _rest[(_rest[:, 1] > 10.5) & (_rest[:, 1] < 23.5) & (_rest[:, 0] > -6.0) & (_rest[:, 0] < 0.2)]; _cv = np.array([v.co[:] for v in cover.data.vertices])
_bmr = bmesh.new(); _bmr.from_mesh(gun.data); _hi = []
for _f in _bmr.faces:
    _c = np.array([v.co[:] for v in _f.verts])
    if (_c[:, 2] > 5.0).any() and ((_c[:, 1] > 10.5) & (_c[:, 1] < 23.5)).any() and ((_c[:, 0] > -6.0) & (_c[:, 0] < 0.2)).any(): _hi.append([_c.min(0).round(1).tolist(), _c.max(0).round(1).tolist()])
_bmr.free(); OUT['cover_rest_faces'] = _hi[:12]; OUT['cover_rest_n'] = len(_hi)
OUT['cover_check'] = {'rest_zmax': round(float(_r[:, 2].max()), 2) if len(_r) else None, 'cover_y': [round(float(_cv[:, 1].min()), 2), round(float(_cv[:, 1].max()), 2)], 'cover_z': [round(float(_cv[:, 2].min()), 2), round(float(_cv[:, 2].max()), 2)]}
OUT['tris'] = {o.name: decimate(o, t) for o, t in ((gun, 70000), (mag, 9000), (ch, 4000), (cover, 6000))}
# 조준선(앞 가늠쇠 = 총구 쪽 가운데 줄 최고점, 뒤 가늠자 = 같은 높이(조준선 ∥ 총열))
P = np.array([v.co[:] for v in gun.data.vertices]); f0, f1 = SPEC['front_y']
cen = P[(P[:, 1] >= f0) & (P[:, 1] <= f1) & (np.abs(P[:, 0] - SPEC['xc']) < 0.15)]
front = [SPEC['xc'], float(cen[cen[:, 2].argmax(), 1]), float(cen[:, 2].max())]; rear = [SPEC['xc'], SPEC['rear_y'], front[2]]
OUT['sight'] = {'front': front, 'rear': rear}
# ---- 배치(2026-11-21 수정): 왼손 받침 자리(MP38/MP40 = 탄창 하우징, StG44 = 탄창 앞 총열 덮개)가 왼팔 길이(37.5cm) 안에 오도록 총을 앞뒤로 맞춤.
#  이전엔 오른손 기준(손잡이 = 눈 앞 4cm)이라 왼손이 닿지 않아 하우징 뒤 좁은 틈을 위에서 잡았고 화면에 손이 안 보였음. 조준선은 눈 아래 5cm(허리 사격 자세).
gx, gy, gz = OPT.get('grip', SPEC['grip']); GUN_ROT = OPT.get('gun_rot', SPEC.get('gun_rot', [2.5, 4.0, -3.0]))
_my = [v.co.y for v in mag.data.vertices]; my0, my1 = min(_my), max(_my); myc = 0.5 * (my0 + my1); OUT['mag_y'] = [round(my0, 2), round(my1, 2)]
HOLD = SPEC.get('hold', 'housing')
if HOLD == 'housing':
    band = P[(P[:, 1] >= my0 + 0.5) & (P[:, 1] <= my1 - 0.5) & (np.abs(P[:, 0] - SPEC['xc']) < 2.5)]
    HB = float(band[:, 2].min()); HOLD_N = Vector((SPEC['xc'], myc + OPT.get('hold_dy', SPEC.get('hold_dy', 0.0)), HB + OPT.get('hold_dz', SPEC.get('hold_dz', 3.0))))   # 하우징 아래쪽(MP38 하우징이 더 짧음); OUT['housing_bottom'] = round(HB, 2)
else:
    HOLD_N = Vector((SPEC['xc'], my0 - OPT.get('guard_ahead', SPEC.get('guard_ahead', 5.0)), SPEC['bore_z'] - 3.0))
sh = arm.matrix_world @ arm.pose.bones['Left arm'].head
def _G(x): return L.gun_native_to_cam([x, -9.0, -OPT.get('sight_drop', 5.0) - front[2]], *GUN_ROT)
gxp = OPT.get('gun_x', gy + 14.0)
if 'gun_x' not in OPT:
    while gxp > gy - 30 and ((_G(gxp) @ HOLD_N) - sh).length * 100 > REACH + OPT.get('reach_slack', 1.0): gxp -= 0.5
GUN_POS = OPT.get('gun_pos', SPEC.get('gun_pos') or [round(gxp, 2), -9.0, round(-OPT.get('sight_drop', 5.0) - front[2], 2)]); OUT['gun_pos'] = GUN_POS; OUT['hold'] = [HOLD, [round(c, 2) for c in HOLD_N]]
G0 = L.gun_native_to_cam(GUN_POS, *GUN_ROT)
for o in (gun, mag, ch, cover): o.matrix_world = G0
bpy.context.view_layer.update()
def dirn(d, M=None): return ((M or G0).to_3x3() @ Vector(d)).normalized()
bvh_all = L2.bvh_of([gun, mag, ch, cover]); bvh_gun = L2.bvh_of([gun, ch, cover])
E = L2.setup_ik(arm); ax = {s: L.hand_axes(arm, s) for s in 'LR'}; fax = {s: L.finger_axes(arm, s, ax[s]) for s in 'LR'}
def solve_place(s, contact, f, p, along=0.45, off=1.6): return L2.place_hand(arm, E, s, ax[s], contact, f, p, palm_off_cm=off, along=along, elbow_hint_m=contact + POLE[s])
def wrist_world(s):
    bpy.context.view_layer.update(); return Matrix.LocRotScale((arm.matrix_world @ arm.pose.bones['%s wrist' % L2.SIDE[s]].head).copy(), E['T_' + s].rotation_quaternion.copy(), None)
def ray(bvh, o_native, d_native):
    h = bvh.ray_cast(G0 @ Vector(o_native), dirn(d_native), 2.0); return h[0], h[1]
ST = {}
# 오른손: 권총손잡이 오른쪽 면, 손가락 앞-아래로 감쌈
rc, rn = ray(bvh_gun, (gx - 10.0, gy, gz), (1, 0, 0)); assert rc is not None, 'grip ray miss'
fR = dirn(tuple(OPT.get('fR', SPEC.get('fR', (0.15, -0.45, -0.88))))); pR = (-rn).normalized()
OUT['R_grip'] = solve_place('R', rc, fR, pR); OUT['R_grip']['pole'] = L2.calib_pole(arm, E, 'R', E['T_R'].location.copy(), rc + POLE['R']); solve_place('R', rc, fR, pR)
OUT.setdefault('seat', {})['R'] = L2.seat_hand(arm, body, E, 'R', ax['R'], bvh_gun)
import fpvm_grip; _trig, OUT['trigger'] = fpvm_grip.trigger_target(arm, 'R', bvh_gun, G0)   # 검지 = 방아쇠울 안 방아쇠 앞면(2026-11-22)
ST['R_GRIP'] = {'ref': 'gun', 'W': wrist_world('R'), 'fing': L2.grip_fingers(arm, 'R', fax['R'], bvh_gun, r_cm=0.55, limits={'Thumb': (20, 25, 25), 'default': (85, 100, 75)}, targets={'IndexFinger': (_trig[0], 1.0, _trig[1])} if _trig is not None else None)}
OUT['R_grip_fingers'] = fpvm_grip.LAST.get('R')
# 왼손 받침. MP38/MP40: 탄창 하우징을 왼쪽에서 감쌈(당시 교범: 탄창 자체를 쥐면 급탄 불량 -> 하우징을 쥘 것). StG44: 탄창 앞 총열 덮개 아래를 받침.
sh = arm.matrix_world @ arm.pose.bones['Left arm'].head; plL = ax['L']['p_local']; flL = ax['L']['f_local']
WRAP0 = {'Thumb': (25, 30, 25), 'IndexFinger': (45, 55, 40), 'MiddleFinger': (50, 60, 45), 'RingFinger': (55, 65, 45), 'LittleFinger': (55, 65, 45)}
if HOLD == 'housing':
    hit = None
    for dz in (0.0, 0.5, -0.5, 1.0, -1.0, 1.5, 2.0):   # 하우징 옆벽(감쇄된 모델은 구멍이 있을 수 있어 둘레를 더듬음)
        for dy in (0.0, 0.8, -0.8, 1.5, -1.5):
            hit, nr = ray(bvh_gun, (SPEC['xc'] + 15.0, HOLD_N.y + dy, HOLD_N.z + dz), (-1, 0, 0))
            if hit is not None: OUT['hold_ray'] = [dy, dz]; break
        if hit is not None: break
    assert hit is not None, 'housing ray miss'
    Hh = L2.hand_local(arm, 'L', fax['L'], {b_: a_ for f_, vals in WRAP0.items() for b_, a_ in zip(L.fbones('L', f_), vals)})
    WL, OUT['L_hold'] = L2.search_hand(Hh, 'palm', hit, bvh_all, sh, reach_cm=REACH + 1.0, excl=(hit, 0.03),
                                      prefer=[(plL, dirn((-1, 0, 0)), 0.7), (flL, dirn((-0.2, -1.0, -0.5)), 0.4)])
    l_, r_, _ = WL.decompose(); E['T_L'].location = l_; E['T_L'].rotation_quaternion = r_; E['P_L'].location = l_ + POLE['L']; bpy.context.view_layer.update()
    for _ in range(12):   # IK 목표 보정 3번으론 손목이 1.5~2.5cm 덜 닿았음(판처슈렉, 2026-11-22)
        err = l_ - (arm.matrix_world @ arm.pose.bones['Left wrist'].head)
        if err.length < 2e-4: break
        E['T_L'].location = E['T_L'].location + err; bpy.context.view_layer.update()
    OUT['L_hold']['wrist_err_cm'] = round((l_ - (arm.matrix_world @ arm.pose.bones['Left wrist'].head)).length * 100, 2)
    OUT['seat'] = OUT.get('seat', {}); OUT['seat']['L'] = L2.seat_hand(arm, body, E, 'L', ax['L'], bvh_gun); lc = hit
else:
    hit, nr = ray(bvh_gun, (HOLD_N.x, HOLD_N.y, -25.0), (0, 0, 1)); assert hit is not None, 'guard ray miss'
    fL = dirn((-1.0, -0.25, 0.15)); pL = (-nr).normalized(); lc2 = hit - fL * OPT.get('guard_shift', 0.012); lc = hit
    OUT['L_grip'] = solve_place('L', lc2, fL, pL); OUT['L_grip']['pole'] = L2.calib_pole(arm, E, 'L', E['T_L'].location.copy(), lc2 + POLE['L']); solve_place('L', lc2, fL, pL)
    OUT['seat']['L'] = L2.seat_hand(arm, body, E, 'L', ax['L'], bvh_gun)
OUT['L_reach_cm'] = round(((arm.matrix_world @ arm.pose.bones['Left wrist'].head) - sh).length * 100, 1)
ST['L_GRIP'] = {'ref': 'gun', 'W': wrist_world('L'), 'fing': L2.grip_fingers(arm, 'L', fax['L'], bvh_gun, r_cm=0.55, limits={'Thumb': (25, 30, 30), 'default': (85, 100, 75)})}
# (2026-11-22) 예전 '둘째·셋째 마디 최소 35/30°' 보정은 뺌: 피부 기준 풀이(fpvm_grip)가 덮개를 직접 감쌈
shL = sh; shR = arm.matrix_world @ arm.pose.bones['Right arm'].head
def fset(v, s): return {b: a for f, vals in v.items() for b, a in zip(L.fbones(s, f), vals)}
PINCH = {'Thumb': (20, 30, 25), 'IndexFinger': (55, 65, 45), 'MiddleFinger': (70, 85, 60), 'RingFinger': (75, 90, 60), 'LittleFinger': (75, 90, 60)}
WRAP = {'Thumb': (25, 30, 25), 'IndexFinger': (45, 55, 40), 'MiddleFinger': (50, 60, 45), 'RingFinger': (55, 65, 45), 'LittleFinger': (55, 65, 45)}
plL = ax['L']['p_local']; flL = ax['L']['f_local']
# 왼손 드럼 쥐기: 드럼 바깥(왼쪽 +X) 면 가운데를 손바닥으로, 손가락은 위로 감쌈 — 드럼 기준
_mv = np.array([v.co[:] for v in mag.data.vertices if v.co.x > 0.5]); DRUM_C = Vector(tuple((_mv.min(0) + _mv.max(0)) / 2)); DRUM_X = float(_mv[:, 0].max())
mz = [v.co.z for v in mag.data.vertices]; mzc = DRUM_C.z
mt = G0 @ Vector((DRUM_X, DRUM_C.y, DRUM_C.z)); H = L2.hand_local(arm, 'L', fax['L'], fset(WRAP, 'L'))
Wm_, OUT['L_mag'] = L2.search_hand(H, 'palm', mt, bvh_all, shL, reach_cm=100, excl=(mt, 0.03), prefer=[(plL, dirn((-1, 0, 0)), 0.6), (flL, dirn((0, -0.3, 1)), 0.4)])
ST['L_MAG'] = {'ref': 'mag', 'W': Wm_, 'fing': fset(WRAP, 'L')}
# 오른손 장전 손잡이 집기(총의 오른쪽 -X) — 손잡이 기준
plR = ax['R']['p_local']; flR = ax['R']['f_local']
hc = [v.co for v in ch.data.vertices]; kn = G0 @ (sum(hc, Vector()) / len(hc)); H = L2.hand_local(arm, 'R', fax['R'], fset(PINCH, 'R'))
Wch, OUT['R_ch'] = L2.search_hand(H, 'pinch', kn, bvh_all, shR, reach_cm=100, excl=(kn, 0.016), prefer=[(plR, dirn((1, 0, -0.2)), 0.6), (flR, dirn((0.2, -1, 0)), 0.4)])
ST['R_CH'] = {'ref': 'handle', 'W': Wch, 'fing': fset(PINCH, 'R')}
ct = G0 @ Vector((SPEC['xc'], CB[1][1] - 1.0, CB[1][2] - 1.5)); H = L2.hand_local(arm, 'L', fax['L'], fset(PINCH, 'L'))
Wcv, OUT['L_cover'] = L2.search_hand(H, 'pinch', ct, bvh_all, shL, reach_cm=100, excl=(ct, 0.016), prefer=[(plL, dirn((0, 0.3, -1)), 0.6), (flL, dirn((-0.3, 0, -1)), 0.4)])
ST['L_COVER'] = {'ref': 'cover', 'W': Wcv, 'fing': fset(PINCH, 'L')}
# 영상(MG34 reload, 사용자 제공 녹화 60프레임): 오른손이 손잡이를 놓고 덮개 '뒤끝 멈치'를 눌러 열고(앞 경첩, 거의 세움), 왼손이 탄띠를 급탄판에 놓고, 오른손이 위에서 덮개를 눌러 닫은 뒤 오른쪽 장전 손잡이
H = L2.hand_local(arm, 'R', fax['R'], fset(PINCH, 'R'))
Wrc, OUT['R_cover'] = L2.search_hand(H, 'pinch', ct, bvh_all, shR, reach_cm=100, excl=(ct, 0.016), prefer=[(plR, dirn((0, 0.3, -1)), 0.6), (flR, dirn((0.3, -0.5, -1)), 0.4)])
ST['R_COVER'] = {'ref': 'cover', 'W': Wrc, 'fing': fset(PINCH, 'R')}
tt = G0 @ Vector((1.6, 15.0, 4.6)); H = L2.hand_local(arm, 'L', fax['L'], fset(PINCH, 'L'))   # 급탄판 왼쪽 위(탄띠 첫 탄을 놓고 오른쪽으로 당김)
Wtr, OUT['L_tray'] = L2.search_hand(H, 'pinch', tt, bvh_all, shL, reach_cm=100, excl=(tt, 0.016), prefer=[(plL, dirn((0, 0, -1)), 0.6), (flL, dirn((-1, 0, -0.3)), 0.4)])
ST['L_TRAY'] = {'ref': 'gun', 'W': Wtr, 'fing': fset(PINCH, 'L')}
Wpouch = Matrix.LocRotScale(Vector((0.05, 0.22, -0.42)), L.wrist_rot_for(ax['L'], Vector((0.6, -0.3, 0.2)), Vector((0.0, -0.3, 1.0))).to_quaternion(), None)
ST['L_POUCH'] = {'ref': 'cam', 'W': Wpouch, 'fing': fset(WRAP, 'L')}
# ---- 뼈
def bone_at(name, parent, head_native):
    h = G0 @ Vector(head_native); t = G0 @ (Vector(head_native) + Vector((0, -5.0, 0))); L.add_bone(arm, name, parent, h, t)
bone_at('VM_Gun', 'Hips', (0, 0, 0)); bone_at('VM_Mag', 'VM_Gun', (SPEC['xc'], myc, mzc)); bone_at('VM_Handle', 'VM_Gun', tuple(G0.inverted() @ kn))
bone_at('VM_Cover', 'VM_Gun', SPEC['cover_hinge'])
for o, b in ((gun, 'VM_Gun'), (mag, 'VM_Mag'), (ch, 'VM_Handle'), (cover, 'VM_Cover')): L.bind_rigid(arm, o, b)
REST = {b.name: b.matrix_local.copy() for b in arm.data.bones}
# ---- 운동학
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def seg(t, t0, t1): return ease((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)
def lin(t, t0, t1): return min(max((t - t0) / (t1 - t0), 0.0), 1.0)
def gun_delta(back=0.0, up=0.0, pitch=0.0, roll=0.0, yaw=0.0, side=0.0):
    pv = G0 @ Vector((SPEC['xc'], gy, gz))   # 손잡이 기준 회전
    R = Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(-pitch), 4, 'Y') @ Matrix.Rotation(math.radians(roll), 4, 'X')
    return Matrix.Translation(Vector((-back, side, up)) / 100.0) @ Matrix.Translation(pv) @ R @ Matrix.Translation(-pv)
OPEN = False   # MG34: 장전 손잡이는 당겼다 앞으로 밀어 두고 사격 때 움직이지 않음
REST_S = SPEC['travel'] if OPEN else 0.0
def frames(st):
    Gw = st['D'] @ G0; Mw = st.get('Mw') or Gw
    HG = Vector(SPEC['cover_hinge']); Cw = Gw @ Matrix.Translation(HG) @ Matrix.Rotation(math.radians(st.get('cv', 0.0)), 4, 'X') @ Matrix.Translation(-HG)   # 덮개: 앞 경첩(X 축)으로 뒤끝이 위로
    return {'gun': Gw, 'mag': Mw, 'handle': Gw @ Matrix.Translation((0, st['s'], 0)), 'cover': Cw, 'cam': Matrix.Identity(4)}
REF0 = frames({'D': Matrix.Identity(4), 's': 0.0})
REL = {k: REF0[v['ref']].inverted() @ v['W'] for k, v in ST.items()}
def hand_world(key, F): return F[ST[key]['ref']] @ REL[key]
def blend_W(Wa, Wb, x, lift=0.0):
    la, ra, _ = Wa.decompose(); lb, rb, _ = Wb.decompose(); l = la.lerp(lb, x) + Vector((0, 0, lift * math.sin(math.pi * x)))
    return Matrix.LocRotScale(l, ra.slerp(rb, x), None)
def blend_f(fa, fb, x): return {b: fa.get(b, 0.0) * (1 - x) + fb.get(b, 0.0) * x for b in set(fa) | set(fb)}
FIRE_LEN = SPEC['fire_len']
def tl_idle(t):
    ph = 2 * math.pi * t / 4.0
    return {'D': gun_delta(up=0.25 * math.sin(ph), pitch=0.3 * math.sin(ph + 0.6), roll=0.2 * math.sin(ph * 0.5)), 's': REST_S, 'L': ('L_GRIP', 'L_GRIP', 0), 'mag_vis': 1}
def tl_fire(t):   # 한 발 주기(분당 rpm): 반동 + 노리쇠(손잡이) 왕복
    k = seg(t, 0.0, 0.25 * FIRE_LEN) * (1 - seg(t, 0.25 * FIRE_LEN, FIRE_LEN))
    if OPEN: s = SPEC['travel'] * (1 - lin(t, 0.0, 0.25 * FIRE_LEN)) if t < 0.25 * FIRE_LEN else SPEC['travel'] * lin(t, 0.25 * FIRE_LEN, 0.9 * FIRE_LEN)
    else: s = 0.0   # StG44: 장전 손잡이는 사격 때 움직이지 않는 것으로(자료 엇갈림 -> 보수적으로)
    return {'D': gun_delta(back=1.2 * k, up=0.4 * k, pitch=1.6 * k, roll=0.4 * k), 's': s, 'L': ('L_GRIP', 'L_GRIP', 0), 'mag_vis': 1}
RT = {'tilt': (0.0, 0.45, 4.40, 4.8), 'rToCov': (0.05, 0.40), 'open': (0.40, 0.70), 'rBack1': (0.70, 1.00), 'toMag': (0.55, 0.95), 'unhook': (0.95, 1.20), 'out': (1.20, 1.45),
      'toPouch': (1.45, 1.85), 'toWell': (1.85, 2.30), 'hook': (2.30, 2.55), 'toTray': (2.55, 2.80), 'pullBelt': (2.80, 2.95), 'toGrip': (2.95, 3.30),
      'rToCov2': (2.80, 3.10), 'close': (3.10, 3.30), 'toCH': (3.30, 3.55), 'pull': (3.55, 3.75), 'push': (3.82, 3.98), 'rBack': (3.98, 4.35)}
HOOK = Vector(SPEC['drum_hook'])
def drum_swing(Gw, a):   # 드럼 뒤를 앞 고리 축(총의 위 방향)으로 바깥(+X)으로 a도
    return Gw @ Matrix.Translation(HOOK) @ Matrix.Rotation(math.radians(-a), 4, 'Z') @ Matrix.Translation(-HOOK)
def tl_reload(t):
    T = RT; c = seg(t, T['tilt'][0], T['tilt'][1]) * (1 - seg(t, T['tilt'][2], T['tilt'][3]))
    D_ = gun_delta(**{k: v * c for k, v in RELOAD_D.items()}); Gw = D_ @ G0
    swung = drum_swing(Gw, 25.0); away = swung @ Matrix.Translation((7.0, 2.0, -5.0)); Mpouch = ST['L_POUCH']['W'] @ (REF0['mag'].inverted() @ ST['L_MAG']['W']).inverted()
    S1, S0 = Matrix.Scale(100, 4), Matrix.Scale(0.01, 4)
    def bw(a, b_, x, lift=0.0): return blend_W(a @ S1, b_ @ S1, x, lift) @ S0
    # 드럼 경로: 걸림 -> 뒤를 바깥으로 돌림(멈치 풂) -> 빼서 아래 왼쪽 -> 탄입대(화면 밖, 빈 드럼 넣고 새 드럼) -> 돌린 자세로 와서 앞 고리에 걸고 -> 뒤를 돌려 끼움
    if t < T['unhook'][0]: Mw = Gw
    elif t < T['unhook'][1]: Mw = drum_swing(Gw, 25.0 * seg(t, *T['unhook']))
    elif t < T['out'][1]: Mw = bw(swung, away, seg(t, *T['out']))
    elif t < T['toPouch'][1]: Mw = bw(away, Mpouch, seg(t, *T['toPouch']), 0.02)
    elif t < T['toWell'][1]: Mw = bw(Mpouch, swung, seg(t, *T['toWell']), 0.03)
    elif t < T['hook'][1]: Mw = drum_swing(Gw, 25.0 * (1 - seg(t, *T['hook'])))
    else: Mw = Gw
    s = SPEC['travel'] * seg(t, *T['pull']) * (1 - seg(t, *T['push']))   # 끝까지 당겼다가 앞으로 밀어 둠
    cv = SPEC['cover_open'] * seg(t, *T['open']) * (1 - seg(t, *T['close']))
    if t < T['toMag'][0]: Lh = ('L_GRIP', 'L_GRIP', 0)
    elif t < T['toMag'][1]: Lh = ('L_GRIP', 'L_MAG', seg(t, *T['toMag']))
    elif t < T['toTray'][0]: Lh = ('L_MAG', 'L_MAG', 0)
    elif t < T['toGrip'][0]: Lh = ('L_MAG', 'L_TRAY', seg(t, *T['toTray']))   # 새 드럼의 탄띠 앞 고리를 급탄판에 놓고 오른쪽으로 당김
    else: Lh = ('L_TRAY', 'L_GRIP', seg(t, *T['toGrip']))
    if t < T['rToCov'][1]: Rh = ('R_GRIP', 'R_COVER', seg(t, *T['rToCov']))   # 오른손: 덮개 뒤끝 멈치 누르고 들어 올림
    elif t < T['open'][1]: Rh = ('R_COVER', 'R_COVER', 0)
    elif t < T['rToCov2'][0]: Rh = ('R_COVER', 'R_GRIP', seg(t, *T['rBack1']))
    elif t < T['close'][1]: Rh = ('R_GRIP', 'R_COVER', seg(t, *T['rToCov2']))   # 위에서 덮개를 눌러 닫음
    elif t < T['rBack'][0]: Rh = ('R_COVER', 'R_CH', seg(t, *T['toCH']))
    else: Rh = ('R_CH', 'R_GRIP', seg(t, *T['rBack']))
    return {'D': D_, 's': s, 'cv': cv, 'L': Lh, 'R': Rh, 'Mw': Mw, 'mag_vis': 1, 'framing': Vector((.06, .0, .02)) * c}
def view_ang(p): return math.degrees(math.atan2(-p.y, max(p.x, 1e-3))), math.degrees(math.atan2(p.z, max(p.x, 1e-3)))
best = None
# 재장전 때 총을 조금 들어 오른쪽으로 비틀어 드럼(왼쪽 면)이 화면 가운데 약간 아래에 보이게. 왼손(드럼)·오른손(장전 손잡이)이 어깨에서 닿는 자세만.
for yw in (-30, -15, 0, 15):
  for fw in (-6, -3, 0, 3):
    for sd in (0, 4, 8):
        for up in (-5, 0, 5):
            for rl in (-35, -20, 0, 20):
                for pt in (0, 10, 20):
                    Dt = gun_delta(back=-fw, side=sd, up=up, pitch=pt, roll=rl, yaw=yw); F = frames({'D': Dt, 's': 0.0})
                    wm = hand_world('L_MAG', F).translation; wc = hand_world('R_CH', F).translation
                    if (wm - shL).length * 100 > REACH + 2 or (wc - shR).length * 100 > REACH + 2: continue
                    g = F['gun'] @ Vector((DRUM_X, DRUM_C.y, DRUM_C.z)); hg, vg = view_ang(g)
                    left = (F['gun'].to_3x3() @ Vector((1, 0, 0))).normalized(); vis = left.dot((-g).normalized())
                    near = min((F['gun'] @ Vector((SPEC['xc'], yy, SPEC['bore_z']))).x for yy in (SPEC['recv_end'], 0.0))
                    v = abs(hg + 4) + abs(vg + 10) + 40 * max(0, 0.40 - vis) + 2 * max(0, 24 - g.length * 100) + 1 * max(0, 8 - near * 100)
                    cost = v + 0.05 * (abs(fw) + sd + abs(up) * 0.5 + abs(rl) * 0.1 + abs(pt) * 0.2 + abs(yw) * 0.1)
                    if best is None or cost < best[0]: best = (cost, dict(back=-fw, side=sd, up=up, pitch=pt, roll=rl, yaw=yw), [round(hg, 1), round(vg, 1), round(near * 100, 1), round(vis, 2)])
RELOAD_D = best[1] if best else dict(back=-1, side=3, up=4, pitch=8, roll=23); OUT['reload_pose'] = {'delta': RELOAD_D, 'hv': best[2] if best else None}
CLIPS = {'Idle': (tl_idle, 4.0), 'Fire': (tl_fire, round(FIRE_LEN, 4)), 'Reload': (tl_reload, 4.8)}
OUT['clips'] = {k: v[1] for k, v in CLIPS.items()}
# ---- 적용/굽기
PB = arm.pose.bones
for pb in PB: pb.rotation_mode = 'QUATERNION'
hip_rest = PB['Hips'].matrix.copy()
def set_rigid(name, Xw, Xw0, vis=1):
    M = Xw @ Xw0.inverted() @ REST[name]
    if not vis: M = M @ Matrix.Scale(0.001, 4)
    PB[name].matrix = M
def apply_state(st):
    PB['Hips'].matrix = hip_rest
    bpy.context.view_layer.update()
    F = frames(st)
    set_rigid('VM_Gun', F['gun'], REF0['gun']); bpy.context.view_layer.update()
    set_rigid('VM_Handle', F['handle'], REF0['handle']); set_rigid('VM_Mag', F['mag'], REF0['mag'], st.get('mag_vis', 1)); set_rigid('VM_Cover', F['cover'], REF0['cover']); bpy.context.view_layer.update()
    ra_, rb_, rx_ = st.get('R', ('R_GRIP', 'R_GRIP', 0)); Wr = blend_W(hand_world(ra_, F), hand_world(rb_, F), rx_, 0.03 if ra_ != rb_ else 0.0)
    la, lb, lx = st['L']; Wl = blend_W(hand_world(la, F), hand_world(lb, F), lx, 0.03 if la != lb else 0.0)
    for s, W in (('R', Wr), ('L', Wl)):
        l, r, _ = W.decompose(); E['T_' + s].location = l; E['T_' + s].rotation_quaternion = r; E['P_' + s].location = l + POLE[s]
    bpy.context.view_layer.update()
    for s, W in (('R', Wr), ('L', Wl)):
        for _ in range(12):   # IK 목표 보정 3번으론 손목이 1.5~2.5cm 덜 닿았음(판처슈렉, 2026-11-22)
            err = W.translation - (arm.matrix_world @ PB['%s wrist' % L2.SIDE[s]].head)
            if err.length < 2e-4: break
            E['T_' + s].location = E['T_' + s].location + err; bpy.context.view_layer.update()
    L2.apply_fingers(arm, fax['R'], blend_f(ST[ra_]['fing'], ST[rb_]['fing'], rx_)); L2.apply_fingers(arm, fax['L'], blend_f(ST[la]['fing'], ST[lb]['fing'], lx)); bpy.context.view_layer.update()
    if 'framing' in st:
        PB['Hips'].matrix = Matrix.Translation(st['framing']) @ hip_rest
        bpy.context.view_layer.update()
def record(): return {pb.name: arm.convert_space(pose_bone=pb, matrix=pb.matrix, from_space='POSE', to_space='LOCAL').copy() for pb in PB}
CONS = [c for pb in PB for c in pb.constraints]
def bake_clip(name, fn, dur):
    n = max(2, int(round(dur * FPS))); rec = []
    for c in CONS: c.mute = False
    for f in range(n + 1): apply_state(fn(min(dur, f / FPS))); rec.append(record())
    for c in CONS: c.mute = True
    act = bpy.data.actions.new('FPVM_%s_%s' % (KEY, name)); arm.animation_data_create(); arm.animation_data.action = act
    for f, Rr in enumerate(rec):
        for pb in PB:
            pb.matrix_basis = Rr[pb.name]
            for path in ('location', 'rotation_quaternion', 'scale'): pb.keyframe_insert(path, frame=f + 1, group=pb.name)
    act.use_fake_user = True; return act, n
def shot(name, fn, t, views=('fp', 'side'), look=(0.12, -0.05, -0.12), scale=0.9):
    for c in CONS: c.mute = False
    apply_state(fn(t)); return L2.render_views(D + r'\Data\fpvm_%s_%s' % (WK, name), views=views, look=look, scale=scale)
for m in bpy.data.materials:
    m.diffuse_color = (0.85, 0.7, 0.62, 1) if 'Skin' in m.name else (0.25, 0.3, 0.55, 1) if 'Outfit' in m.name else (0.42, 0.42, 0.45, 1)
if STAGE == 'grip':
    R_ = []
    for nm, pt in (('gripR', rc), ('gripL', lc)): R_ += shot(nm, tl_idle, 0.0, ('side', 'left', 'top', 'front'), look=tuple(pt), scale=0.24)
    OUT['renders'] = R_; OUT['gap_after_apply'] = {s_: L2.palm_gap(arm, body, s_, ax[s_], bvh_gun) for s_ in 'RL'}
elif STAGE == 'pose':
    OUT['renders'] = shot('pose', tl_idle, 0.0, ('fp', 'side', 'top', 'front'), look=tuple(G0 @ Vector((0, 0, 0))), scale=0.8)
elif STAGE in ('anim', 'export', 'reload_export'):
    if STAGE == 'anim':
        R_ = []
        for nm, fn, t in (('rl_open', tl_reload, 0.65), ('rl_unhook', tl_reload, 1.2), ('rl_hooked', tl_reload, 2.5), ('rl_tray', tl_reload, 2.9), ('rl_close', tl_reload, 3.25), ('rl_pull', tl_reload, 3.75)):
            R_ += shot(nm, fn, t, ('fp', 'side'), look=tuple(G0 @ Vector((0, 0, 0))), scale=0.8)
        OUT['renders'] = R_
    else:
        bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1.0
        acts = {}
        clips = CLIPS if STAGE == 'export' else {'Reload': CLIPS['Reload']}
        for nm, (fn, dur) in clips.items(): a, n = bake_clip(nm, fn, dur); acts[nm] = a
        for pb in PB:
            for c in list(pb.constraints): pb.constraints.remove(c)
        for e in list(E.values()): bpy.data.objects.remove(e)
        os.makedirs(D + r'\FBX\FPVM', exist_ok=True)
        if STAGE == 'export':
            arm.animation_data.action = acts['Idle']
            bpy.ops.object.select_all(action='DESELECT')
            for o in (arm, body, gun, mag, ch, cover): o.select_set(True)
            for o in CA: o.select_set(True)   # 병과 캐릭터 7종 1인칭 팔
            bpy.context.view_layer.objects.active = arm
            bpy.ops.export_scene.fbx(filepath=D + r'\FBX\FPVM\SK_FPVM_%s.fbx' % KEY, use_selection=True, object_types={'ARMATURE', 'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                                     add_leaf_bones=False, bake_anim=False, mesh_smooth_type='FACE', path_mode='STRIP', armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X')
        for nm, a in acts.items():
            arm.animation_data.action = a; s0, s1 = a.frame_range; bpy.context.scene.frame_start = round(s0); bpy.context.scene.frame_end = round(s1)
            bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
            bpy.ops.export_scene.fbx(filepath=D + r'\FBX\FPVM\AS_FPVM_%s_%s.fbx' % (KEY, nm), use_selection=True, object_types={'ARMATURE'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                                     add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0,
                                     armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X')
        OUT['exported'] = True
        # 정조준 입력(fpvm_ads_calc.py all 이 읽음)
        json.dump({'gun_pos': GUN_POS, 'gun_rot': GUN_ROT, 'rear': rear, 'front': front, 'rear_dist_cm': (SPEC['recv_end'] - rear[1]) + 7.0}, open(D + r'\Data\fpvm_%s_ads_in.json' % WK, 'w'))
OUT['mats'] = sorted({m.name for o in (body, gun, mag, ch, cover) for m in o.data.materials if m}); OUT['spec'] = {k: v for k, v in SPEC.items() if k in ('rpm', 'cap', 'travel', 'fire_len')}
json.dump(OUT, open(D + r'\Data\fpvm_%s.json' % WK, 'w'), indent=1, default=str)
print('FPVM_MG34_OK', json.dumps({k: OUT.get(k) for k in ('gun_pos', 'yL', 'seat', 'L_mag', 'L_ch', 'handle_faces', 'mag_faces', 'tris', 'sight', 'reload_pose', 'unfolded_verts')})[:1600])
