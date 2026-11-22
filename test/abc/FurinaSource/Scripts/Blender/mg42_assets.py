"""blender -b --python mg42_assets.py -- <check|export>  (2026-11-22)
MG42 설치(거치) 사격용 에셋:
 1) 총(양각대 편 상태, 받은 모델 정리본 SM_DE_mg42): 정리본은 긴 축으로 90° 누워 있음(위 = -X, 손잡이·양각대 발 = +X) -> 표준(위 +Z, 왼쪽 +X, 총구 -Y)으로 돌림.
    원점 = 땅(양각대 발·개머리판 바닥 높이) 위 총 가운데. -> FBX/MG42/SM_MG42_Deployed.fbx
 2) 탄 한 발 단위(탄띠 고리 + 7.92x57 s.S. 탄): 받은 탄띠 에셋은 실제의 약 0.6배라 실제 치수로 새로 만듦(사용자 지정: 탄피 황동, 뇌관 구리).
    탄피 57mm·림 11.95mm·탄두 s.S.(전장 80.6mm) 회전체, 뇌관 지름 5.5mm 원판, 탄두 톰백(구리빛), 고리 = 탄피를 감는 띠 + 다음 고리로 이어지는 코일(흑색 강철).
    단위 좌표: X = 탄띠가 총으로 들어가는 방향(다음 탄 쪽 반대), Z = 탄 축(탄두 끝 쪽), 원점 = 탄 무게중심. -> FBX/MG42/SM_MG42_BeltUnit.fbx
 3) 탄약 상자(Patronenkasten 34 꼴, 받은 에셋): 열린 상자(뚜껑 열림, 안의 탄띠 지움)·닫힌 상자, 길이 35.5cm 로 고르게 키움. -> SM_MG42_BoxOpen / SM_MG42_BoxClosed
 4) 상자 안 탄 250발 자리: 탄을 세워(탄두 위) 탄띠를 상자 길이 방향으로 18발씩 지그재그 14줄(252자리). 순서 = 상자 입구 쪽(먼저 나가는 탄)부터.
 5) 배치(설치 상태): 상자는 총 왼쪽(+X) 땅 위, 긴 축이 총과 나란히, 입구 = 총 쪽 벽 위 가운데. 급탄구 = 리시버 왼쪽 덮개 아래 입구.
 -> Data/mg42_emplacement.json (모두 설치 원점 기준 cm, 언리얼과 같은 축: UE 는 Y 를 뒤집어 씀)"""
import bpy, bmesh, sys, json, math, os
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Scripts\Blender')
import fpvm_lib as L
A = sys.argv[sys.argv.index('--') + 1:]; STAGE = A[0] if A else 'check'
D = L.D; OUTD = os.path.join(D, 'FBX', 'MG42'); os.makedirs(OUTD, exist_ok=True)
SRC_BOX = os.environ.get('MG42_BOX_BLEND', r'C:\Users\fromj\AppData\Local\Temp\mg42box_src\MG42_Belt_Box_Colored.blend')
OUT = {}
PITCH = 1.75      # 탄띠 고리 간격(cm) - Patronengurt 34 (50발 약 0.9m)
CART_LEN = 8.06
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, rgb, metal, rough):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*rgb, 1); return m


# ---------------------------------------------------------------- 1) 총
gun = L.load_weapon('mg42'); gun.name = 'MG42'
R = Matrix(((0, 0, 1, 0), (0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 0, 1)))   # new = (z, y, -x)
gun.data.transform(R)
co = np.array([v.co[:] for v in gun.data.vertices])
feet = co[co[:, 1] < -30]; butt = co[co[:, 1] > 40]
GROUND = float(min(feet[:, 2].min(), butt[:, 2].min()))
jacket = co[(co[:, 1] > -28) & (co[:, 1] < -2)]; BORE = Vector((float(np.median(jacket[:, 0])), 0, float((jacket[:, 2].min() + jacket[:, 2].max()) / 2)))
gun.data.transform(Matrix.Translation((-BORE.x, 0, -GROUND)))
co = np.array([v.co[:] for v in gun.data.vertices]); BORE_Z = BORE.z - GROUND
OUT['gun'] = {'bbox': [co.min(0).round(2).tolist(), co.max(0).round(2).tolist()], 'bore_z': round(BORE_Z, 2), 'ground_was': round(GROUND, 2)}
# 급탄구: 리시버(y -2..18) 왼쪽(+X) 면, 총열 높이 + 1cm 에서 가장 바깥 점보다 0.5cm 밖
rec = co[(co[:, 1] > 2) & (co[:, 1] < 12) & (np.abs(co[:, 2] - (BORE_Z + 1.0)) < 1.0)]
FEED = Vector((float(rec[:, 0].max()) + 0.5, 7.0, BORE_Z + 1.0)); OUT['feed'] = [round(c, 2) for c in FEED]
# 양각대 축(조준 회전 중심): 양각대 위 끝 = 총열 덮개 앞쪽, 총열 높이
BIPOD = Vector((0.0, float(feet[:, 1].mean()), BORE_Z)); OUT['bipod_pivot'] = [round(c, 2) for c in BIPOD]

# ---------------------------------------------------------------- 2) 탄 한 발 단위
def lathe(name, prof, segs=20, cap_lo=True, cap_hi=True, z0=0.0):
    bm = bmesh.new(); rings = []
    for r, z in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs), z + z0)) for k in range(segs)] if r > 1e-4 else [bm.verts.new((0, 0, z + z0))]
        rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        if len(a) == 1:
            for k in range(segs): bm.faces.new((a[0], b[k], b[(k + 1) % segs]))
        elif len(b) == 1:
            for k in range(segs): bm.faces.new((a[k], a[(k + 1) % segs], b[0]))
        else:
            for k in range(segs): bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
    if cap_lo and len(rings[0]) > 1: bm.faces.new(list(reversed(rings[0])))
    if cap_hi and len(rings[-1]) > 1: bm.faces.new(rings[-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o
M_CASE = mat('MG42_Case_Brass', (0.80, 0.60, 0.26), 1.0, 0.32)
M_PRIM = mat('MG42_Primer_Copper', (0.72, 0.36, 0.20), 1.0, 0.35)
M_BUL = mat('MG42_Bullet_Tombac', (0.70, 0.42, 0.24), 1.0, 0.30)
M_LINK = mat('MG42_Link_Steel', (0.06, 0.06, 0.065), 0.8, 0.55)
# 탄피(머리 z 0 -> 입 z 5.7): 림 r .595, 추출 홈, 몸통 .585 -> .545, 어깨 -> 목 .448
case = lathe('case', [(0.27, 0.0), (0.595, 0.0), (0.595, 0.11), (0.48, 0.14), (0.48, 0.25), (0.585, 0.30), (0.545, 4.62), (0.452, 4.98), (0.448, 5.70), (0.40, 5.70)], cap_lo=False, cap_hi=False)
primer = lathe('primer', [(0.0, -0.005), (0.27, -0.005), (0.27, 0.0)], cap_lo=False, cap_hi=False)
bullet = lathe('bullet', [(0.40, 5.70), (0.411, 5.72), (0.411, 6.55), (0.36, 7.20), (0.22, 7.80), (0.06, 8.05), (0.0, 8.06)], cap_lo=True, cap_hi=False)
case.data.materials.append(M_CASE); primer.data.materials.append(M_PRIM); bullet.data.materials.append(M_BUL)
# 고리(Gurt 34): 탄피 몸통(z 1.4~3.0)을 감는 얇은 띠(앞이 트임) + 다음 탄 쪽(-X)으로 이어지는 코일(경첩)
def link_mesh():
    bm = bmesh.new(); segs = 18; r0, r1 = 0.60, 0.66; z_lo, z_hi = 1.5, 2.9
    def ring(r, z, a0, a1): return [bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for a in np.linspace(a0, a1, segs)]
    a0, a1 = math.radians(40), math.radians(320)   # +X 쪽(탄이 나가는 쪽)이 트임
    rl = [ring(r0, z_lo, a0, a1), ring(r1, z_lo, a0, a1), ring(r1, z_hi, a0, a1), ring(r0, z_hi, a0, a1)]
    for i in range(4):
        a, b = rl[i], rl[(i + 1) % 4]
        for k in range(segs - 1): bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
    me = bpy.data.meshes.new('link'); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('link', me); bpy.context.scene.collection.objects.link(o); return o
link = link_mesh(); link.data.materials.append(M_LINK)
coil = lathe('coil', [(0.0, 0.0), (0.14, 0.0), (0.14, 1.9), (0.0, 1.9)], segs=10, cap_lo=False, cap_hi=False, z0=0.0)
coil.data.transform(Matrix.Translation((-PITCH * 0.5, 0.0, 1.25))); coil.data.materials.append(M_LINK)
unit_parts = [case, primer, bullet, link, coil]
bpy.ops.object.select_all(action='DESELECT')
for o in unit_parts: o.select_set(True)
bpy.context.view_layer.objects.active = case; bpy.ops.object.join(); unit = case; unit.name = 'MG42_BeltUnit'
unit.data.transform(Matrix.Translation((0, 0, -3.6)))   # 원점 = 대략 무게중심(탄피 가운데쯤)
OUT['unit'] = {'pitch_cm': PITCH, 'len_cm': CART_LEN, 'verts': len(unit.data.vertices), 'origin_from_head_cm': 3.6}

# ---------------------------------------------------------------- 3) 상자
def load_box(names, scale):
    with bpy.data.libraries.load(SRC_BOX, link=False) as (src, dst): dst.objects = [n for n in src.objects if n in names]
    objs = [o for o in dst.objects if o]
    for o in objs: bpy.context.scene.collection.objects.link(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.data.transform(Matrix.Scale(100 * scale, 4))
    # 원본 장면에서 상자가 비스듬히(약 15°) 놓여 있음 -> 벽 윗부분 정점들의 주축(PCA)을 Y 축으로 맞춤
    P = np.array([v.co[:] for v in o.data.vertices]); W_ = P[P[:, 2] > P[:, 2].min() + 0.75 * (P[:, 2].max() - P[:, 2].min())][:, :2]
    W_ = W_ - W_.mean(0); ev, evec = np.linalg.eigh(np.cov(W_.T)); ax = evec[:, int(np.argmax(ev))]
    ang = math.atan2(ax[0], ax[1]); o.data.transform(Matrix.Rotation(ang, 4, 'Z')); OUT.setdefault('box_align_deg', []).append(round(math.degrees(ang), 2))
    return o
closed = load_box(['Closed box | Handle folded'], 1.0)
cc = np.array([v.co[:] for v in closed.data.vertices]); ext = cc.max(0) - cc.min(0); BOX_S = 35.5 / float(max(ext[0], ext[1]))   # 자료 하나(fjm44)가 36x17x9cm: 250발을 세워 넣으려면 이 크기가 필요(27.5cm 면 약 195발)
closed.data.transform(Matrix.Scale(BOX_S, 4)); cc = np.array([v.co[:] for v in closed.data.vertices])
long_axis = int(np.argmax((cc.max(0) - cc.min(0))[:2]))
if long_axis == 0: closed.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z')); cc = np.array([v.co[:] for v in closed.data.vertices])   # 긴 축 = Y
cen = (cc.min(0) + cc.max(0)) / 2; closed.data.transform(Matrix.Translation((-cen[0], -cen[1], -cc[:, 2].min()))); closed.name = 'MG42_BoxClosed'
cc = np.array([v.co[:] for v in closed.data.vertices]); OUT['box_closed'] = {'size': (cc.max(0) - cc.min(0)).round(2).tolist(), 'scale': round(BOX_S * 100, 3)}
opened = load_box(['Open box'], 1.0); opened.data.transform(Matrix.Scale(BOX_S, 4)); oc = np.array([v.co[:] for v in opened.data.vertices])
# 열린 상자: 몸통(뚜껑 뺀) 범위 = 가장 높은 벽 높이 근처 정점들의 y 범위로
body = oc[oc[:, 2] > oc[:, 2].max() * 0.85]
oyl = (oc.max(0) - oc.min(0)); long_o = int(np.argmax(oyl[:2]))
if long_o == 0: opened.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z')); oc = np.array([v.co[:] for v in opened.data.vertices])
# 몸통 = 닫힌 상자 크기와 같은 길이: 바닥(z 최저 근처) 정점들의 범위
walls = oc[oc[:, 2] > oc[:, 2].min() + 0.75 * (oc[:, 2].max() - oc[:, 2].min())]   # 몸통 벽 윗부분(뚜껑은 땅에 펼쳐져 낮음)
bcen = (walls.min(0) + walls.max(0)) / 2
opened.data.transform(Matrix.Translation((-bcen[0], -bcen[1], -oc[:, 2].min()))); opened.name = 'MG42_BoxOpen'
oc = np.array([v.co[:] for v in opened.data.vertices]); walls = oc[oc[:, 2] > 0.75 * oc[:, 2].max()]
from mathutils.bvhtree import BVHTree   # 안쪽 벽: 몸통 가운데(벽 높이 절반)에서 ±X/±Y 로 쏜 광선이 처음 닿는 면
_bv = BVHTree.FromPolygons([tuple(v.co) for v in opened.data.vertices], [tuple(p.vertices) for p in opened.data.polygons]); _c = Vector((0, 0, 0.5 * float(walls[:, 2].max())))
_d = {k: _bv.ray_cast(_c, Vector(v), 100)[3] for k, v in (('+x', (1, 0, 0)), ('-x', (-1, 0, 0)), ('+y', (0, 1, 0)), ('-y', (0, -1, 0)))}
OUT['box_inner_rays'] = {k: round(v, 2) if v else None for k, v in _d.items()}
_sx = (_d['+x'] - _d['-x']) / 2; _sy = (_d['+y'] - _d['-y']) / 2; opened.data.transform(Matrix.Translation((-_sx, -_sy, 0)))
IN_W, IN_L = _d['+x'] + _d['-x'] - 0.4, _d['+y'] + _d['-y'] - 0.4
WALL_H = float(walls[:, 2].max())
lid_side = 1.0 if oc[:, 1].max() > -oc[:, 1].min() else -1.0   # 뚜껑이 열린 쪽(+Y 또는 -Y)
OUT['box_open'] = {'inner_w': round(IN_W, 2), 'inner_l': round(IN_L, 2), 'wall_h': round(WALL_H, 2), 'lid_side': lid_side, 'bbox': [oc.min(0).round(2).tolist(), oc.max(0).round(2).tolist()]}

# ---------------------------------------------------------------- 4) 상자 안 자리(상자 원점 기준)
N_LAYER, PER = 16, 16; LAYER = min(0.98, (WALL_H - 1.0) / N_LAYER); SPAN = (PER - 1) * PITCH   # 16단 x 16발 = 256자리: 탄을 눕혀(탄 축 = 상자 폭) 탄띠를 길이 방향 지그재그로 쌓음
slots = []   # 바닥(탄띠 끝)부터 쌓은 뒤 뒤집음
for f in range(N_LAYER):
    z = 0.4 + 0.6 + LAYER * f; d = 1 if f % 2 == 0 else -1
    for k in range(PER):
        y = d * (-SPAN / 2 + k * PITCH)
        slots.append({'loc': [-0.43, y, z], 'xdir': [0, d, 0], 'zdir': [1, 0, 0]})   # 탄 원점은 탄 가운데쯤(머리에서 3.6) -> 상자 폭 가운데 근처
slots = slots[:250][::-1]   # 입구 쪽(마지막 줄 끝)부터
# 입구: 마지막 줄(f = 16)이 끝나는 쪽 벽 위
last = slots[0]; MOUTH_BOX = Vector((0.0, last['loc'][1] + 1.0 * (1 if last['xdir'][1] > 0 else -1), WALL_H + 1.5))
OUT['slots_n'] = len(slots); OUT['layer_gap'] = round(LAYER, 3)

# ---------------------------------------------------------------- 5) 설치 배치: 상자 = 총 왼쪽(+X) 땅 위
BOX_POS = Vector((FEED.x + 14.0, FEED.y + 4.0, 0.0)); BOX_YAW = 0.0
def box_to_emp(p): return Matrix.Translation(BOX_POS) @ Matrix.Rotation(BOX_YAW, 4, 'Z') @ Vector(p)
# 입구가 총 쪽(-X)을 보게: 상자를 Z 축으로 돌려 마지막 줄이 총 쪽 벽에 오게
MOUTH = box_to_emp(MOUTH_BOX)
# 늘어진 탄띠(설치 직후 정지 모양): 급탄구 -> 입구, 길이 = 직선 거리 x 1.35, 아래로 처진 2차 베지어. 탄 축은 급탄구(총구 쪽 -Y)에서 상자 안(+X)으로 차츰 돌아감
def bez(t, a, c, b): return a * (1 - t) ** 2 + c * 2 * t * (1 - t) + b * t * t
_d = (MOUTH - FEED).length; _mid = (FEED + MOUTH) / 2; SAG = 0.45 * _d
_ctrl = _mid - Vector((0, 0, SAG)) + (FEED - MOUTH).normalized() * 0.0
_pts = [bez(t, FEED, _ctrl, MOUTH) for t in np.linspace(0, 1, 400)]; _acc = [0.0]
for a_, b_ in zip(_pts[:-1], _pts[1:]): _acc.append(_acc[-1] + (b_ - a_).length)
L_SPAN = _acc[-1]; S_N = int(L_SPAN // PITCH); span = []
for i in range(S_N):
    sv = i * PITCH; j = int(np.searchsorted(_acc, sv)); j = min(max(j, 1), len(_pts) - 1)
    p = _pts[j]; tg = (_pts[j] - _pts[j - 1]).normalized()   # 급탄구 -> 입구 방향
    xdir = -tg   # 단위 X = 총으로 들어가는 쪽
    w = sv / L_SPAN; zc = (Vector((0, -1, 0)) * (1 - w) + Vector((1, 0, 0)) * w).normalized(); zc = (zc - xdir * zc.dot(xdir)).normalized()
    span.append({'loc': [round(c, 3) for c in p], 'xdir': [round(c, 4) for c in xdir], 'zdir': [round(c, 4) for c in zc]})
OUT['span'] = {'n': S_N, 'len_cm': round(L_SPAN, 2), 'sag_cm': round(SAG, 2)}
EMP = {'gun_feed': [round(c, 3) for c in FEED], 'feed_belt_dir': [-1, 0, 0], 'feed_cart_axis': [0, -1, 0],   # 탄띠는 왼쪽에서 오른쪽(-X)으로 들어가고 탄두는 총구(-Y) 쪽
       'bipod_pivot': OUT['bipod_pivot'], 'bore_z': OUT['gun']['bore_z'], 'box_pos': [round(c, 3) for c in BOX_POS], 'box_yaw_deg': round(math.degrees(BOX_YAW), 1),
       'mouth': [round(c, 3) for c in MOUTH], 'pitch': PITCH, 'capacity': 250, 'span': span,
       'slots': [{'loc': [round(c, 3) for c in box_to_emp(s['loc'])], 'xdir': [round(c, 4) for c in (Matrix.Rotation(BOX_YAW, 3, 'Z') @ Vector(s['xdir']))], 'zdir': [round(c, 4) for c in (Matrix.Rotation(BOX_YAW, 3, 'Z') @ Vector(s['zdir']))]} for s in slots]}
OUT['emp'] = {k: v for k, v in EMP.items() if k not in ('slots', 'span')}
json.dump(EMP, open(os.path.join(D, 'Data', 'mg42_emplacement.json'), 'w'), indent=1)


def export(o, name):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUTD, name + '.fbx'), use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                             mesh_smooth_type='FACE', path_mode='STRIP', add_leaf_bones=False, bake_anim=False)


for o in (gun, unit, closed, opened): o.matrix_world = Matrix.Scale(0.01, 4)
if STAGE == 'export':
    export(gun, 'SM_MG42_Deployed'); export(unit, 'SM_MG42_BeltUnit'); export(closed, 'SM_MG42_BoxClosed'); export(opened, 'SM_MG42_BoxOpen'); OUT['exported'] = True
if STAGE in ('check', 'export'):   # 확인 렌더: 설치 전체(탄 250발 자리 + 입구-급탄구 직선)
    for s in EMP['span'] + EMP['slots'][len(EMP['span']):]:
        u = unit.copy(); u.data = unit.data; bpy.context.scene.collection.objects.link(u)
        x = Vector(s['xdir']); z = Vector(s['zdir']); y = z.cross(x)
        u.matrix_world = Matrix.Scale(0.01, 4) @ Matrix.Translation(Vector(s['loc'])) @ Matrix((x, y, z)).transposed().to_4x4()
    ob = opened.copy(); ob.data = opened.data; bpy.context.scene.collection.objects.link(ob); ob.matrix_world = Matrix.Scale(0.01, 4) @ Matrix.Translation(BOX_POS) @ Matrix.Rotation(BOX_YAW, 4, 'Z')
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'; sc.render.resolution_x = 1200; sc.render.resolution_y = 700
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 35
    for nm, eye in (('emp_a', Vector((1.3, 0.9, 0.8))), ('emp_b', Vector((0.5, -0.4, 0.5))), ('emp_top', Vector((0.19, 0.11, 1.2)))):
        tgt = Vector((0.1, 0.0, 0.05)) if nm != 'emp_top' else Vector((0.19, 0.111, 0.0)); d = (tgt - eye).normalized(); xx = d.cross(Vector((0, 0, 1)) if nm != 'emp_top' else Vector((0, 1, 0))).normalized(); yy = xx.cross(d)
        cam.matrix_world = Matrix((xx, yy, -d)).transposed().to_4x4(); cam.location = eye
        sc.render.filepath = os.path.join(D, 'Data', 'mg42_' + nm + '.png'); bpy.ops.render.render(write_still=True)
json.dump(OUT, open(os.path.join(D, 'Data', 'mg42_assets.json'), 'w'), indent=1, default=str)
print('MG42_ASSETS', json.dumps(OUT, default=str)[:1500])
