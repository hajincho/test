"""Blender headless: is the gun (ik_hand_gun) rigid in the right hand, and where is the left hand relative to the gun?
Reports per animation the spread of hand_r^-1 * ik_hand_gun and gun^-1 * hand_l over all frames (cm / deg)."""
import bpy, sys, os, json, math
root, out = sys.argv[sys.argv.index('--') + 1:][:2]
anim_dir = os.path.join(root, '_Exported', 'Animations')
res = {}
def deg(q): return math.degrees(2 * math.acos(min(1.0, abs(q.w))))
for f in sorted(os.listdir(anim_dir)):
    if 'WEP' in f: continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(anim_dir, f), automatic_bone_orientation=False, ignore_leaf_bones=False)
    a = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]
    act = a.animation_data.action; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    rel_g, rel_l, head_gun = [], [], []
    for fr in range(f0, f1 + 1):
        bpy.context.scene.frame_set(fr)
        M = lambda b: a.matrix_world @ a.pose.bones[b].matrix
        hr, gun, hl, hd = M('hand_r'), M('ik_hand_gun'), M('hand_l'), M('head')
        rel_g.append(hr.inverted() @ gun); rel_l.append(gun.inverted() @ hl); head_gun.append(hd.inverted() @ gun)
    def spread(mats):
        t0, q0 = mats[0].to_translation(), mats[0].to_quaternion()
        return dict(first_cm=[round(v * 100, 2) for v in t0], first_q=[round(v, 4) for v in q0],
                    max_move_cm=round(max((m.to_translation() - t0).length for m in mats) * 100, 2),
                    max_rot_deg=round(max(deg(q0.rotation_difference(m.to_quaternion())) for m in mats), 2))
    res[f] = dict(frames=[f0, f1], gun_in_hand_r=spread(rel_g), hand_l_in_gun=spread(rel_l), gun_in_head=spread(head_gun))
json.dump(res, open(out, 'w'), indent=1)
print('GUN_HAND_DONE')
