"""blender -b --python fpvm_launchers.py -- <panzerfaust|panzerschreck> <pose|ads|anim|export|gameplay> [json 옵션]
 대전차 화기 1인칭 뷰모델(푸리나 팔 + 화기 한 몸, 2026-11-21). 근거: Motion/DE_FP_MOTION_RESEARCH.md 7·10절.
 Panzerfaust 60: 탄두(Korn 포함)를 관에서 떼어 VM_Warhead 뼈로(쏘면 숨기고 UE 에서 같은 자리에 탄두 발사체를 띄움).
   가늠자 판(VM_Leaf) 구멍 3개 = 30/60/80 m(TM-E 30-451). 겨누기 = 구멍 아래 뾰족한 끝 + 탄두 위 Korn 끝.
   원본 모델의 구멍 높이는 실제 탄도(초속 45 m/s)와 맞지 않아(30 m 구멍이 Korn 보다 낮음) 가늠자 판만 세로로 다시 매핑해
   '구멍 끝-Korn' 선과 관 축 사이 각 = 그 거리의 발사각이 되게 함(관 축으로 날아간 탄두가 그 거리에서 조준점에 떨어짐).
   발사 애니메이션 후반에 빈 관을 내린다. 게임에서는 별도의 관 메시가 바닥으로 떨어진다.
 Panzerschreck(RPzB 54, 방패): 원본은 총구가 +Y 라 Z 180° + 관 축을 원점으로. 원본 안의 로켓(Rocket_001)은 지우고
   로켓 모델은 VM_Rocket 뼈에 연결한다. 게임의 재장전 모션은 무기를 기울였다가 다시 드는 방식이다.
   조준 = 방패 창(사수 왼쪽) 가운데,
   영점 100/150/200 m(로켓 110 m/s) 만큼 관을 들어 올림(가늠쇠 눈금 자료는 찾지 못함).
 출력: FBX/FPVM/SK_FPVM_<KEY>.fbx + AS_FPVM_<KEY>_<Idle|IdleEmpty|Fire|Reload>.fbx, FBX/FPVM/SM_FPVM_PzfWarhead.fbx(발사체),
       Data/fpvm_<key>.json, Data/fpvm_launchers_ads.json(영점별 정조준 변환, 발사각, 소켓).
 gameplay는 바뀐 클립 하나만 내보내며 Panzerfaust의 경우 빈 관 모델도 함께 내보낸다."""
import bpy, bmesh, sys, json, math, os
sys.path.insert(0, r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Scripts\Blender')
import numpy as np
from mathutils import Matrix, Vector, Quaternion
import fpvm_lib as L, fpvm_lib2 as L2
from fpvm_panzerfaust60 import load_panzerfaust60
A = sys.argv[sys.argv.index('--') + 1:]; WK = A[0]; STAGE = A[1] if len(A) > 1 else 'pose'; OPT = json.loads(A[2]) if len(A) > 2 else {}
D = L.D; FPS = 30; KEY = WK.upper(); OUT = {'key': WK, 'stage': STAGE}; PZF = WK == 'panzerfaust'
G_MS2 = 9.81
def elev_deg(r_m, v): return math.degrees(0.5 * math.asin(G_MS2 * r_m / v ** 2))
if PZF:
    V0 = 45.0; ZERO_M = [30, 60, 80]          # Pzf 60: 45 m/s, 가늠자 30/60/80 m
    KORN = Vector((0.0, -43.0, 3.19)); LEAF_Y = -11.1; EYE_CM = OPT.get('eye_cm', 34.0)   # 2026-11-22: 겨드랑이에 낀 자세라 눈이 가늠자 판 뒤 34cm(45cm 는 팔이 관에 안 닿음)(예전 24cm 는 판이 화면 세로를 다 덮음)
    HIP = Vector((-4.0 - (EYE_CM - 24.0), -5.0, -7.0))   # 비조준: 정조준(60 m) 자세에서 뒤·오른쪽 5·아래 7 cm(겨드랑이 쪽). 눈 거리를 늘린 만큼 뒤로(대기 자세·팔 닿는 거리는 예전 그대로)
else:
    V0 = 110.0; ZERO_M = [100, 150, 200]      # RPzB 54 로켓 약 110 m/s
    WIN = Vector((10.99, -39.1, 10.9)); EYE_CM = 28.0   # 눈 = 뒤 가늠자 홈 뒤 28cm(방패 바로 뒤 얼굴, 2026-11-22; 예전 창 중심 40cm)
    HIP = Vector((-3.0, -6.0, -10.0))
THETA = [elev_deg(r, V0) for r in ZERO_M]; OUT['zero'] = {'m': ZERO_M, 'v_ms': V0, 'elev_deg': [round(t, 3) for t in THETA]}
CLAV = {'L': [-10.73, 9.89, -16.11], 'R': [-17.46, -9.78, -17.09]}; REACH = OPT.get('reach', 37.5)
POLE = {'R': Vector((-0.10, -0.14, -0.20)), 'L': Vector((-0.06, 0.16, -0.20))}
# ---- 팔(fpvm_smg.py 와 같은 준비)
arm, body, info = L.load_arms('a1', 0); OUT['arms'] = info; arm.name = 'Armature'
CA = L.class_arm_objects(arm)   # 병과 캐릭터 7종 1인칭 팔(같은 팔 뼈대, 재질 CA<Key>_*): 내보낼 때 함께 선택
OUT['clavicle_err_cm'] = L2.pose_clavicles(arm, CLAV); OUT['sleeves'] = L2.fold_sleeves(arm)
L.bake_arms_rest(arm, [body] + CA)   # 푸리나 팔 + 병과 팔 모두 같은 휴식 자세로(2026-11-22)
for _uv in list(body.data.uv_layers)[1:]: body.data.uv_layers.remove(_uv)
# ---- 화기 정리 + 부품 분리
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
    bmesh.ops.delete(bm, geom=sel, context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(o.data); bm.free()
    p = bpy.data.objects.new(name, me2); bpy.context.scene.collection.objects.link(p); p.matrix_world = o.matrix_world.copy(); return p, len(ids)
def comp_faces(pred):
    lab, comps, co = comps_of(gun); take = set(ci for ci, idx in enumerate(comps) if pred(co[idx].min(0), co[idx].max(0)))
    return lambda f: lab[f.verts[0].index] in take
PARTS = {}
if PZF:
    LEAF_HINGE = Vector((0.0, -13.0, -2.8)); AXIS_Z = -5.1; R_TUBE = 2.43
    WAR_C = Vector((0.0, -40.0, AXIS_Z)); MUZ = Vector((0.0, -27.6, AXIS_Z)); BACK = Vector((0.0, 52.25, AXIS_Z))
    source = os.path.join(D, 'FBX', 'FPVM', 'Panzerfaust60Source', 'panzerfaust.fbx')
    gun, PARTS['warhead'], PARTS['leaf'] = load_panzerfaust60(source, MUZ.y, BACK.y, AXIS_Z)
    # 2026-11-22: 받은 Pzf 60 모델의 실제 가늠자로 조준(예전 공식 높이 NEW_Z 는 이 모델 구멍과 안 맞아 80 m 에선 눈이 판 막힌 곳을 지났음)
    #   가늠쇠 = 탄두 맨 위(Korn), 뒤 = 가늠자 판 구멍 3개(아래부터 30/60/80 m). 각 구멍 가운데 -> 탄두 끝 선이 관보다 기운 각 = 그 영점 발사각.
    from mathutils.bvhtree import BVHTree
    _Lv = np.array([v.co[:] for v in PARTS['leaf'].data.vertices]); _Hv = np.array([v.co[:] for v in PARTS['warhead'].data.vertices])
    KORN = Vector(tuple(_Hv[_Hv[:, 2].argmax()])); KORN.x = 0.0
    _lb = BVHTree.FromPolygons([tuple(v) for v in _Lv], [tuple(p.vertices) for p in PARTS['leaf'].data.polygons]); _y0 = _Lv[:, 1].max() + 1.0
    _zs = np.arange(KORN.z + 0.5, _Lv[:, 2].max(), 0.05); _open = [z for z in _zs if _lb.ray_cast(Vector((0.0, _y0, z)), Vector((0, -1, 0)), 10.0)[0] is None]
    _grp = []
    for z in _open:
        if _grp and z - _grp[-1][-1] < 0.08: _grp[-1].append(z)
        else: _grp.append([z])
    _grp = [g for g in _grp if g[-1] - g[0] > 0.3][:3]; assert len(_grp) == 3, ('leaf holes', [(g[0], g[-1]) for g in _grp])
    LEAF_Y = float((_Lv[:, 1].min() + _Lv[:, 1].max()) / 2)
    REAR = [Vector((0.0, LEAF_Y, (g[0] + g[-1]) / 2)) for g in _grp]
    THETA = [math.degrees(math.atan((r.z - KORN.z) / (r.y - KORN.y))) for r in REAR]
    V0 = float(np.mean([math.sqrt(m * G_MS2 / math.sin(math.radians(2 * t))) for m, t in zip(ZERO_M, THETA)]))   # 공기 저항 든 실효 속도(약 39 m/s)
    OUT['zero'] = {'m': ZERO_M, 'v_ms': round(V0, 2), 'elev_deg': [round(t, 3) for t in THETA], 'holes_z': [[round(g[0], 2), round(g[-1], 2)] for g in _grp], 'korn': [round(c, 2) for c in KORN], 'leaf_y': round(LEAF_Y, 2)}
else:
    gun = L.load_weapon(WK)
    mats = [m.name if m else '' for m in gun.data.materials]
    # 원본 안 로켓(Rocket_001) 지움 -> 단품 로켓 모델로 교체
    ri = mats.index('Rocket_001'); bm = bmesh.new(); bm.from_mesh(gun.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == ri], context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(gun.data); bm.free()
    # 장전 레버(방아쇠 뭉치 앞 사각 고리): 원본 y 7.3~30, 아래 -16 까지
    PARTS['lever'], n = split_faces(gun, 'W_lever', comp_faces(lambda lo, hi: lo[1] >= 7.3 and hi[1] <= 30.0 and lo[2] <= -16.0 and 11.0 <= lo[0] and hi[0] <= 14.2)); OUT['lever_faces'] = n
    # 총구 -Y 로(Z 180°) + 관 축(원본 x 12.62, z 1.83) 을 원점으로
    M = Matrix.Translation((12.62, 0.0, -1.83)) @ Matrix.Rotation(math.pi, 4, 'Z')
    for o in (gun, PARTS['lever']): o.data.transform(M)
    # 2026-11-22 고증 가늠자(bergflak.com pssight/psshield, Soviet 교범 '가늠자 홈 다섯'): 뒤 가늠자는 방패 바로 뒤 관 옆에 용접, 방패 고정쇠가 그 앞에 끼어 유리창이 조준선 위에 오게 함.
    #   원본 모델의 뒤(y -33.3)·앞(y -79.7) 가늠자 틀은 유리창(중심 x 11, z 10.9)보다 9cm 낮아 조준선이 창을 지나지 않음 -> 지우고 창 중심을 지나는 조준선에 새로 만듦.
    #   뒤 = 홈판(가운데 0, 양옆 15·30 앞지름 홈), 앞 = 열린 틀 + 가운데 기둥(150 m 에서 기둥 끝이 홈 바닥에 맞음 - 'T34 가 150 m 에서 기둥 폭').
    def _sight_comp(lo, hi):
        return (-34.3 <= lo[1] and hi[1] <= -32.3 and lo[0] >= 2.4 and hi[2] <= 5.3) or (-80.4 <= lo[1] and hi[1] <= -78.9 and hi[0] <= 9.8 and lo[2] >= -3.6)
    _bm = bmesh.new(); _bm.from_mesh(gun.data); _bm.faces.ensure_lookup_table()
    _lab, _comps, _co = comps_of(gun); _take = set(ci for ci, idx in enumerate(_comps) if _sight_comp(_co[idx].min(0), _co[idx].max(0)))
    _old = [f_ for f_ in _bm.faces if _lab[f_.verts[0].index] in _take]; OUT['old_sight_faces'] = len(_old)
    bmesh.ops.delete(_bm, geom=_old, context='FACES'); bmesh.ops.delete(_bm, geom=[v for v in _bm.verts if not v.link_faces], context='VERTS')
    _mi = mats.index('Main_001')
    def _box(c, sz):
        r = bmesh.ops.create_cube(_bm, size=1.0); vs = r['verts']
        for v in vs: v.co = Vector((c[0] + v.co.x * sz[0], c[1] + v.co.y * sz[1], c[2] + v.co.z * sz[2]))
        for f_ in {f_ for v in vs for f_ in v.link_faces}: f_.material_index = _mi
    SX = 10.99; TH1 = elev_deg(150, 110.0)   # 조준선: 창 중심 x, 관보다 150 m 발사각만큼 아래로 기움
    NOTCH = Vector((SX, -33.3, 11.25)); POST = Vector((SX, -79.7, NOTCH.z - (79.7 - 33.3) * math.tan(math.radians(TH1))))
    # 뒤 가늠자 홈판(두께 0.3, 폭 7, 높이 2.4) - 홈 바닥 = NOTCH.z, 홈 폭 0.5, 깊이 0.8, 앞지름 홈 ±1.3(15)·±2.6(30)
    _hz = NOTCH.z + 0.8; _plate_top = _hz
    for x0, x1 in ((-3.5, -2.85), (-2.35, -1.55), (-1.05, -0.25), (0.25, 1.05), (1.55, 2.35), (2.85, 3.5)):
        _box((SX + (x0 + x1) / 2, NOTCH.y, NOTCH.z + 0.4), (x1 - x0, 0.3, 0.8))
    _box((SX, NOTCH.y, NOTCH.z - 0.8), (7.0, 0.3, 1.6))
    _box(((SX + 4.6) / 2, NOTCH.y, NOTCH.z - 1.4), (SX - 4.6, 0.6, 0.6))           # 받침대(관 왼쪽 위에서 홈판까지)
    _box((5.0, NOTCH.y, (NOTCH.z - 1.4 + 2.5) / 2), (0.6, 0.6, NOTCH.z - 1.4 - 2.5))
    # 앞 가늠자: 열린 틀(폭 6, 높이 7, 굵기 0.4) + 가운데 기둥(폭 0.35, 끝 = POST.z)
    _fb = POST.z - 3.6; _ft = POST.z + 3.0
    _box((SX, POST.y, _fb), (6.0, 0.4, 0.4)); _box((SX, POST.y, _ft), (6.0, 0.4, 0.4))
    _box((SX - 3.0, POST.y, (_fb + _ft) / 2), (0.4, 0.4, _ft - _fb)); _box((SX + 3.0, POST.y, (_fb + _ft) / 2), (0.4, 0.4, _ft - _fb))
    _box((SX, POST.y, (_fb + POST.z) / 2), (0.35, 0.4, POST.z - _fb))
    _box(((SX - 3.0 + 4.6) / 2, POST.y, _fb), (SX - 3.0 - 4.6, 0.6, 0.6)); _box((4.6, POST.y, (_fb + 2.5) / 2), (0.6, 0.6, _fb - 2.5))
    _bm.to_mesh(gun.data); _bm.free(); OUT['pzs_sight'] = {'notch': list(NOTCH), 'post_tip': list(POST), 'elev150_deg': round(TH1, 3)}
    rk = L.load_weapon('panzerschreck_rocket'); rk.name = 'W_rocket'; rk.data.transform(Matrix.Translation((0.0, 44.66, 0.0))); PARTS['rocket'] = rk   # 꼬리 끝 y 77.2(원본 로켓 자리)
    REAR = [Vector((10.99, -33.3, 11.25)) for _ in THETA]; AXIS_Z = 0.0; R_TUBE = 4.95   # 2026-11-22: 뒤 가늠자 홈 바닥(창 중심을 지나는 조준선)
    ROCKET_C = Vector((0.0, 44.66, 0.0)); MUZ = Vector((0.0, -82.0, 0.0)); BACK = Vector((0.0, 82.0, 0.0))
    LEVER_PIV = Vector((0.0, -7.44, -4.1))
OUT['parts'] = {k: len(o.data.polygons) for k, o in PARTS.items()}; OUT['gun_faces'] = len(gun.data.polygons)
# ---- 정조준 자세(영점별): 눈(카메라) 축이 뒤 조준점(REAR)을 지나고, 관 축은 눈 축보다 발사각만큼 위
def ads_pose(i):
    th = math.radians(THETA[i]); u = Vector((math.cos(th), 0, math.sin(th))); v = Vector((-math.sin(th), 0, math.cos(th))); a = Vector((0, 1, 0))
    R3 = Matrix((a, -u, v)).transposed().to_4x4()
    G = R3 @ Matrix.Scale(0.01, 4); p = G @ REAR[i]; G = Matrix.Translation(Vector((EYE_CM / 100.0, 0, 0)) - p) @ G; return G
GADS = [ads_pose(i) for i in range(3)]
G0 = Matrix.Translation(HIP / 100.0) @ GADS[1]       # 메시 기준(대기) 자세 = 가운데 영점 정조준에서 HIP 만큼 내린 자세
FLIP = Matrix.Diagonal((1, -1, 1, 1))
def ue_of(T):
    U = FLIP @ T @ FLIP; q = U.to_quaternion(); return {'ue_loc_cm': [c * 100 for c in U.translation], 'ue_quat_xyzw': [q.x, q.y, q.z, q.w]}
ADS = {}
for i in range(3):
    T = GADS[i] @ G0.inverted(); e = ue_of(T); e.update({'zero_m': ZERO_M[i], 'elev_deg': THETA[i], 'rear_cam_m': list(GADS[i] @ REAR[i])}); ADS[i] = e
for o in [gun] + list(PARTS.values()): o.matrix_world = G0
bpy.context.view_layer.update()
def dirn(d, M=None): return ((M or G0).to_3x3() @ Vector(d)).normalized()
def P(nat, M=None): return (M or G0) @ Vector(nat)
bvh_gun = L2.bvh_of([gun] + list(PARTS.values()))
E = L2.setup_ik(arm); ax = {s: L.hand_axes(arm, s) for s in 'LR'}; fax = {s: L.finger_axes(arm, s, ax[s]) for s in 'LR'}
def solve_place(s, contact, f, p, along=0.45, off=1.6): return L2.place_hand(arm, E, s, ax[s], contact, f, p, palm_off_cm=off, along=along, elbow_hint_m=contact + POLE[s])
def wrist_world(s):
    bpy.context.view_layer.update(); return Matrix.LocRotScale((arm.matrix_world @ arm.pose.bones['%s wrist' % L2.SIDE[s]].head).copy(), E['T_' + s].rotation_quaternion.copy(), None)
def ray(o_nat, d_nat):
    h = bvh_gun.ray_cast(P(o_nat), dirn(d_nat), 2.0); return h[0], h[1]
ST = {}; shL = arm.matrix_world @ arm.pose.bones['Left arm'].head; shR = arm.matrix_world @ arm.pose.bones['Right arm'].head
if PZF:
    # 오른손: 가늠자 뒤 관을 오른쪽에서 감싸 쥐고 엄지는 위 방아쇠 막대 쪽. 왼손: 가늠자 앞(탄두 뒤) 관을 아래에서 받침
    yR = OPT.get('yR', 3.0); yL = OPT.get('yL', -16.5)
    rc, rn = ray((-12.0, yR, AXIS_Z), (1, 0, 0)); assert rc is not None, 'tube ray R'
    lc, ln = ray((0.0, yL, AXIS_Z - 12.0), (0, 0, 1)); assert lc is not None, 'tube ray L'
    fR = dirn((0.0, -0.25, -1.0)); pR = (-rn).normalized(); fL = dirn((-1.0, -0.3, 0.15)); pL = (-ln).normalized()
else:
    # 오른손: 권총 손잡이(관 아래 방아쇠 뭉치). 왼손: 방패 뒤 관 왼쪽 옆을 감싸 받침(손가락은 위로 넘김)
    yR = OPT.get('yR', -6.0); zR = OPT.get('zR', -12.0); yL = OPT.get('yL', -21.0)
    hits = []   # 손잡이 판: 오른쪽에서 격자로 쏴 맞은 점들의 가운데에 가장 가까운 점
    for yy in np.arange(-17.0, 5.0, 1.0):
        for zz in np.arange(-20.0, -4.5, 1.0):
            h_, n_ = ray((-12.0, float(yy), float(zz)), (1, 0, 0))
            if h_ is not None:
                hn = G0.inverted() @ h_
                if -2.5 < hn.x < 0.5: hits.append((h_, n_, hn))
    assert hits, 'grip ray'
    cen = sum((h[2] for h in hits), Vector()) / len(hits); rc, rn, hn = min(hits, key=lambda h: (h[2] - cen).length)
    OUT['grip_ray'] = {'n': len(hits), 'center_nat': [round(c, 2) for c in cen], 'pick_nat': [round(c, 2) for c in hn]}
    assert rc is not None, 'grip ray'
    lc, ln = ray((12.0, yL, 0.5), (-1, 0, 0)); assert lc is not None, 'tube ray L'
    fR = dirn(tuple(OPT.get('fR', (0.15, -0.45, -0.88)))); pR = (-rn).normalized(); fL = dirn((-0.15, -0.25, 1.0)); pL = (-ln).normalized()
OUT['R_grip'] = solve_place('R', rc, fR, pR); OUT['R_grip']['pole'] = L2.calib_pole(arm, E, 'R', E['T_R'].location.copy(), rc + POLE['R']); solve_place('R', rc, fR, pR)
OUT.setdefault('seat', {})['R'] = L2.seat_hand(arm, body, E, 'R', ax['R'], bvh_gun)
import fpvm_grip; _trig, OUT['trigger'] = fpvm_grip.trigger_target(arm, 'R', bvh_gun, G0) if not PZF else (None, 'no trigger guard')   # 검지 = 방아쇠울 안 방아쇠 앞면(2026-11-22)
ST['R_GRIP'] = {'ref': 'gun', 'W': wrist_world('R'), 'fing': L2.grip_fingers(arm, 'R', fax['R'], bvh_gun, r_cm=0.55, limits={'Thumb': (25, 30, 30), 'default': (85, 100, 75)}, targets={'IndexFinger': (_trig[0], 1.0, _trig[1])} if _trig is not None else None)}
OUT['R_grip_fingers'] = fpvm_grip.LAST.get('R')
OUT['L_grip'] = solve_place('L', lc, fL, pL); OUT['L_grip']['pole'] = L2.calib_pole(arm, E, 'L', E['T_L'].location.copy(), lc + POLE['L']); solve_place('L', lc, fL, pL)
OUT['seat']['L'] = L2.seat_hand(arm, body, E, 'L', ax['L'], bvh_gun)
ST['L_GRIP'] = {'ref': 'gun', 'W': wrist_world('L'), 'fing': L2.grip_fingers(arm, 'L', fax['L'], bvh_gun, r_cm=0.55, limits={'Thumb': (25, 30, 30), 'default': (85, 100, 75)})}
OUT['reach_cm'] = {s: round(((arm.matrix_world @ arm.pose.bones['%s wrist' % L2.SIDE[s]].head) - (shL if s == 'L' else shR)).length * 100, 1) for s in 'LR'}
def fset(v, s): return {b: a for f, vals in v.items() for b, a in zip(L.fbones(s, f), vals)}
WRAP = {'Thumb': (25, 30, 25), 'IndexFinger': (45, 55, 40), 'MiddleFinger': (50, 60, 45), 'RingFinger': (55, 65, 45), 'LittleFinger': (55, 65, 45)}
if not PZF:   # 왼손 장전 레버 쥐기(사각 고리 아래 막대 뒤쪽) — 레버 기준
    lv = PARTS['lever']; Pl = np.array([v.co[:] for v in lv.data.vertices]); zb = Pl[:, 2].min()
    tgt = P((0.0, -12.0, float(zb) + 0.4)); H = L2.hand_local(arm, 'L', fax['L'], fset(WRAP, 'L'))
    Wlv, OUT['L_lever'] = L2.search_hand(H, 'palm', tgt, bvh_gun, shL, reach_cm=REACH + 3, excl=(tgt, 0.025), prefer=[(ax['L']['p_local'], dirn((0, 0, 1)), 0.5), (ax['L']['f_local'], dirn((-1, 0, 0)), 0.4)])
    ST['L_LEVER'] = {'ref': 'lever', 'W': Wlv, 'fing': fset(WRAP, 'L')}
# ---- 뼈
def bone_at(name, parent, head_native):
    h = P(head_native); t = P(Vector(head_native) + Vector((0, -5.0, 0))); L.add_bone(arm, name, parent, h, t)
bone_at('VM_Gun', 'Hips', (0, 0, 0))
if PZF:
    bone_at('VM_Warhead', 'VM_Gun', tuple(WAR_C)); bone_at('VM_Leaf', 'VM_Gun', tuple(LEAF_HINGE))
    BIND = ((gun, 'VM_Gun'), (PARTS['warhead'], 'VM_Warhead'), (PARTS['leaf'], 'VM_Leaf'))
else:
    bone_at('VM_Rocket', 'VM_Gun', tuple(ROCKET_C)); bone_at('VM_Lever', 'VM_Gun', tuple(LEVER_PIV))
    BIND = ((gun, 'VM_Gun'), (PARTS['rocket'], 'VM_Rocket'), (PARTS['lever'], 'VM_Lever'))
for o, b in BIND: L.bind_rigid(arm, o, b)
REST = {b.name: b.matrix_local.copy() for b in arm.data.bones}
# ---- 운동학
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def seg(t, t0, t1): return ease((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)
PIV = Vector((0.0, 0.0 if PZF else -6.0, AXIS_Z))   # 회전 기준(오른손 근처 관 축)
def gun_delta(back=0.0, up=0.0, pitch=0.0, roll=0.0, yaw=0.0, side=0.0):
    pv = P(PIV); R = Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(-pitch), 4, 'Y') @ Matrix.Rotation(math.radians(roll), 4, 'X')
    return Matrix.Translation(Vector((-back, side, up)) / 100.0) @ Matrix.Translation(pv) @ R @ Matrix.Translation(-pv)
def about(piv_nat, axis, deg):   # 화기 원본 좌표의 축(X/Y/Z) 회전(부품용, 원본 cm)
    pv = Vector(piv_nat); return Matrix.Translation(pv) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-pv)
def frames(st):
    Gw = st['D'] @ G0; Mn = Matrix.Scale(1.0, 4)
    F = {'gun': Gw, 'cam': Matrix.Identity(4)}
    if PZF:
        F['warhead'] = Gw; F['leaf'] = Gw @ about(LEAF_HINGE, 'X', st.get('leaf', 0.0))
    else:
        F['rocket'] = Gw @ Matrix.Translation((0, st.get('rk', 0.0), 0)); F['lever'] = Gw @ about(LEVER_PIV, 'X', st.get('lever', 0.0))
    return F
REF0 = frames({'D': Matrix.Identity(4)})
REL = {k: REF0[v['ref']].inverted() @ v['W'] for k, v in ST.items()}
def hand_world(key, F): return F[ST[key]['ref']] @ REL[key]
def blend_W(Wa, Wb, x, lift=0.0):
    la, ra, _ = Wa.decompose(); lb, rb, _ = Wb.decompose(); l = la.lerp(lb, x) + Vector((0, 0, lift * math.sin(math.pi * x)))
    return Matrix.LocRotScale(l, ra.slerp(rb, x), None)
def blend_f(fa, fb, x): return {b: fa.get(b, 0.0) * (1 - x) + fb.get(b, 0.0) * x for b in set(fa) | set(fb)}
def breathe(t): ph = 2 * math.pi * t / 4.0; return gun_delta(up=0.25 * math.sin(ph), pitch=0.25 * math.sin(ph + 0.6), roll=0.15 * math.sin(ph * 0.5))
LEAF_FOLD = 85.0   # 가늠자 접힘(앞으로 눕힘)
def tl_idle(t): return {'D': breathe(t), 'L': ('L_GRIP', 'L_GRIP', 0), 'part_vis': 1}
def tl_idle_empty(t): return {'D': breathe(t), 'L': ('L_GRIP', 'L_GRIP', 0), 'part_vis': 0}
FIRE_LEN = 1.0 if PZF else 0.8
def tl_fire(t):   # 무반동(뒤로 가스 분출) -> 몸으로 오는 반동은 작음: 짧게 들썩이고 가라앉음
    k = seg(t, 0.0, 0.06) * (1 - seg(t, 0.06, 0.6))
    release = seg(t, 0.23, 0.72) if PZF else 0.0
    return {'D': gun_delta(back=0.8 * k, up=0.6 * k - 21 * release, pitch=1.8 * k - 24 * release,
                          roll=0.5 * k + 28 * release, side=12 * release),
            'L': ('L_GRIP', 'L_GRIP', 0), 'part_vis': 0}
if PZF:
    RELOAD_LEN = 3.0
    def tl_reload(t):
        # 0~0.7 빈 관을 내림(화면 밖) -> 0.75 새 관(탄두 있음, 가늠자 접힘) -> 0.8~1.6 올림(가늠자가 보이게 조금 들고) -> 1.8~2.2 가늠자 세움 -> 2.2~2.9 대기 자세
        down = seg(t, 0.0, 0.7) * (1 - seg(t, 0.8, 1.6))
        prep = seg(t, 0.8, 1.6) * (1 - seg(t, 2.2, 2.9))
        D_ = gun_delta(up=-42 * down - 3 * prep, back=6 * down + 2 * prep, pitch=-25 * down + 6 * prep, roll=25 * down - 6 * prep, side=-6 * down)
        leaf = LEAF_FOLD * (1 - seg(t, 1.8, 2.2)) if t >= 0.75 else 0.0
        return {'D': D_, 'L': ('L_GRIP', 'L_GRIP', 0), 'part_vis': 1 if t >= 0.75 else 0, 'leaf': leaf}
else:
    RELOAD_LEN = 4.0
    def tl_reload(t):
        lower = seg(t, 0.0, 1.05) * (1 - seg(t, 2.15, 3.82))
        settle = math.exp(-((t - 3.64) / 0.19) ** 2)
        pose = gun_delta(up=-8 * lower - 1.7 * settle, back=2 * lower, pitch=10 * lower + 1.2 * settle,
                         roll=12 * lower, yaw=6 * lower, side=3 * lower)
        return {'D': pose, 'L': ('L_GRIP', 'L_GRIP', 0), 'part_vis': t >= 2.05}
CLIPS = {'Idle': (tl_idle, 4.0), 'IdleEmpty': (tl_idle_empty, 4.0), 'Fire': (tl_fire, FIRE_LEN), 'Reload': (tl_reload, RELOAD_LEN)}
OUT['clips'] = {k: v[1] for k, v in CLIPS.items()}
# ---- 적용/굽기
PB = arm.pose.bones
for pb in PB: pb.rotation_mode = 'QUATERNION'
hip_rest = PB['Hips'].matrix.copy()
def set_rigid(name, Xw, Xw0, vis=1):
    M_ = Xw @ Xw0.inverted() @ REST[name]
    if not vis: M_ = M_ @ Matrix.Scale(0.001, 4)
    PB[name].matrix = M_
def apply_state(st):
    PB['Hips'].matrix = hip_rest; bpy.context.view_layer.update(); F = frames(st)
    set_rigid('VM_Gun', F['gun'], REF0['gun']); bpy.context.view_layer.update()
    if PZF:
        set_rigid('VM_Warhead', F['warhead'], REF0['warhead'], st.get('part_vis', 1)); set_rigid('VM_Leaf', F['leaf'], REF0['leaf'])
    else:
        set_rigid('VM_Rocket', F['rocket'], REF0['rocket'], st.get('part_vis', 1)); set_rigid('VM_Lever', F['lever'], REF0['lever'])
    bpy.context.view_layer.update()
    Wr = hand_world('R_GRIP', F); la, lb, lx = st['L']; Wl = blend_W(hand_world(la, F), hand_world(lb, F), lx, 0.03 if la != lb else 0.0)
    for s, W in (('R', Wr), ('L', Wl)):
        l, r, _ = W.decompose(); E['T_' + s].location = l; E['T_' + s].rotation_quaternion = r; E['P_' + s].location = l + POLE[s]
    bpy.context.view_layer.update()
    for s, W in (('R', Wr), ('L', Wl)):
        for _ in range(12):   # IK 목표 보정 3번으론 손목이 1.5~2.5cm 덜 닿았음(판처슈렉, 2026-11-22)
            err = W.translation - (arm.matrix_world @ PB['%s wrist' % L2.SIDE[s]].head)
            if err.length < 2e-4: break
            E['T_' + s].location = E['T_' + s].location + err; bpy.context.view_layer.update()
    L2.apply_fingers(arm, fax['R'], ST['R_GRIP']['fing']); L2.apply_fingers(arm, fax['L'], blend_f(ST[la]['fing'], ST[lb]['fing'], lx)); bpy.context.view_layer.update()
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
for m in bpy.data.materials:
    m.diffuse_color = (0.85, 0.7, 0.62, 1) if 'Skin' in m.name else (0.25, 0.3, 0.55, 1) if 'Outfit' in m.name else (0.36, 0.38, 0.30, 1)
def shot(name, fn, t, views=('fp', 'side'), look=None, scale=1.4, T=None):
    for c in CONS: c.mute = False
    apply_state(fn(t))
    movers = [arm] + [o for o in bpy.data.objects if o.type in ('MESH', 'EMPTY') and o.parent is None]
    keep = {o: o.matrix_world.copy() for o in movers}
    if T is not None:
        for o in movers: o.matrix_world = T @ o.matrix_world
        bpy.context.view_layer.update()
    f = L2.render_views(D + r'\Data\fpvm_%s_%s' % (WK, name), views=views, look=look or tuple(P((0, 0, AXIS_Z))), scale=scale)
    if T is not None:
        for o, mw in keep.items(): o.matrix_world = mw
        bpy.context.view_layer.update()
    return f
# ---- 소켓(UE 카메라 공간, 대기 자세 기준): 발사 위치(탄두/로켓 중심), 관 앞 끝, 관 뒤 끝(후폭풍)
def sock(nat, fwd_nat):
    w = P(nat); fw = dirn(fwd_nat); up = dirn((0, 0, 1)); return {'ue_cam_cm': [w.x * 100, -w.y * 100, w.z * 100], 'ue_fwd': [fw.x, -fw.y, fw.z], 'ue_up': [up.x, -up.y, up.z]}
SOCK = {'VM_Muzzle': sock(MUZ, (0, -1, 0)), 'VM_Launch': sock(WAR_C if PZF else MUZ + Vector((0, -20.0, 0)), (0, -1, 0)), 'VM_Rear': sock(BACK, (0, 1, 0))}
def export_animation(name, action):
    arm.animation_data.action = action
    start, end = action.frame_range
    bpy.context.scene.frame_start = round(start)
    bpy.context.scene.frame_end = round(end)
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(filepath=D + r'\FBX\FPVM\AS_FPVM_%s_%s.fbx' % (KEY, name),
                             use_selection=True, object_types={'ARMATURE'}, axis_forward='-Y', axis_up='Z',
                             apply_unit_scale=True, add_leaf_bones=False, bake_anim=True,
                             bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             bake_anim_simplify_factor=0.0, armature_nodetype='NULL',
                             primary_bone_axis='Y', secondary_bone_axis='X')


def export_spent_tube():
    meshes = []
    for source in (gun, PARTS['leaf']):
        obj = bpy.data.objects.new('TubePropPart', source.data.copy())
        bpy.context.scene.collection.objects.link(obj)
        meshes.append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    tube = bpy.context.view_layer.objects.active
    tube.name = 'SM_FPVM_PzfSpentTube'
    tube.data.transform(Matrix.Scale(0.01, 4) @ Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Translation(-(MUZ + BACK) / 2))
    bpy.ops.export_scene.fbx(filepath=D + r'\FBX\FPVM\SM_FPVM_PzfSpentTube.fbx', use_selection=True,
                             object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                             mesh_smooth_type='FACE', path_mode='STRIP', bake_anim=False)


if STAGE == 'gameplay':
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.render.fps_base = 1.0
    clip = 'Fire' if PZF else 'Reload'
    action, _ = bake_clip(clip, *CLIPS[clip])
    for pb in PB:
        for constraint in list(pb.constraints):
            pb.constraints.remove(constraint)
    export_animation(clip, action)
    if PZF:
        export_spent_tube()
    print('FPVM_LAUNCHER_GAMEPLAY_EXPORTED', KEY, clip)
    sys.exit(0)
elif STAGE == 'pose':
    OUT['renders'] = shot('pose', tl_idle, 0.0, ('fp', 'side', 'top', 'back'))
elif STAGE == 'ads':
    R_ = []
    for i in range(3): R_ += shot('ads%d' % i, tl_idle, 0.0, ('fp',), T=GADS[i] @ G0.inverted())
    OUT['renders'] = R_
elif STAGE == 'anim':
    R_ = []
    pts = (('fire', tl_fire, 0.06), ('rl1', tl_reload, 0.5), ('rl2', tl_reload, 1.3), ('rl3', tl_reload, 2.0), ('rl4', tl_reload, 2.7)) if PZF else \
          (('fire', tl_fire, 0.06), ('rl1', tl_reload, 1.0), ('rl2', tl_reload, 2.0), ('rl3', tl_reload, 2.8), ('rl4', tl_reload, 3.6))
    for nm, fn, t in pts: R_ += shot(nm, fn, t, ('fp', 'side'))
    OUT['renders'] = R_
elif STAGE == 'export':
    bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1.0
    acts = {}
    for nm, (fn, dur) in CLIPS.items(): a, n = bake_clip(nm, fn, dur); acts[nm] = a
    for pb in PB:
        for c in list(pb.constraints): pb.constraints.remove(c)
    for e in list(E.values()): bpy.data.objects.remove(e)
    os.makedirs(D + r'\FBX\FPVM', exist_ok=True)
    arm.animation_data.action = acts['Idle']
    bpy.ops.object.select_all(action='DESELECT')
    for o in [arm, body, gun] + list(PARTS.values()): o.select_set(True)
    for o in CA: o.select_set(True)   # 병과 캐릭터 7종 1인칭 팔
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(filepath=D + r'\FBX\FPVM\SK_FPVM_%s.fbx' % KEY, use_selection=True, object_types={'ARMATURE', 'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                             add_leaf_bones=False, bake_anim=False, mesh_smooth_type='FACE', path_mode='STRIP', armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X')
    for nm, a in acts.items():
        export_animation(nm, a)
    if PZF:
        src = PARTS['warhead']; me = src.data.copy(); ob = bpy.data.objects.new('SM_FPVM_PzfWarhead', me); bpy.context.scene.collection.objects.link(ob)
        ob.data.transform(Matrix.Scale(0.01, 4) @ Matrix.Translation(-WAR_C))
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.export_scene.fbx(filepath=D + r'\FBX\FPVM\SM_FPVM_PzfWarhead.fbx', use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True, mesh_smooth_type='FACE', path_mode='STRIP', bake_anim=False)
        export_spent_tube()
    OUT['exported'] = True
    f = os.path.join(D, 'Data', 'fpvm_launchers_ads.json'); allj = json.load(open(f)) if os.path.isfile(f) else {}
    allj[WK] = {'zeros': ADS, 'sockets': SOCK, 'v0_ms': V0, 'clips': OUT['clips'], 'gun_pos_mat': [list(r) for r in G0]}
    json.dump(allj, open(f, 'w'), indent=1)
OUT['ads'] = ADS; OUT['sockets'] = SOCK
OUT['mats'] = sorted({m.name for o in [body, gun] + list(PARTS.values()) for m in o.data.materials if m})
json.dump(OUT, open(D + r'\Data\fpvm_%s.json' % WK, 'w'), indent=1, default=str)
print('FPVM_LAUNCHER_OK', json.dumps({k: OUT.get(k) for k in ('zero', 'parts', 'R_grip', 'L_grip', 'reach_cm', 'seat', 'L_lever', 'grip_ray')}, default=str)[:2500])
