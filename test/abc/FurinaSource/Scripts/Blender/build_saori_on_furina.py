"""Blender headless: builds FBX/Saori/Saori_cm.fbx = Joumae Saori's meshes skinned to the FURINA skeleton (same 240 bones, names, hierarchy and bind pose as FBX/Furina_cm.fbx) so that SK_Furina_Skeleton,
the retargeted animations, ABP_Furina and CR_FurinaSecondary keep working unchanged.
 1. import Furina_cm.fbx (armature FA, meshes removed) and Saori's FBX (armature SA, 36 mesh objects, MMD bones)
 2. similarity fit (uniform scale + translation) of Saori's joints onto Furina's joints (hips/spine/chest/neck/head, legs, arms): residuals are printed
 3. every Saori vertex group is merged into a Furina bone (MMD name -> Furina name table; unknown bones -> nearest mapped ancestor), max 4 influences, normalized
 4. all meshes are fitted, joined into one mesh 'Body', parented to FA with an Armature modifier and exported like blender_export_cm.py (cm units, FBX_SCALE_NONE)
Reports -> Data/saori_build.json. Usage: blender.exe -b -P build_saori_on_furina.py"""
import bpy, json, math, os, shutil, re
from mathutils import Vector, Matrix
R0 = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
FUR = R0 + r'\FBX\Furina_cm.fbx'
SAO = r'C:\Users\fromj\Downloads\joumae-saori\source\Joumae Saori From Blue Archive\Joumae Saori.fbx'
OUTDIR = R0 + r'\FBX\Saori'; os.makedirs(OUTDIR, exist_ok=True)
REP = {}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FUR, automatic_bone_orientation=False, ignore_leaf_bones=False)
FA = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]; FA.name = 'Armature'
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH': bpy.data.objects.remove(o, do_unlink=True)
before = set(bpy.context.scene.objects)
bpy.ops.import_scene.fbx(filepath=SAO)
new = [o for o in bpy.context.scene.objects if o not in before]
SA = [o for o in new if o.type == 'ARMATURE'][0]; SA.name = 'SaoriArmature'
meshes = [o for o in new if o.type == 'MESH']
bpy.context.view_layer.update()
def wpos(arm, bone, tail=False):
    b = arm.data.bones[bone]; return arm.matrix_world @ (b.tail_local if tail else b.head_local)
# ---------- joint pairs (Saori bone, Furina bone)
PAIRS = [('腰', 'Hips'), ('上半身', 'Spine'), ('上半身2', 'Chest'), ('首', 'Neck'), ('頭', 'Head'), ('左足', 'Left leg'), ('右足', 'Right leg'), ('左ひざ', 'Left knee'), ('右ひざ', 'Right knee'),
         ('左肩', 'Left shoulder'), ('右肩', 'Right shoulder'), ('左腕', 'Left arm'), ('右腕', 'Right arm'), ('左ひじ', 'Left elbow'), ('右ひじ', 'Right elbow'), ('左手首', 'Left wrist'), ('右手首', 'Right wrist')]
S = [wpos(SA, a) for a, b in PAIRS]; F = [wpos(FA, b) for a, b in PAIRS]
# least squares uniform scale + translation (no rotation: both face -Y, Z up)
sc = Vector((0, 0, 0)); fc = Vector((0, 0, 0))
for s, f in zip(S, F): sc += s; fc += f
sc /= len(S); fc /= len(F)
num = sum(((f - fc).dot(s - sc)) for s, f in zip(S, F)); den = sum(((s - sc).dot(s - sc)) for s in S); k = num / den
T = Matrix.Translation(fc - sc * k) @ Matrix.Scale(k, 4)   # world_F = k * (world_S - sc) + fc
res = {PAIRS[i][1]: round((T @ S[i] - F[i]).length * 100, 2) for i in range(len(S))}   # centimetres (Furina world is metres)
REP['scale_k'] = k; REP['joint_residual_cm'] = res
# feet: lowest Saori vertex after the fit should sit on z = 0
lo = 1e9; hi = -1e9
for o in meshes:
    if o.name == 'Halo': continue
    for v in o.data.vertices:
        z = (T @ (o.matrix_world @ v.co)).z; lo = min(lo, z); hi = max(hi, z)
REP['fit_height_m'] = [lo, hi]
# ---------- weight remap
FUR_BONES = set(b.name for b in FA.data.bones)
def f_name(side, base):
    n = ('Left ' if side == 'L' else 'Right ') + base; return n if n in FUR_BONES else None
def map_bone(jp):
    """Saori (MMD) bone name -> Furina bone name or None"""
    side = 'L' if jp.startswith('左') else ('R' if jp.startswith('右') else None); core = jp[1:] if side else jp
    fixed = {'センター': 'Hips', 'グルーブ': 'Hips', '腰': 'Hips', '下半身': 'Hips', '上半身': 'Spine', '上半身2': 'Chest', '首': 'Neck', '頭': 'Head', 'ヘッドセット': 'Head', 'メガネ': 'Head', 'halo': 'Head',
             '腰キャンセル左': 'Hips', '腰キャンセル右': 'Hips', '膣ダミー': 'Hips', '全ての親': 'Hips', '首輪': 'Neck', '両目': 'Head', '舌１': 'Head', '舌２': 'Head', '舌３': 'Head'}
    if jp in fixed: return fixed[jp]
    if not side: return None
    if core in ('目',): return 'Eye_L' if side == 'L' else 'Eye_R'
    if core.startswith('乳'): return 'Chest'
    if core in ('肩', '肩P', '肩C', '肩+'): return f_name(side, 'shoulder')
    if core in ('腕', '腕+'): return f_name(side, 'arm')
    if core.startswith('腕捩'): return 'zArmTwist_' + side
    if core in ('ひじ', 'ひじ+'): return f_name(side, 'elbow')
    if core.startswith('手捩'): return 'zHandTwist_' + side
    if core in ('手首', '手首+', '手先', 'ダミー', '握り', '拡散'): return f_name(side, 'wrist')
    if core in ('足', '足D'): return f_name(side, 'leg')
    if core in ('ひざ', 'ひざD'): return f_name(side, 'knee')
    if core in ('足首', '足首D'): return f_name(side, 'ankle')
    if core in ('つま先', '足先EX'): return f_name(side, 'toe')
    m = re.match(r'(親指|人指|人差指|中指|薬指|小指)([０-９0-9]?)', core)
    if m:
        fn = {'親指': 'Thumb', '人指': 'IndexFinger', '人差指': 'IndexFinger', '中指': 'MiddleFinger', '薬指': 'RingFinger', '小指': 'LittleFinger'}[m.group(1)]
        idx = (m.group(2) or '3').translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        if m.group(1) == '親指': idx = str(min(int(idx), 2))
        elif idx == '0': idx = '1'
        nm = '%s%s_%s' % (fn, idx, side); return nm if nm in FUR_BONES else None
    if core in ('握', '指握', '人指握', '中指握', '薬指握', '小指握', '親指握'): return f_name(side, 'wrist')
    return None
parent = {b.name: (b.parent.name if b.parent else None) for b in SA.data.bones}
cache = {}
def resolve(jp):
    if jp in cache: return cache[jp]
    cur = jp; out = None
    while cur:
        out = map_bone(cur)
        if out: break
        cur = parent.get(cur)
    out = out or 'Hips'
    if out not in FUR_BONES: out = 'Hips'
    cache[jp] = out; return out
unmapped = {}
for o in meshes:
    names = {vg.index: vg.name for vg in o.vertex_groups}
    for n in names.values():
        r = resolve(n)
        if map_bone(n) is None: unmapped[n] = r
REP['unmapped_to_ancestor'] = {k_: v for k_, v in list(unmapped.items())[:80]}; REP['n_unmapped'] = len(unmapped)
# ---------- fit + remap each mesh, then join
FINV = FA.matrix_world.inverted()
for o in meshes:
    bpy.context.view_layer.objects.active = o
    names = {vg.index: vg.name for vg in o.vertex_groups}
    weights = []
    for v in o.data.vertices:
        acc = {}
        for g in v.groups:
            if g.weight <= 0: continue
            tgt = resolve(names[g.group]); acc[tgt] = acc.get(tgt, 0.0) + g.weight
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; tot = sum(w for _, w in top) or 1.0
        weights.append([(n, w / tot) for n, w in top])
    mw = o.matrix_world.copy()
    for v in o.data.vertices: v.co = FINV @ (T @ (mw @ v.co))
    # drop old parent / modifiers / groups, set transform identity (vertices are now in Furina armature-local space)
    for m in list(o.modifiers): o.modifiers.remove(m)
    o.parent = None; o.matrix_world = Matrix.Identity(4)
    for vg in list(o.vertex_groups): o.vertex_groups.remove(vg)
    groups = {}
    for i, ws in enumerate(weights):
        for n, w in ws:
            if n not in groups: groups[n] = o.vertex_groups.new(name=n)
            groups[n].add([i], w, 'REPLACE')
# the fitted vertex coordinates are in Furina armature-local units (cm); FA is scaled 0.01 -> parent with identity inverse and give the mesh the armature's scale
for o in bpy.context.scene.objects: o.select_set(False)
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active; body.name = 'Body'
body.data.name = 'Body'
body.parent = FA; body.matrix_parent_inverse = Matrix.Identity(4)
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = FA
bpy.data.objects.remove(SA, do_unlink=True)
for o in list(bpy.context.scene.objects):
    if o.type == 'EMPTY': bpy.data.objects.remove(o, do_unlink=True)
# body verts are in cm (armature local); FA.scale = 0.01 in the imported file, the cm export wants scale 1
FA.scale = (1, 1, 1); bpy.context.scene.unit_settings.scale_length = 0.01
bb = [body.matrix_world @ Vector(c) for c in body.bound_box]
REP['body_bbox_cm'] = [[round(min(v[i] for v in bb), 2) for i in range(3)], [round(max(v[i] for v in bb), 2) for i in range(3)]]
REP['materials'] = [m.name if m else None for m in body.data.materials]; REP['verts'] = len(body.data.vertices); REP['groups'] = len(body.vertex_groups)
# textures next to the FBX
imgs = {}
for m in body.data.materials:
    if not m or not m.use_nodes: continue
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image: imgs.setdefault(m.name, []).append(n.image.filepath or n.image.name)
REP['material_images'] = imgs
for o in bpy.context.scene.objects: o.select_set(o.type in ('ARMATURE', 'MESH'))
bpy.context.view_layer.objects.active = FA
bpy.ops.export_scene.fbx(filepath=OUTDIR + r'\Saori_cm.fbx', use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False, bake_anim=False, use_armature_deform_only=False,
                         mesh_smooth_type='FACE', use_mesh_modifiers=False, path_mode='STRIP', primary_bone_axis='Y', secondary_bone_axis='X', axis_forward='-Z', axis_up='Y',
                         apply_scale_options='FBX_SCALE_NONE', global_scale=1.0)
json.dump(REP, open(R0 + r'\Data\saori_build.json', 'w'), indent=1, ensure_ascii=False); print('SAORI_BUILD_DONE', k, res)
