"""blender -b --python build_class_on_furina.py -- <class_key> [build|preview]
병과 캐릭터(제3제국 7종, 원신 MMD PMX 모델)를 푸리나 뼈대(FBX/Furina_cm.fbx, 240개 뼈 이름·계층·뼈 방향)에 옮겨 FBX/Classes/<key>_cm.fbx 로.
 - 키(cm)는 받은 압축 파일 이름(사용자 지정): CLASSES 표. 모자·리본 등 의상을 포함한 발바닥~맨 위 높이.
 - 가중치: PMX 원래 가중치를 MMD 표준 뼈 이름 -> 푸리나 뼈 이름 표로 합침(표에 없는 뼈 = 가장 가까운 표의 조상, 머리카락·치마 물리 뼈 포함), 정점당 4개.
 - 관절: 몸 21개 + 손가락 30개 = PMX 뼈 위치(각 모델 고유 비율). 뼈 방향만 푸리나와 같게 돌린 자세를 메시에 굳힘(build_soldier_on_furina.py 와 같은 방식)
   -> 언리얼에서 이 뼈들의 이동 리타깃 = Skeleton(메시 기준 길이)이라 푸리나 애니메이션이 각 캐릭터 몸 비율로 재생됨.
 - 기본 상태에서 숨은 재질(확산 알파 0)과 반사 덧칠 층(이름 끝 '+', spa/sph 텍스처)은 뺌. 재질 슬롯 이름 = Mat00.. (언리얼 자산 이름용), 원래 이름·텍스처는 Data/class_<key>_build.json.
 preview: Data/class_<key>_{rest,bend}_{front,side}.png"""
import bpy, json, math, os, re, sys
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmx_reader import read_pmx

R0 = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
FUR = R0 + r'\FBX\Furina_cm.fbx'
SRC = R0 + r'\FBX\Classes\source'
CLASSES = {'officer': ('장교', 173.0), 'infantry': ('보병', 165.0), 'assault': ('돌격병', 184.0), 'antitank': ('대전차병', 125.0),
           'heavy': ('중화기병', 166.0), 'sniper': ('저격수', 163.0), 'armor': ('기갑병', 171.0),
           # 대일본제국(2026-11-22, 받은 압축 파일 이름의 키)
           'jp_officer': ('장교', 187.0), 'jp_infantry': ('보병', 186.0), 'jp_assault': ('돌격병', 166.0), 'jp_antitank': ('대전차병', 163.0),
           'jp_heavy': ('중화기병', 177.0), 'jp_sniper': ('저격수', 178.0), 'jp_armor': ('기갑병', 190.0)}
A = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['infantry']
KEY = A[0]; MODE = A[1] if len(A) > 1 else 'build'; H = CLASSES[KEY][1]
REP = {'key': KEY, 'class': CLASSES[KEY][0], 'height_cm': H}
PMX = max((os.path.join(r, f) for r, _, fs in os.walk(os.path.join(SRC, KEY)) for f in fs if f.lower().endswith('.pmx')), key=os.path.getsize)   # 소품 PMX(무기·차 등) 말고 캐릭터 본체
REP['pmx'] = os.path.relpath(PMX, R0)

# ---------------- MMD 표준 뼈 -> 푸리나 뼈
FIN = {'親指': ('Thumb', ['０', '１', '２']), '人指': ('IndexFinger', ['１', '２', '３']), '中指': ('MiddleFinger', ['１', '２', '３']),
       '薬指': ('RingFinger', ['１', '２', '３']), '小指': ('LittleFinger', ['１', '２', '３'])}
def mmd_to_furina(n):
    fixed = {'センター': 'Hips', 'グルーブ': 'Hips', '腰': 'Hips', '下半身': 'Hips', '上半身': 'Spine', '上半身2': 'Chest', '上半身３': 'Chest', '上半身3': 'Chest',
             '首': 'Neck', '頭': 'Head', '両目': 'Head', '全ての親': 'Hips', '操作中心': 'Hips'}
    if n in fixed: return fixed[n]
    side = 'Left' if n.startswith('左') else ('Right' if n.startswith('右') else None)
    if not side: return None
    c = n[1:]; s = 'L' if side == 'Left' else 'R'
    if c == '目': return 'Eye_' + s
    if c in ('肩', '肩P', '肩C'): return side + ' shoulder'
    if c in ('腕',) or c.startswith('腕捩'): return side + ' arm'
    if c in ('ひじ',) or c.startswith('手捩'): return side + ' elbow'
    if c in ('手首', '手先', 'ダミー'): return side + ' wrist'
    if c in ('足', '足D'): return side + ' leg'
    if c in ('ひざ', 'ひざD'): return side + ' knee'
    if c in ('足首', '足首D'): return side + ' ankle'
    if c in ('つま先', '足先EX', 'つま先D'): return side + ' toe'
    for jp, (base, digits) in FIN.items():
        if c.startswith(jp):
            d = c[len(jp):]
            if d in digits: return '%s%d_%s' % (base, digits.index(d) + (0 if base == 'Thumb' else 1), s)
            if d == '先': return '%s%d_%s' % (base, 2 if base == 'Thumb' else 3, s)
    return None

# ---------------- 푸리나 뼈대
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FUR, automatic_bone_orientation=False, ignore_leaf_bones=False)
FA = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]; FA.name = 'Armature'
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH': bpy.data.objects.remove(o, do_unlink=True)
FB = {b.name: (b.head_local.copy(), b.tail_local.copy(), b.parent.name if b.parent else None) for b in FA.data.bones}

# ---------------- PMX -> 메시(아마추어 로컬 cm: 왼쪽 +X, 앞 -Y, 위 +Z)
P = read_pmx(PMX)
V = P['verts'][:, [0, 2, 1]].astype(np.float64)     # (x, z, y): 왼손 -> 오른손, -Z 앞 -> -Y 앞
bones = P['bones']; bpos = np.array([b['pos'] for b in bones], np.float64)[:, [0, 2, 1]]
names = [b['name'] for b in bones]; bidx = {n: i for i, n in enumerate(names)}
# 면·재질(숨은 재질 제외)
faces = []; fmat = []; mats_used = []; start = 0
for mi, m in enumerate(P['materials']):
    F = P['faces'][start:start + m['face_count']]; start += m['face_count']
    if m['diffuse'][3] <= 0.001: continue
    tex = P['textures'][m['tex']] if 0 <= m['tex'] < len(P['textures']) else ''
    if m['name'].endswith('+') or re.search(r'(^|/)(spa|sph)[^/]*$', tex.lower()): continue   # MMD 반사 덧칠 층(髮+ 등): 불투명으로 그리면 머리가 검게 덮임
    slot = len(mats_used); mats_used.append(mi)
    faces.extend(F[:, ::-1].tolist()); fmat.extend([slot] * len(F))
used_v = np.unique(np.array(faces).ravel())
# 키: 의상 포함 맨 위
EXCL = re.compile(r'(?!x)x')   # 키는 의상(모자·리본 등) 포함 높이(사용자 지정, 2026-11-22) -> 빼는 재질 없음
vmat = {}
for f, s in zip(faces, fmat):
    for v in f: vmat.setdefault(v, s)
body_v = np.array([v for v in used_v if not EXCL.search(P['materials'][mats_used[vmat[v]]]['name'])])
zmin = V[used_v, 2].min(); ztop = V[body_v, 2].max(); k = H / (ztop - zmin)
V = (V - np.array([0, 0, zmin])) * k; bpos = (bpos - np.array([0, 0, zmin])) * k
cx = 0.5 * (bpos[bidx['左足'], 0] + bpos[bidx['右足'], 0]); V[:, 0] -= cx; bpos[:, 0] -= cx     # 좌우 가운데
REP.update(scale=k, mmd_height_units=float(ztop - zmin), excluded_materials=[P['materials'][i]['name'] for i in mats_used if EXCL.search(P['materials'][i]['name'])])
# 사용하는 정점만 남기기
remap = -np.ones(len(V), np.int64); remap[used_v] = np.arange(len(used_v))
me = bpy.data.meshes.new('Body'); me.from_pydata([tuple(c) for c in V[used_v]], [], [tuple(remap[f]) for f in faces]); me.update()
uvl = me.uv_layers.new(name='UVMap'); UV = P['uvs'][used_v]
lv = np.zeros(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
uvs = np.stack([UV[lv, 0], 1.0 - UV[lv, 1]], 1).ravel(); uvl.data.foreach_set('uv', uvs)
for s, mi in enumerate(mats_used):
    mm = bpy.data.materials.new('Mat%02d' % s); me.materials.append(mm)
me.polygons.foreach_set('material_index', np.array(fmat, np.int32)); me.polygons.foreach_set('use_smooth', np.ones(len(fmat), bool))
body = bpy.data.objects.new('Body', me); bpy.context.scene.collection.objects.link(body)
REP['materials'] = [{'slot': 'Mat%02d' % s, 'name': P['materials'][mi]['name'], 'texture': (P['textures'][P['materials'][mi]['tex']] if 0 <= P['materials'][mi]['tex'] < len(P['textures']) else None),
                     'diffuse': [round(c, 3) for c in P['materials'][mi]['diffuse']]} for s, mi in enumerate(mats_used)]
REP['textures_dir'] = os.path.relpath(os.path.dirname(PMX), R0)
# 가중치
cache = {}
def resolve(i):
    if i in cache: return cache[i]
    j = i; out = None
    while j is not None and j >= 0:
        out = mmd_to_furina(names[j])
        if out and out in FB: break
        out = None; j = bones[j]['parent']
    cache[i] = out or 'Hips'; return cache[i]
groups = {}
unm = {}
for new_i, old_i in enumerate(used_v):
    acc = {}
    for bi, w in P['weights'][old_i]:
        if bi < 0 or w <= 0: continue
        t = resolve(bi); acc[t] = acc.get(t, 0.0) + w
        if mmd_to_furina(names[bi]) is None: unm[names[bi]] = t
    top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; tot = sum(w for _, w in top) or 1.0
    for n, w in top:
        if n not in groups: groups[n] = body.vertex_groups.new(name=n)
        groups[n].add([new_i], w / tot, 'REPLACE')
REP['n_unmapped_bones'] = len(unm); REP['unmapped_sample'] = dict(list(unm.items())[:40]); REP['groups'] = sorted(groups)

# ---------------- 관절(PMX 뼈 위치)
def bp(n): return Vector(bpos[bidx[n]].tolist())
def first(*ns):
    for n in ns:
        if n in bidx: return bp(n)
    raise KeyError(ns)
J = {}
legmid = 0.5 * (first('左足D', '左足') + first('右足D', '右足'))
J['Hips'] = legmid + Vector((0, 0, 0.02 * H)); J['Spine'] = bp('上半身'); J['Chest'] = first('上半身2', '上半身3') if ('上半身2' in bidx or '上半身3' in bidx) else J['Spine'].lerp(bp('首'), 0.5)
if J['Spine'].z <= J['Hips'].z + 1: J['Spine'] = J['Hips'].lerp(bp('首'), 0.2)
J['Neck'] = bp('首'); J['Head'] = bp('頭'); J['Head_tail'] = Vector((J['Head'].x, J['Head'].y, H))
CHILD = {'Hips': 'Spine', 'Spine': 'Chest', 'Chest': 'Neck', 'Neck': 'Head', 'Head': 'Head_tail'}
for side, jp, s in (('Left', '左', 'L'), ('Right', '右', 'R')):
    J[side + ' shoulder'] = bp(jp + '肩'); J[side + ' arm'] = bp(jp + '腕'); J[side + ' elbow'] = bp(jp + 'ひじ'); J[side + ' wrist'] = bp(jp + '手首')
    J[side + ' leg'] = first(jp + '足D', jp + '足'); J[side + ' knee'] = first(jp + 'ひざD', jp + 'ひざ'); J[side + ' ankle'] = first(jp + '足首D', jp + '足首')
    tip = first(jp + '足先EX', jp + 'つま先'); ank = J[side + ' ankle']
    J[side + ' toe'] = Vector((ank.x + 0.6 * (tip.x - ank.x), ank.y + 0.6 * (tip.y - ank.y), max(tip.z, 0.02 * H)))
    J[side + ' toe_tail'] = Vector((tip.x, tip.y, max(tip.z, 0.02 * H)))
    CHILD.update({side + ' shoulder': side + ' arm', side + ' arm': side + ' elbow', side + ' elbow': side + ' wrist', side + ' leg': side + ' knee',
                  side + ' knee': side + ' ankle', side + ' ankle': side + ' toe', side + ' toe': side + ' toe_tail'})
    mids = []
    for jpf, (base, digits) in FIN.items():
        chain = [jp + jpf + d for d in digits if jp + jpf + d in bidx]
        fur = ['%s%d_%s' % (base, i + (0 if base == 'Thumb' else 1), s) for i in range(len(digits))]
        if len(chain) < 3: continue
        tipn = jp + jpf + '先'
        for i, (mn, fn) in enumerate(zip(chain, fur)):
            J[fn] = bp(mn)
            if i < 2: CHILD[fn] = fur[i + 1]
            else:
                J[fn + '_tail'] = bp(tipn) if tipn in bidx else bp(mn) + (bp(mn) - bp(chain[1])) * 0.8; CHILD[fn] = fn + '_tail'
        mids.append(J[fur[0]])
    J[side + ' wrist_tail'] = sum(mids, Vector()) / len(mids) if mids else J[side + ' wrist'] + (J[side + ' wrist'] - J[side + ' elbow']) * 0.4
    CHILD[side + ' wrist'] = side + ' wrist_tail'
BODY = [n for n in CHILD if n in FB]
REP['joints'] = {n: [round(c, 2) for c in J[n]] for n in BODY}

# ---------------- 임시 뼈대(모델 자세) + 원래 가중치 -> 뼈 방향을 푸리나 방향으로 굳힘
def body_anc(n):
    while n and n not in BODY: n = FB[n][2]
    return n
tmp = bpy.data.objects.new('Tmp', bpy.data.armatures.new('Tmp')); bpy.context.scene.collection.objects.link(tmp)
bpy.context.view_layer.objects.active = tmp; bpy.ops.object.mode_set(mode='EDIT')
for n in BODY:
    eb = tmp.data.edit_bones.new(n); eb.head = J[n]; eb.tail = J[CHILD[n]]
    if (eb.tail - eb.head).length < 0.05: eb.tail = eb.head + Vector((0, 0, 1))
extra = [g for g in groups if g not in BODY]
for n in extra:   # 눈 등 몸 뼈가 아닌 그룹: 몸 조상에 붙은 짧은 뼈(조상과 같이 움직임)
    a = body_anc(n); eb = tmp.data.edit_bones.new(n); eb.head = J[a]; eb.tail = J[a] + Vector((0, 0, 1))
for n in BODY + extra:
    p = FB[n][2] if n in BODY else body_anc(n)
    while p and p not in BODY: p = FB[p][2]
    if p and n != p: tmp.data.edit_bones[n].parent = tmp.data.edit_bones[p]
bpy.ops.object.mode_set(mode='OBJECT')
body.parent = tmp; mod = body.modifiers.new('Arm', 'ARMATURE'); mod.object = tmp
bpy.context.view_layer.objects.active = tmp; bpy.ops.object.mode_set(mode='POSE')
def depth(n):
    d = 0
    while FB[n][2] in BODY: n = FB[n][2]; d += 1
    return d
for n in sorted(BODY, key=depth):
    pb = tmp.pose.bones[n]; bpy.context.view_layer.update()
    h = pb.head.copy(); cur = (pb.tail - pb.head).normalized(); want = (FB[n][1] - FB[n][0]).normalized()
    pb.matrix = Matrix.Translation(h) @ cur.rotation_difference(want).to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix
bpy.context.view_layer.update()
posed = {n: (tmp.pose.bones[n].head.copy(), tmp.pose.bones[n].tail.copy()) for n in BODY}
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = body; bpy.ops.object.modifier_apply(modifier=mod.name)
body.parent = None; body.matrix_world = Matrix.Identity(4); bpy.data.objects.remove(tmp, do_unlink=True)
REP['dir_err_deg_max'] = round(max(math.degrees((posed[n][1] - posed[n][0]).angle(FB[n][1] - FB[n][0])) for n in BODY), 3)

# ---------------- 최종 뼈대 = 푸리나 뼈대, 몸·손가락 뼈 머리만 모델 관절로, 나머지는 몸 조상과 평행 이동
bpy.context.view_layer.objects.active = FA; bpy.ops.object.mode_set(mode='EDIT')
ebs = FA.data.edit_bones
for eb in ebs: eb.use_connect = False
delta = {}
for n in BODY:
    h, t = posed[n]; eb = ebs[n]; ln = max((t - h).length, 0.3)
    eb.head = h; eb.tail = h + (FB[n][1] - FB[n][0]).normalized() * ln; delta[n] = h - FB[n][0]
for eb in ebs:
    if eb.name in BODY: continue
    dv = delta.get(body_anc(eb.name), Vector((0, 0, 0))); eb.head = FB[eb.name][0] + dv; eb.tail = FB[eb.name][1] + dv
bpy.ops.object.mode_set(mode='OBJECT')
body.parent = FA; body.matrix_parent_inverse = Matrix.Identity(4)
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = FA
for o in list(bpy.context.scene.objects):
    if o.type == 'EMPTY': bpy.data.objects.remove(o, do_unlink=True)
FA.scale = (1, 1, 1); bpy.context.scene.unit_settings.scale_length = 0.01
REP['body_bones'] = BODY; REP['verts'] = len(me.vertices)

if MODE == 'preview':
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = 700; sc.render.resolution_y = 1000
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'; sc.world = bpy.data.worlds.new('w')
    tdir = os.path.dirname(PMX)
    for s, info in enumerate(REP['materials']):
        mm = body.data.materials[s]; mm.use_nodes = True; nt = mm.node_tree
        if info['texture'] and os.path.exists(os.path.join(tdir, info['texture'])):
            tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(os.path.join(tdir, info['texture']))
            nt.links.new(tx.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(H, 120) * 1.15; cam.data.clip_end = 5000
    def shoot(name, d):
        look = Vector((0, 0, H * 0.5)); cam.location = look - d * 1000; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = R0 + rf'\Data\class_{KEY}_{name}.png'; bpy.ops.render.render(write_still=True)
    shoot('rest_front', Vector((0, 1, 0))); shoot('rest_side', Vector((-1, 0, 0)))
    bpy.context.view_layer.objects.active = FA; bpy.ops.object.mode_set(mode='POSE')
    def rot(n, axis, deg):
        pb = FA.pose.bones[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = Vector([math.radians(deg) if a == axis else 0 for a in 'XYZ'])
    rot('Left elbow', 'X', 70); rot('Right elbow', 'X', 70); rot('Left knee', 'X', -60); rot('Left leg', 'X', 50); rot('Right arm', 'Z', 40); rot('Head', 'Z', 30)
    for f in ('IndexFinger1_L', 'MiddleFinger1_L', 'RingFinger1_L', 'LittleFinger1_L'): rot(f, 'X', 60)
    bpy.ops.object.mode_set(mode='OBJECT'); bpy.context.view_layer.update()
    shoot('bend_front', Vector((0, 1, 0)))
else:
    for o in bpy.context.scene.objects: o.select_set(o.type in ('ARMATURE', 'MESH'))
    bpy.context.view_layer.objects.active = FA
    os.makedirs(R0 + r'\FBX\Classes', exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=R0 + rf'\FBX\Classes\{KEY}_cm.fbx', use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False, bake_anim=False,
                             use_armature_deform_only=False, mesh_smooth_type='FACE', use_mesh_modifiers=False, path_mode='STRIP', primary_bone_axis='Y', secondary_bone_axis='X',
                             axis_forward='-Z', axis_up='Y', apply_scale_options='FBX_SCALE_NONE', global_scale=1.0)
    REP['exported'] = rf'FBX\Classes\{KEY}_cm.fbx'
json.dump(REP, open(R0 + rf'\Data\class_{KEY}_build.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('CLASS_BUILD_DONE', KEY, MODE, 'k=%.3f' % k, 'dir_err', REP['dir_err_deg_max'], 'unmapped', REP['n_unmapped_bones'])
