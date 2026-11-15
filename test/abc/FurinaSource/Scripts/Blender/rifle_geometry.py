"""Blender headless: SK_AssaultRifle vertices (bind pose, cm) in the mesh's armature space + bounds, for sight finding
and first-person clipping/visibility tuning. Writes <out json>: {'verts': [[x,y,z],...] (decimated), 'bounds', 'bones'}.
usage: blender -b --factory-startup --python rifle_geometry.py -- <fbx> <out json>"""
import bpy, sys, json
fbx, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx, automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]
mesh = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
inv = arm.matrix_world.inverted()
vs = [inv @ (mesh.matrix_world @ v.co) for v in mesh.data.vertices]      # armature space (FBX cm units)
xs, ys, zs = [v.x for v in vs], [v.y for v in vs], [v.z for v in vs]
bones = {b.name: [list(b.head_local), list(b.tail_local)] for b in arm.data.bones}
json.dump({'verts': [[round(v.x, 2), round(v.y, 2), round(v.z, 2)] for v in vs], 'n': len(vs),
           'bounds': [[min(xs), max(xs)], [min(ys), max(ys)], [min(zs), max(zs)]], 'bones': bones,
           'arm_scale': list(arm.scale), 'arm_rot': list(arm.rotation_euler)}, open(out, 'w'))
print('RIFLE_GEOM_DONE', len(vs))
