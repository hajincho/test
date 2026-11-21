"""blender -b --python de_weapons_build.py -- <stage: preview|export> [무기키,...]
 독일 무기 원본(Downloads/FurinaWeaponSrc/Germany) -> 정리(바닥/카메라/조명/탄띠 제거) -> 한 메시로 합치기 -> 방향(총구 Blender -Y = UE +Y, 위 +Z) -> 실제 전장 길이로 축척.
 preview: 무기별 옆/위/뒤 렌더 -> Data/de_prev_<키>.png      export: FBX/Germany/SM_DE_<키>.fbx + Data/de_weapons_build.json(머티리얼별 텍스처 경로)
 방향 보정은 ORIENT[키] = (먼저 적용할 회전 오일러 XYZ 도) - preview 를 보고 정함."""
import bpy, bmesh, json, os, glob, math, sys, re
import numpy as np
import xml.etree.ElementTree as ET
from mathutils import Matrix, Vector, Euler
A = sys.argv[sys.argv.index('--') + 1:]; STAGE = A[0]; ONLY = A[1].split(',') if len(A) > 1 and A[1] else None
SRC = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany'; D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
EXP = SRC + r'\_export'; os.makedirs(EXP, exist_ok=True)
# 키: (원본, 텍스처 폴더, 실제 최장 길이 m, 제거할 메시 이름 정규식, 제거할 머티리얼 정규식)
W = {
 'p38': ('p38/source/Walther_P38+SatinFloor.fbx', 'p38/textures', 0.216, None, 'SatinFloor|Bullet'),
 'p08': ('p08/source/model_unzipped/model/model.dae', 'p08/textures', 0.222, None, None),
 'pp': ('pp/source/walther_pp_unzipped/walther_pp.obj', 'pp/textures', 0.170, None, None),
 'kar98k': ('kar98k/source/model_unzipped/model/model.dae', 'kar98k/textures', 1.110, r'^p_low', None),
 'g43': ('g43/source/Gewehr43.fbx', 'g43/textures', 1.130, None, None),
 'stg44': ('stg44/source/STG44_Full.fbx', 'stg44/textures', 0.940, None, None),
 'mp40': ('mp40/source/MP40_unzipped/MP40/MP40.fbx', 'mp40/textures', 0.833, r'^(Mag|bullet)$', None),   # 원본 탄창이 옆에 45도로 따로 놓여 있어 제외
 'mp38': ('mp38/MP38_Rosewood_Metal060B.fbx', 'mp38/textures', 0.630, None, None),   # 개머리판 접힘 상태
 'mg42': ('mg42/source/MG 42.fbx', 'mg42/textures', 1.220, r'BezierCurve|Plane\.006', None),   # 탄띠/판 제거
 'mg34': ('mg34/source/mg 34 full tex.blend', 'mg34/textures', 1.219, r'inf lent', None),
 'panzerfaust': ('panzerfaust/source/model_unzipped/model/model.dae', 'panzerfaust/textures', 1.045, None, None),
 'panzerschreck': ('panzerschreck/source/model_unzipped/model/model.dae', 'panzerschreck/textures', 1.640, None, None),
 'panzerschreck_rocket': ('panzerschreck/Panzerschreck_Rocket/Panzerschreck_Rocket.fbx', 'panzerschreck/Panzerschreck_Rocket/textures', 0.650, None, None),
 'pzb39': ('PzB39/PzB39_Colored.fbx', 'PzB39/textures', 1.620, None, None),
 'grw34': ('grw34/source/Blender_unzipped/sgw34.blend', 'grw34/textures', 1.100, r'^a$', None),   # 'a' = 4m 장식 고리
 'mortar_shell': ('Mortar_Shell/source/ArtilleryShell.fbx', None, 0.330, None, None),
 'zf4': ('zf4_scope/ZF4_scope_with_mount.fbx', 'zf4_scope/textures', 0.270, None, None),
 'zf39': ('zf39_scope/main_view.stl', None, 0.280, None, None),   # 조립된 전체 모델만
 'zf41': ('zf41_scope/new ZF41/*.stl', None, 0.130, None, None),
 'ammo_7_92x94': ('7_92x94_ammo/Patronen_painted.fbx', '7_92x94_ammo/textures', 0.1175, None, None),
 'mauser_clip': ('mauser_ammo_clip/source/bullet2.blend', None, 0.082, None, None),
}
ORIENT = json.load(open(D + r'\Data\de_weapons_orient.json')) if os.path.exists(D + r'\Data\de_weapons_orient.json') else {}
def load_dae(path):
    ns = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}; root = ET.parse(path).getroot()
    unit = float(root.find('c:asset/c:unit', ns).get('meter', '1')) if root.find('c:asset/c:unit', ns) is not None else 1.0
    up = (root.find('c:asset/c:up_axis', ns).text if root.find('c:asset/c:up_axis', ns) is not None else 'Y_UP')
    mats = {m.get('id'): m.get('name') or m.get('id') for m in root.iter('{%s}material' % ns['c'])}
    geoms = {}
    for g in root.iter('{%s}geometry' % ns['c']):
        mesh = g.find('c:mesh', ns)
        src = {}
        for s in mesh.findall('c:source', ns):
            fa = s.find('c:float_array', ns); acc = s.find('c:technique_common/c:accessor', ns)
            src[s.get('id')] = np.array(fa.text.split(), float).reshape(-1, int(acc.get('stride')))
        vmap = {}
        for v in mesh.findall('c:vertices', ns):
            for i in v.findall('c:input', ns):
                if i.get('semantic') == 'POSITION': vmap[v.get('id')] = i.get('source')[1:]
        parts = []
        for pl in mesh.findall('c:polylist', ns) + mesh.findall('c:triangles', ns):
            ins = [(i.get('semantic'), i.get('source')[1:], int(i.get('offset')), i.get('set')) for i in pl.findall('c:input', ns)]
            stride = max(o for _, _, o, _ in ins) + 1
            p = np.array(pl.find('c:p', ns).text.split(), int).reshape(-1, stride)
            vc = np.array(pl.find('c:vcount', ns).text.split(), int) if pl.find('c:vcount', ns) is not None else np.full(len(p) // 3, 3)
            parts.append((pl.get('material'), ins, p, vc))
        geoms[g.get('id')] = (src, vmap, parts)
    def mk(gid, M, mbind, name):
        src, vmap, parts = geoms[gid]
        verts = None; faces = []; uvs = []; fmat = []; matnames = []
        for mat_sym, ins, p, vc in parts:
            vin = [x for x in ins if x[0] == 'VERTEX'][0]; uvin = [x for x in ins if x[0] == 'TEXCOORD']
            P = src[vmap[vin[1]]][:, :3]; verts = P
            mname = mats.get(mbind.get(mat_sym, ''), mat_sym or 'Mat')
            if mname not in matnames: matnames.append(mname)
            k = 0
            for n in vc:
                idx = p[k:k + n]; faces.append(list(idx[:, vin[2]]))
                if uvin: T = src[uvin[0][1]]; uvs.append([tuple(T[j][:2]) for j in idx[:, uvin[0][2]]])
                else: uvs.append([(0, 0)] * n)
                fmat.append(matnames.index(mname)); k += n
        me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
        uvl = me.uv_layers.new(name='UVMap')
        li = 0
        for pi, poly in enumerate(me.polygons):
            for j, l in enumerate(poly.loop_indices): uvl.data[l].uv = uvs[pi][j]
        for mn in matnames:
            m = bpy.data.materials.get(mn) or bpy.data.materials.new(mn); me.materials.append(m)
        for pi, poly in enumerate(me.polygons): poly.material_index = fmat[pi]
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = M
        for poly in me.polygons: poly.use_smooth = True
    conv = Matrix.Rotation(math.radians(90), 4, 'X') if up == 'Y_UP' else Matrix.Identity(4)
    def walk(node, parentM):
        m = node.find('c:matrix', ns)
        L = Matrix(np.array(m.text.split(), float).reshape(4, 4).tolist()) if m is not None else Matrix.Identity(4)
        M = parentM @ L
        for ig in node.findall('c:instance_geometry', ns):
            mb = {im.get('symbol'): im.get('target')[1:] for im in ig.iter('{%s}instance_material' % ns['c'])}
            mk(ig.get('url')[1:], M, mb, node.get('name') or node.get('id'))
        for ch in node.findall('c:node', ns): walk(ch, M)
    base = conv @ Matrix.Scale(unit, 4)
    for vs in root.iter('{%s}visual_scene' % ns['c']):
        for n in vs.findall('c:node', ns): walk(n, base)
ONE_CLUSTER = {'p38', 'kar98k'}; PCA_KEYS = {'p38'}; KEEP_UP = {'grw34'}
def keep_one_cluster(ob, mode='touch'):
    # 떨어진 부품(섬)들을 경계상자 겹침으로 묶어 정점이 가장 많은 묶음만 남김 (같은 장면에 총이 여러 자루일 때)
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); seen = set(); isl = []
    for v in bm.verts:
        if v.index in seen: continue
        stack = [v]; comp = []; seen.add(v.index)
        while stack:
            x = stack.pop(); comp.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); stack.append(y)
        isl.append(comp)
    co = np.array([v.co[:] for v in bm.verts]); diag = float(np.linalg.norm(co.max(0) - co.min(0))); r = diag * 0.003
    lab = np.zeros(len(co), int)
    for k, c in enumerate(isl): lab[c] = k
    from mathutils.kdtree import KDTree
    kd = KDTree(len(co))
    for i, p_ in enumerate(co): kd.insert(p_, i)
    kd.balance(); par = list(range(len(isl)))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    if mode == 'touch':
        for i in range(0, len(co), 3):   # 닿아 있는(가까운) 섬끼리만 묶기
            for (_, j, _) in kd.find_range(co[i], r):
                a_, b_ = f(lab[i]), f(lab[j])
                if a_ != b_: par[a_] = b_
    else:   # 경계상자가 25% 이상 겹치면 묶기
        pad = diag * 0.004; bb = [(co[c].min(0) - pad, co[c].max(0) + pad) for c in isl]
        for i in range(len(isl)):
            for j in range(i + 1, len(isl)):
                lo = np.maximum(bb[i][0], bb[j][0]); hi = np.minimum(bb[i][1], bb[j][1])
                if np.all(lo < hi) and np.prod(hi - lo) >= 0.25 * min(np.prod(bb[i][1] - bb[i][0]), np.prod(bb[j][1] - bb[j][0])): par[f(i)] = f(j)
    groups = {}
    for i, c in enumerate(isl): groups.setdefault(f(i), []).extend(c)
    best = max(groups.values(), key=len); keep = set(best)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS'); bm.to_mesh(ob.data); bm.free(); ob.data.update()
    return [len(g) for g in sorted(groups.values(), key=len, reverse=True)][:6]
def load(key):
    rel = W[key][0]; paths = sorted(glob.glob(os.path.join(SRC, rel)))
    for p in paths:
        ext = p.lower().rsplit('.', 1)[1]
        if ext == 'fbx': bpy.ops.import_scene.fbx(filepath=p, use_anim=False)
        elif ext == 'obj': bpy.ops.wm.obj_import(filepath=p)
        elif ext == 'stl': bpy.ops.wm.stl_import(filepath=p)
        elif ext == 'dae': load_dae(p)
        elif ext == 'blend':
            with bpy.data.libraries.load(p, link=False) as (src, dst): dst.objects = list(src.objects)
            for o in dst.objects:
                if o is not None: bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update()
def build(key):
    bpy.ops.wm.read_factory_settings(use_empty=True); load(key)
    _, texdir, real, drop_mesh, drop_mat = W[key]; info = {'key': key}
    # 메시 아닌 것, 제거 대상 메시 삭제 (부모 변환은 적용)
    for o in list(bpy.context.scene.objects):
        if o.type == 'MESH':
            o.matrix_world = o.matrix_world.copy()
    for o in list(bpy.context.scene.objects):
        if o.type == 'MESH': o.parent = None if False else o.parent
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in list(bpy.context.scene.objects):
        if o.type != 'MESH' or (drop_mesh and re.search(drop_mesh, o.name)): bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:   # 애니메이션/서브디비전 제거, 셰이프키 제거
        o.animation_data_clear()
        for md in list(o.modifiers):
            if md.type == 'SUBSURF': o.modifiers.remove(md)
        if o.data.shape_keys: o.shape_key_clear()
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if any(o.modifiers for o in meshes): bpy.ops.object.convert(target='MESH')
    bpy.ops.object.make_single_user(object=True, obdata=True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = 'SM_DE_' + key
    if drop_mat:   # 특정 머티리얼 면 제거(바닥 등)
        idx = [i for i, s in enumerate(ob.material_slots) if s.material and re.search(drop_mat, s.material.name)]
        bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in idx], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(ob.data); bm.free(); info['dropped_mat'] = len(idx)
    if key in ONE_CLUSTER: info['clusters'] = keep_one_cluster(ob, 'touch' if key == 'p38' else 'bbox')
    co = np.array([v.co[:] for v in ob.data.vertices]); size = co.max(0) - co.min(0); info['raw_size'] = size.round(4).tolist()
    # 자동 방향: 최장축 -> Y, 두번째 -> Z(높이)   (이후 ORIENT 로 앞뒤/위아래 보정).  PCA 대상은 주성분 축 사용, KEEP_UP 은 원래 Z(위) 유지
    if key in PCA_KEYS:
        c0 = co.mean(0); U, S_, Vt = np.linalg.svd(co - c0, full_matrices=False); R = np.zeros((3, 3)); R[1] = Vt[0]; R[2] = Vt[1]; R[0] = np.cross(Vt[1], Vt[0])
        if np.linalg.det(R) < 0: R[0] = -R[0]
    elif key in KEEP_UP:
        R = np.eye(3) if size[1] >= size[0] else np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1.0]])
    else:
        order = np.argsort(-size); ax_long, ax_mid, ax_short = order
        R = np.zeros((3, 3)); R[1, ax_long] = 1; R[2, ax_mid] = 1; R[0, ax_short] = 1
        if np.linalg.det(R) < 0: R[0, ax_short] = -1
    M = Matrix(R.tolist()).to_4x4()
    if key in ORIENT: M = Euler([math.radians(a) for a in ORIENT[key]], 'XYZ').to_matrix().to_4x4() @ M
    ob.data.transform(M); ob.data.update()
    co = np.array([v.co[:] for v in ob.data.vertices]); size = co.max(0) - co.min(0)
    s = real / (size.max() if key in KEEP_UP else size[1]); ob.data.transform(Matrix.Scale(s, 4)); info['scale'] = round(float(s), 6)
    co = np.array([v.co[:] for v in ob.data.vertices]); c = (co.max(0) + co.min(0)) / 2
    ob.data.transform(Matrix.Translation(Vector((-c).tolist()))); ob.data.update()
    co = np.array([v.co[:] for v in ob.data.vertices]); info['size_m'] = (co.max(0) - co.min(0)).round(4).tolist()
    info['verts'] = len(ob.data.vertices); info['tris'] = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    # 안 쓰는 머티리얼 슬롯 제거 + 머티리얼별 면 수
    used = set(pl.material_index for pl in ob.data.polygons)
    bpy.context.view_layer.objects.active = ob
    for i in reversed(range(len(ob.material_slots))):
        if i not in used: ob.active_material_index = i; bpy.ops.object.material_slot_remove()
    info['mat_faces'] = {}
    for pl in ob.data.polygons:
        m = ob.material_slots[pl.material_index].material if ob.material_slots else None; n_ = m.name if m else 'None'; info['mat_faces'][n_] = info['mat_faces'].get(n_, 0) + 1
    # 머티리얼 -> 텍스처
    texfiles = sorted(glob.glob(os.path.join(SRC, texdir, '*'))) if texdir else []
    mats = {}
    for sl in ob.material_slots:
        m = sl.material
        if not m: continue
        found = {}
        if m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image:
                    fn = os.path.basename(n.image.filepath or n.image.name).lower()
                    for t in texfiles:
                        if os.path.basename(t).lower() == fn: found.setdefault('_node', []).append(t)
        mats[m.name] = {'node_textures': found.get('_node', [])}
    info['materials'] = mats; info['texture_files'] = [os.path.basename(t) for t in texfiles]
    return ob, info
def render(ob, key):
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = 900; sc.render.resolution_y = 300
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
    for m in bpy.data.materials: m.diffuse_color = (0.55, 0.55, 0.58, 1)
    cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
    co = np.array([v.co[:] for v in ob.data.vertices]); size = co.max(0) - co.min(0); L = float(size.max()) * 1.1
    out = []
    for nm, loc, rot in (('side', (L * 3, 0, 0), (90, 0, 90)), ('top', (0, 0, L * 3), (0, 0, 90)), ('back', (0, L * 3, 0), (90, 0, 180))):
        cam.location = loc; cam.rotation_euler = Euler([math.radians(a) for a in rot]); cd.ortho_scale = L
        if nm == 'back': cd.ortho_scale = float(max(size[0], size[2])) * 1.4
        sc.render.filepath = D + r'\Data\de_prev_%s_%s.png' % (key, nm); bpy.ops.render.render(write_still=True); out.append(sc.render.filepath)
    return out
R = {}
for key in W:
    if ONLY and key not in ONLY: continue
    try:
        ob, info = build(key)
        if STAGE == 'preview': info['renders'] = render(ob, key)
        else:
            bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
            fn = EXP + '\\SM_DE_%s.fbx' % key
            bpy.ops.export_scene.fbx(filepath=fn, use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True, mesh_smooth_type='FACE', path_mode='STRIP', add_leaf_bones=False, bake_anim=False)
            info['fbx'] = fn
        R[key] = info; print('BUILD', key, info.get('size_m'), info.get('tris'))
    except Exception as ex:
        import traceback; R[key] = {'error': traceback.format_exc()[-600:]}; print('BUILD_ERR', key, str(ex)[:200])
old = json.load(open(D + r'\Data\de_weapons_build.json', encoding='utf-8')) if os.path.exists(D + r'\Data\de_weapons_build.json') else {}
old.update(R); json.dump(old, open(D + r'\Data\de_weapons_build.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('DE_BUILD_DONE', STAGE)
