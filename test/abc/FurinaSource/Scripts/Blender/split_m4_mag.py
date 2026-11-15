"""Splits the real magazine out of the AR15 model (2026-11-15). The earlier prepare_m4.py cut the magazine with a box test on vertices
(z < .85 and -.55 < x < .3), which also sliced the trigger guard / magwell / grip. Here the AR15 meshes are split into connected components
(loose parts) and a part belongs to the magazine when it reaches the bottom of the model (component z_min < 0.1 in source units; measured in
Data/ar15_parts.json: Plane.003 components n=1042 and n=528, x -0.11..0.37, z -0.01..1.0). Nothing is cut through a part.
Outputs (rifle-local cm, the same transform as prepare_m4.py, same FBX axes):
  FBX/M4/SK_M4A1.fbx   rifle without the magazine (all vertices on bone Grip, armature = the template weapon skeleton)
  FBX/M4/SM_M4Mag.fbx  the magazine alone (static, origin = rifle origin, so 'seated' = identity relative to the rifle)
  Data/m4_mag_split.json  counts, magazine bounds
usage: blender -b --factory-startup --python split_m4_mag.py"""
import bpy, bmesh, json, os
from mathutils import Vector, Matrix
ROOT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'; OUT = os.path.join(ROOT, 'FBX', 'M4')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\blender_source_files_freefpstemplate\Blender_Source_Files_FreeFpsTemplate\_Exported\Meshes\SK_AssaultRifle.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
for o in list(bpy.context.scene.objects):
    if o != arm: bpy.data.objects.remove(o, do_unlink=True)
arm.animation_data_clear()
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\ar15\source\ar15 (2)\ar_15.fbx')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
S = 80 / 4.949013233184814
def tf(p): return Vector((p.y * S, (p.x - .65) * S + 10.8, (p.z - .8) * S))
def components(bm):
    seen = set(); out = []
    for v in bm.verts:
        if v.index in seen: continue
        stack = [v]; seen.add(v.index); idx = []
        while stack:
            c = stack.pop(); idx.append(c.index)
            for e in c.link_edges:
                w = e.other_vert(c)
                if w.index not in seen: seen.add(w.index); stack.append(w)
        out.append(idx)
    return out
body_objs, mag_objs = [], []; R = {'parts': []}; mag_min = Vector((1e9,) * 3); mag_max = Vector((-1e9,) * 3)
for o in meshes:
    M = o.matrix_world; me = o.data
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    mag_idx = set()
    for comp in components(bm):
        pts = [M @ bm.verts[i].co for i in comp]
        zmin = min(p.z for p in pts); xc = sum(p.x for p in pts) / len(pts)
        if zmin < 0.1 and -0.15 < xc < 0.4: mag_idx.update(comp)
    R['parts'].append(dict(name=o.name, verts=len(bm.verts), mag_verts=len(mag_idx)))
    for tag, keep_mag in (('body', False), ('mag', True)):
        b2 = bm.copy(); b2.verts.ensure_lookup_table()
        drop = [v for v in b2.verts if (v.index in mag_idx) != keep_mag]
        bmesh.ops.delete(b2, geom=drop, context='VERTS')
        if not b2.verts: b2.free(); continue
        for v in b2.verts:
            v.co = tf(M @ v.co)
            if keep_mag:
                for k in range(3): mag_min[k] = min(mag_min[k], v.co[k]); mag_max[k] = max(mag_max[k], v.co[k])
        new = bpy.data.meshes.new(o.name + '_' + tag); b2.to_mesh(new); b2.free()
        for m in me.materials: new.materials.append(m)
        ob = bpy.data.objects.new(o.name + '_' + tag, new); bpy.context.scene.collection.objects.link(ob)
        if keep_mag: mag_objs.append(ob)
        else:
            ob.parent = arm; ob.matrix_parent_inverse = Matrix.Identity(4)
            grip = ob.vertex_groups.new(name='Grip'); ob.vertex_groups.new(name='Magazine')
            grip.add(list(range(len(new.vertices))), 1, 'REPLACE')
            mod = ob.modifiers.new('WeaponRig', 'ARMATURE'); mod.object = arm
            body_objs.append(ob)
    bm.free()
for o in meshes: bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
for o in body_objs: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SK_M4A1.fbx'), use_selection=True, add_leaf_bones=False, bake_anim=False, axis_forward='-Y', axis_up='Z', apply_unit_scale=True)
bpy.ops.object.select_all(action='DESELECT')
for o in mag_objs: o.select_set(True)
bpy.context.view_layer.objects.active = mag_objs[0]
bpy.ops.object.join()                                    # one static mesh (two material slots AR3 / AR4)
bpy.context.view_layer.objects.active.name = 'SM_M4Mag'
mag = bpy.context.view_layer.objects.active; mag.scale = (0.01, 0.01, 0.01)      # the armature of the rifle FBX carries the 0.01 (cm -> Blender m); a static mesh needs it on the object
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SM_M4Mag.fbx'), use_selection=True, add_leaf_bones=False, bake_anim=False, axis_forward='-Y', axis_up='Z', apply_unit_scale=True)
R['mag_min'] = [round(x, 2) for x in mag_min]; R['mag_max'] = [round(x, 2) for x in mag_max]
json.dump(R, open(os.path.join(ROOT, 'Data', 'm4_mag_split.json'), 'w'), indent=1); print('M4_MAG_SPLIT', R)
