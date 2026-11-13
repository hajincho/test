"""Blender: import Furina (BlenderAlternate.fbx), report, export a UE-ready FBX (Furina skeleton only)."""
import bpy, sys, json
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, out_fbx, report = argv
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src, automatic_bone_orientation=False, ignore_leaf_bones=False)
arms = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
arm = arms[0]
info = dict(objects=[(o.name, o.type, o.parent.name if o.parent else None, list(o.matrix_world.to_scale())) for o in bpy.context.scene.objects])
bpy.context.view_layer.update()
mw = arm.matrix_world
def head(n): return list(mw @ arm.data.bones[n].head_local)
info['bones'] = len(arm.data.bones)
info['roots'] = [b.name for b in arm.data.bones if not b.parent]
for n in ['Hips', 'Head', 'Left ankle', 'Left toe', 'Left leg', 'Left wrist', 'Right wrist', 'Left arm', 'Left elbow']:
    if n in arm.data.bones: info[n] = [round(v, 4) for v in head(n)]
m = meshes[0]
bb = [m.matrix_world @ Vector(c) for c in m.bound_box]
info['bbox_min'] = [round(min(v[i] for v in bb), 4) for i in range(3)]
info['bbox_max'] = [round(max(v[i] for v in bb), 4) for i in range(3)]
info['materials'] = [(s.material.name if s.material else None) for s in m.material_slots]
info['shape_keys'] = [k.name for k in m.data.shape_keys.key_blocks] if m.data.shape_keys else []
info['verts'] = len(m.data.vertices)
# weighted groups
used = set()
for v in m.data.vertices:
    for g in v.groups:
        if g.weight > 0: used.add(m.vertex_groups[g.group].name)
info['weighted_bones'] = len(used)
info['unweighted_bones'] = [b.name for b in arm.data.bones if b.name not in used]
json.dump(info, open(report, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
# Rename armature object so UE does not keep it as an extra root bone.
arm.name = 'Armature'
for o in bpy.context.scene.objects:
    o.select_set(o in (arm, m))
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=out_fbx, use_selection=True, object_types={'ARMATURE', 'MESH'},
                         add_leaf_bones=False, bake_anim=False, use_armature_deform_only=False,
                         mesh_smooth_type='FACE', use_mesh_modifiers=False, path_mode='STRIP',
                         primary_bone_axis='Y', secondary_bone_axis='X', axis_forward='-Z', axis_up='Y',
                         apply_scale_options='FBX_SCALE_NONE', global_scale=1.0)
print('EXPORTED', out_fbx)
