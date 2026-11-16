"""Builds the Colt M4A1 rifle for the existing weapon rig (2026-11-15).
Source: C:\\Users\\fromj\\Downloads\\colt-m4a1-carbine\\source\\Colt_m4A1.fbx (object m4a1.001 = rifle with a seated STANAG magazine; 'ammo' / 'mag_20rnd' are loose parts and are not used).
The body is levelled (bore pitch from the analysis -3.824 deg, then a second rotation so that the sight line rear aperture -> front post has the same tiny slope as the old rifle's),
scaled to 80 cm (muzzle -> butt) and placed so that the rear aperture sits exactly on the old rear-sight point (rifle-local UE (0, -11.757, 9.984)).
Outputs (rifle-local cm, same FBX axes as split_m4_mag.py):
  FBX/M4/SK_M4A1.fbx   body without the magazine (faces with material stanag_mag removed), all vertices on bone Grip of the template weapon armature
  FBX/M4/SM_M4Mag.fbx  the seated magazine alone (static, origin = rifle origin so 'seated' = identity)
  Data/colt_geometry.json  new rifle-local calibration points (UE axes)
usage: blender -b --factory-startup --python build_colt_rifle.py"""
import bpy, bmesh, json, os, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'; OUT = os.path.join(ROOT, 'FBX', 'M4')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\blender_source_files_freefpstemplate\Blender_Source_Files_FreeFpsTemplate\_Exported\Meshes\SK_AssaultRifle.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
for o in list(bpy.context.scene.objects):
    if o != arm: bpy.data.objects.remove(o, do_unlink=True)
arm.animation_data_clear()
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\colt-m4a1-carbine\source\Colt_m4A1.fbx')
src = bpy.data.objects['m4a1.001']; M = src.matrix_world; me = src.data
mats = [m.name if m else None for m in me.materials]
R1 = Matrix.Rotation(math.radians(-3.8240519141381806), 4, 'X')
W1 = [R1 @ (M @ v.co) for v in me.vertices]
# --- sight points in the levelled frame
bvh = BVHTree.FromPolygons([tuple(v) for v in W1], [list(p.vertices) for p in me.polygons], all_triangles=False)
def passes(z, y0=0.7, y1=0.9):                               # does a ray along +y at x=0, height z, pass the rear sight plate untouched?
    p = Vector((0, -8, z)); d = Vector((0, 1, 0))
    for _ in range(20):
        h, n, i, dist = bvh.ray_cast(p, d, 100)
        if h is None: return True
        if y0 < h.y < y1: return False
        p = h + d * 1e-4
    return True
gap = [z / 1000 for z in range(1830, 1900, 2) if passes(z / 1000)]
ap_z = (min(gap) + max(gap)) / 2 if gap else 1.86
ap_y = 0.7735
post = max((v for v in W1 if abs(v.x) < .06 and -2.6 < v.y < -2.2), key=lambda v: v.z); post_y = sum(v.y for v in W1 if abs(v.x) < .06 and -2.6 < v.y < -2.2 and v.z > post.z - .01) / max(1, len([v for v in W1 if abs(v.x) < .06 and -2.6 < v.y < -2.2 and v.z > post.z - .01]))
rear = Vector((0, ap_y, ap_z)); front = Vector((0, post_y, post.z))
th_c = math.atan2(front.z - rear.z, -(front.y - rear.y))                    # current sight-line angle (forward = -y)
th_d = math.atan2(9.815 - 9.984, 42.367)                                     # old rifle sight-line angle
R2 = Matrix.Rotation(-(th_d - th_c), 4, 'X')
RR = R2 @ R1
def lev(p): return R2 @ (R1 @ p)
rear2 = lev(rear) if False else R2 @ rear; front2 = R2 @ front
ang = math.degrees(math.atan2(front2.z - rear2.z, -(front2.y - rear2.y)))
assert abs(ang - math.degrees(th_d)) < 0.05, (ang, math.degrees(th_d))
Wl = [R2 @ w for w in W1]
ymin = min(w.y for w in Wl); ymax = max(w.y for w in Wl)
S = 80 / (ymax - ymin)
ox, oy, oz = rear2.x, rear2.y, rear2.z
def T(p):                                                   # levelled colt coordinates -> rifle-local Blender (q); UE = (q.x, -q.y, q.z)
    return Vector(((p.x - ox) * S, (p.y - oy) * S + 11.757165, (p.z - oz) * S + 9.984))
def ue(q): return [round(q.x, 3), round(-q.y, 3), round(q.z, 3)]
R = {'scale_cm_per_unit': S, 'sight_slope_deg': ang, 'aperture_z_gap': [min(gap), max(gap)] if gap else None}
muz_pts = [w for w in Wl if w.y < ymin + 0.08]; muz = sum(muz_pts, Vector()) / len(muz_pts); R['muzzle'] = ue(T(muz))
but_pts = [w for w in Wl if w.y > ymax - 0.05]; but = sum(but_pts, Vector()) / len(but_pts); R['stock_butt'] = ue(T(but))
R['rear_aperture'] = ue(T(rear2)); R['front_post'] = ue(T(front2))
# --- split by material and export
body_objs = []; mag_objs = []
for tag, keep_mag in (('body', False), ('mag', True)):
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    drop = [f for f in bm.faces if (mats[f.material_index] == 'stanag_mag') != keep_mag]
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for v in bm.verts:
        v.co = T(R2 @ (R1 @ (M @ v.co)))
        for k in range(3): mn[k] = min(mn[k], v.co[k]); mx[k] = max(mx[k], v.co[k])
    new = bpy.data.meshes.new('colt_' + tag); bm.to_mesh(new); bm.free()
    for m in me.materials: new.materials.append(m)
    ob = bpy.data.objects.new('colt_' + tag, new); bpy.context.scene.collection.objects.link(ob)
    R[tag + '_verts'] = len(new.vertices); R[tag + '_bounds_ue'] = [ue(Vector((mn.x, mx.y, mn.z))), ue(Vector((mx.x, mn.y, mx.z)))]
    if keep_mag: mag_objs.append(ob)
    else:
        ob.parent = arm; ob.matrix_parent_inverse = Matrix.Identity(4)
        grip = ob.vertex_groups.new(name='Grip'); ob.vertex_groups.new(name='Magazine')
        grip.add(list(range(len(new.vertices))), 1, 'REPLACE')
        mod = ob.modifiers.new('WeaponRig', 'ARMATURE'); mod.object = arm
        body_objs.append(ob)
for o in list(bpy.context.scene.objects):
    if o.name in ('m4a1.001', 'ammo', 'mag_20rnd'): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
for o in body_objs: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SK_M4A1.fbx'), use_selection=True, add_leaf_bones=False, bake_anim=False, axis_forward='-Y', axis_up='Z', apply_unit_scale=True)
bpy.ops.object.select_all(action='DESELECT')
for o in mag_objs: o.select_set(True)
bpy.context.view_layer.objects.active = mag_objs[0]
mag = mag_objs[0]; mag.name = 'SM_M4Mag'; mag.scale = (0.01, 0.01, 0.01)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SM_M4Mag.fbx'), use_selection=True, add_leaf_bones=False, bake_anim=False, axis_forward='-Y', axis_up='Z', apply_unit_scale=True)
json.dump(R, open(os.path.join(ROOT, 'Data', 'colt_geometry.json'), 'w'), indent=1); print('COLT_BUILD', json.dumps(R))
