"""Re-export Furina for UE with the unit scale baked in (no x100 on the root joint). Writes variants for inspection."""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
src, outdir = argv
def load():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=src, automatic_bone_orientation=False, ignore_leaf_bones=False)
    arm = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]
    arm.name = 'Armature'
    for o in bpy.context.scene.objects: o.select_set(o.type in ('ARMATURE', 'MESH'))
    bpy.context.view_layer.objects.active = arm
common = dict(use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False, bake_anim=False,
              use_armature_deform_only=False, mesh_smooth_type='FACE', use_mesh_modifiers=False, path_mode='STRIP',
              primary_bone_axis='Y', secondary_bone_axis='X', axis_forward='-Z', axis_up='Y')
load(); bpy.ops.export_scene.fbx(filepath=outdir + r'\Furina_all.fbx', apply_scale_options='FBX_SCALE_ALL', global_scale=1.0, **common)
load(); bpy.ops.export_scene.fbx(filepath=outdir + r'\Furina_units.fbx', apply_scale_options='FBX_SCALE_UNITS', global_scale=1.0, **common)
# variant: work in centimetres in Blender (scene unit 0.01, armature scaled x100 and applied)
load()
sc = bpy.context.scene; sc.unit_settings.scale_length = 0.01
arm = bpy.data.objects['Armature']
for o in bpy.context.scene.objects: o.select_set(o.type in ('ARMATURE', 'MESH'))
arm.scale = (100, 100, 100)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        bpy.context.view_layer.objects.active = o
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=outdir + r'\Furina_cm.fbx', apply_scale_options='FBX_SCALE_NONE', global_scale=1.0, **common)
print('VARIANTS_DONE')
