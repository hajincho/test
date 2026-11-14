"""Blender headless: inspects the free FPS template FBX files (skeleton, animated bones, frame ranges, key bone poses).
usage: blender -b --factory-startup --python inspect_fp_template.py -- <template root> <out json>"""
import bpy, sys, os, json
root, out = sys.argv[sys.argv.index('--') + 1:][:2]
exp = os.path.join(root, '_Exported')
files = [os.path.join(exp, 'Animations', f) for f in sorted(os.listdir(os.path.join(exp, 'Animations')))]
files += [os.path.join(root, 'Meshes', 'Manny', 'SK_FP_Manny_Simple.fbx'), os.path.join(exp, 'Meshes', 'SK_AssaultRifle.fbx')]
KEY = ['root', 'pelvis', 'spine_01', 'spine_05', 'neck_01', 'head', 'clavicle_r', 'upperarm_r', 'hand_r', 'hand_l', 'ik_hand_gun',
       'ik_hand_r', 'ik_hand_l', 'weapon_r', 'thigh_l', 'foot_l', 'camera', 'Camera']
res = {}
for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    r = {}
    try:
        bpy.ops.import_scene.fbx(filepath=f, automatic_bone_orientation=False, ignore_leaf_bones=False)
        objs = list(bpy.context.scene.objects)
        r['objects'] = [(o.name, o.type) for o in objs]
        arms = [o for o in objs if o.type == 'ARMATURE']
        meshes = [o for o in objs if o.type == 'MESH']
        r['meshes'] = [(m.name, len(m.data.vertices), sorted({g.name for g in m.vertex_groups})[:5], len(m.vertex_groups)) for m in meshes]
        for a in arms:
            ad = {'n_bones': len(a.data.bones), 'bones': [b.name for b in a.data.bones][:400],
                  'scale': list(a.scale), 'rot': list(a.rotation_euler)}
            act = a.animation_data.action if a.animation_data else None
            if act:
                fr = act.frame_range
                ad['action'] = act.name; ad['frames'] = [fr[0], fr[1]]; ad['fps'] = bpy.context.scene.render.fps
                names = set()
                try:
                    for fc in act.fcurves: names.add(fc.data_path.split('"')[1] if '"' in fc.data_path else fc.data_path)
                except Exception:
                    for layer in act.layers:
                        for strip in layer.strips:
                            for cb in strip.channelbags:
                                for fc in cb.fcurves: names.add(fc.data_path.split('"')[1] if '"' in fc.data_path else fc.data_path)
                ad['animated'] = sorted(names)
                poses = {}
                for fno in (int(fr[0]), int((fr[0] + fr[1]) / 2)):
                    bpy.context.scene.frame_set(fno)
                    poses[fno] = {b: [round(v, 2) for v in (a.matrix_world @ a.pose.bones[b].head)] for b in KEY if b in a.pose.bones}
                ad['poses'] = poses
            r[a.name] = ad
    except Exception as e:
        r['error'] = repr(e)
    res[os.path.basename(f)] = r
json.dump(res, open(out, 'w'), indent=1)
print('INSPECT_DONE')
