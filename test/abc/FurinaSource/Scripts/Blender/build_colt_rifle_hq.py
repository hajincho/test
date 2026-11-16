"""High quality Colt M4A1 rifle build (2026-11-16), replaces the visuals made by build_colt_rifle.py. Same levelling / scaling / placement (rear aperture on the old rear-sight point, 80 cm, same constants in Data/colt_geometry.json),
but:
  * the magazine is the detailed loose object `mag_20rnd` (7,024 vertices, a real 20-round STANAG with its own UVs) fitted onto the seated magazine with a rigid ICP (residual reported), instead of the 1,040-vertex seated one;
    the seated magazine faces (material stanag_mag) are removed from the body so nothing is doubled
  * tangent space is exported (use_tspace) and the FBX smoothing / custom normals are kept
  * nothing is decimated; the body keeps all 32,370 vertices
Outputs: FBX/M4/SK_M4A1.fbx (body, all vertices on bone Grip of the template weapon armature), FBX/M4/SM_M4Mag.fbx (magazine, static, origin = rifle origin) and Data/colt_geometry_hq.json (same points + magazine data).
usage: blender -b --factory-startup --python build_colt_rifle_hq.py"""
import bpy, bmesh, json, os, math
import numpy as np
from mathutils import Vector, Matrix, kdtree
from mathutils.bvhtree import BVHTree
ROOT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'; OUT = os.path.join(ROOT, 'FBX', 'M4')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\blender_source_files_freefpstemplate\Blender_Source_Files_FreeFpsTemplate\_Exported\Meshes\SK_AssaultRifle.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
for o in list(bpy.context.scene.objects):
    if o != arm: bpy.data.objects.remove(o, do_unlink=True)
arm.animation_data_clear()
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\colt-m4a1-carbine\source\Colt_m4A1.fbx')
src = bpy.data.objects['m4a1.001']; loose = bpy.data.objects['mag_20rnd']; M = src.matrix_world; me = src.data
mats = [m.name if m else None for m in me.materials]
R1 = Matrix.Rotation(math.radians(-3.8240519141381806), 4, 'X')
W1 = [R1 @ (M @ v.co) for v in me.vertices]
bvh = BVHTree.FromPolygons([tuple(v) for v in W1], [list(p.vertices) for p in me.polygons], all_triangles=False)
def passes(z, y0=0.7, y1=0.9):
    p = Vector((0, -8, z)); d = Vector((0, 1, 0))
    for _ in range(20):
        h, n, i, dist = bvh.ray_cast(p, d, 100)
        if h is None: return True
        if y0 < h.y < y1: return False
        p = h + d * 1e-4
    return True
gap = [z / 1000 for z in range(1830, 1900, 2) if passes(z / 1000)]
ap_z = (min(gap) + max(gap)) / 2 if gap else 1.86; ap_y = 0.7735
post = max((v for v in W1 if abs(v.x) < .06 and -2.6 < v.y < -2.2), key=lambda v: v.z)
sel = [v for v in W1 if abs(v.x) < .06 and -2.6 < v.y < -2.2 and v.z > post.z - .01]; post_y = sum(v.y for v in sel) / len(sel)
rear = Vector((0, ap_y, ap_z)); front = Vector((0, post_y, post.z))
th_c = math.atan2(front.z - rear.z, -(front.y - rear.y)); th_d = math.atan2(9.815 - 9.984, 42.367)
R2 = Matrix.Rotation(-(th_d - th_c), 4, 'X'); rear2 = R2 @ rear; front2 = R2 @ front
ang = math.degrees(math.atan2(front2.z - rear2.z, -(front2.y - rear2.y))); assert abs(ang - math.degrees(th_d)) < 0.05, ang
Wl = [R2 @ w for w in W1]; ymin = min(w.y for w in Wl); ymax = max(w.y for w in Wl); S = 80 / (ymax - ymin); ox, oy, oz = rear2.x, rear2.y, rear2.z
def T(p): return Vector(((p.x - ox) * S, (p.y - oy) * S + 11.757165, (p.z - oz) * S + 9.984))
def ue(q): return [round(q.x, 3), round(-q.y, 3), round(q.z, 3)]
R = {'scale_cm_per_unit': S, 'sight_slope_deg': ang}
# ---- fit the detailed loose magazine onto the seated one (rigid ICP, no scale), in the world frame of the import
def world(o, only_mat=None):
    Mo = np.array(o.matrix_world); mm = o.data; idx = set(range(len(mm.vertices)))
    if only_mat:
        ms = [m.name if m else None for m in mm.materials]; idx = set(v for p in mm.polygons if ms[p.material_index] == only_mat for v in p.vertices)
    P = np.array([mm.vertices[i].co[:] for i in sorted(idx)]); return (np.c_[P, np.ones(len(P))] @ Mo.T)[:, :3]
seated = world(src, 'stanag_mag'); lv = world(loose)
def pca(P): c = P.mean(0); u, s, vt = np.linalg.svd(P - c, full_matrices=False); return c, vt
def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0); H = (A - ca).T @ (B - cb); u, s, vt = np.linalg.svd(H); d = np.sign(np.linalg.det(vt.T @ u.T)); Rm = vt.T @ np.diag([1, 1, d]) @ u.T; return Rm, cb - Rm @ ca
kd = kdtree.KDTree(len(seated))
for i, p in enumerate(seated): kd.insert(p, i)
kd.balance()
def icp(R0, t0, it=60):
    Rm, t = R0, t0
    for _ in range(it):
        cur = lv @ Rm.T + t; nn = np.array([seated[kd.find(p)[1]] for p in cur[::3]]); Rm, t = kabsch(lv[::3], nn)
    cur = lv @ Rm.T + t; return Rm, t, float(np.sqrt(np.mean([np.sum((seated[kd.find(p)[1]] - p) ** 2) for p in cur[::5]])))
cs, As = pca(seated); cl, Al = pca(lv); best = None
for sx in (1, -1):
    for sy in (1, -1):
        Rm0 = As.T @ np.diag([sx, sy, sx * sy]) @ Al; res = icp(Rm0, cs - Rm0 @ cl)
        if best is None or res[2] < best[2]: best = res
Rm, tm, rms = best; R['mag_icp_rms_units'] = rms; R['mag_icp_rms_cm'] = rms * S
FIT = Matrix([[*Rm[0], tm[0]], [*Rm[1], tm[1]], [*Rm[2], tm[2]], [0, 0, 0, 1]])
muz_pts = [w for w in Wl if w.y < ymin + 0.08]; muz = sum(muz_pts, Vector()) / len(muz_pts); R['muzzle'] = ue(T(muz))
but_pts = [w for w in Wl if w.y > ymax - 0.05]; but = sum(but_pts, Vector()) / len(but_pts); R['stock_butt'] = ue(T(but))
R['rear_aperture'] = ue(T(rear2)); R['front_post'] = ue(T(front2))
body_objs = []; mag_objs = []
# body: everything except the seated magazine faces
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if mats[f.material_index] == 'stanag_mag'], context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
for v in bm.verts: v.co = T(R2 @ (R1 @ (M @ v.co)))
new = bpy.data.meshes.new('colt_body'); bm.to_mesh(new); bm.free()
for m in me.materials: new.materials.append(m)
ob = bpy.data.objects.new('colt_body', new); bpy.context.scene.collection.objects.link(ob); ob.parent = arm; ob.matrix_parent_inverse = Matrix.Identity(4)
grip = ob.vertex_groups.new(name='Grip'); ob.vertex_groups.new(name='Magazine'); grip.add(list(range(len(new.vertices))), 1, 'REPLACE'); mod = ob.modifiers.new('WeaponRig', 'ARMATURE'); mod.object = arm; body_objs.append(ob)
R['body_verts'] = len(new.vertices)
# magazine: the loose detailed object, fitted, then the same transform chain as the body (copy of the mesh data so the normals / UVs are kept)
lm = loose.data.copy(); mag = bpy.data.objects.new('colt_mag', lm); bpy.context.scene.collection.objects.link(mag)
Lw = loose.matrix_world
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for v in lm.vertices:
    p = FIT @ (Lw @ v.co); v.co = T(R2 @ (R1 @ p))
    for k in range(3): mn[k] = min(mn[k], v.co[k]); mx[k] = max(mx[k], v.co[k])
lm.update(); R['mag_verts'] = len(lm.vertices); R['mag_bounds_ue'] = [ue(Vector((mn.x, mx.y, mn.z))), ue(Vector((mx.x, mn.y, mx.z)))]
mag_objs.append(mag)
for o in list(bpy.context.scene.objects):
    if o.name in ('m4a1.001', 'ammo', 'mag_20rnd'): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
for o in body_objs: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SK_M4A1.fbx'), use_selection=True, add_leaf_bones=False, bake_anim=False, axis_forward='-Y', axis_up='Z', apply_unit_scale=True, use_tspace=True)
bpy.ops.object.select_all(action='DESELECT'); mag.select_set(True); bpy.context.view_layer.objects.active = mag; mag.name = 'SM_M4Mag'; mag.scale = (0.01, 0.01, 0.01)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SM_M4Mag.fbx'), use_selection=True, add_leaf_bones=False, bake_anim=False, axis_forward='-Y', axis_up='Z', apply_unit_scale=True, use_tspace=True)
old = json.load(open(os.path.join(ROOT, 'Data', 'colt_geometry.json'))); R['case_port'] = old.get('case_port', [-2.2, -3.5, 4.5])
json.dump(R, open(os.path.join(ROOT, 'Data', 'colt_geometry_hq.json'), 'w'), indent=1); print('COLT_HQ', json.dumps(R))
