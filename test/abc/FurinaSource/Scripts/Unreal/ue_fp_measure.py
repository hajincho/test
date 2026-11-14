"""Measures, from the animation data itself (AnimPose API, no actors):
Manny A_FP_AssaultRifle_<pose> vs Furina's retargeted AS_Furina_FP_<pose> (both in component space, same frame)
 - rifle socket on Furina's right wrist  = MannyGun relative to FurinaRW
 - left-hand IK goal relative to RW      = (Manny hand_l position, Furina LW rotation) relative to FurinaRW
Writes Data/fp_measure.json."""
import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
R = {}
APE = unreal.AnimPoseExtensions
def T(x): return {'t': [round(v, 3) for v in x.translation.to_tuple()], 'q': [round(x.rotation.x, 5), round(x.rotation.y, 5), round(x.rotation.z, 5), round(x.rotation.w, 5)]}
try:
    opts = unreal.AnimPoseEvaluationOptions()
    def pose_at(path, frame=0):
        return APE.get_anim_pose_at_frame(unreal.load_asset(path), frame, opts)
    W = unreal.AnimPoseSpaces.WORLD
    for pose, frame in (('Idle_Pose', 0), ('Aim_Pose', 0), ('Idle_Loop', 30), ('Walk_F_Loop', 10), ('Run_Loop', 10)):
        mp = pose_at('/Game/Furina/FP/Manny/A_FP_AssaultRifle_' + pose, frame)
        fp = pose_at('/Game/Furina/FP/Anim/AS_Furina_FP_' + pose, frame)
        names = [str(n) for n in APE.get_bone_names(mp)]
        g = lambda p, b: APE.get_bone_pose(p, b, W)
        has_gun = 'ik_hand_gun' in names
        mg = g(mp, 'ik_hand_gun') if has_gun else g(mp, 'hand_r')
        mr, ml, mh = g(mp, 'hand_r'), g(mp, 'hand_l'), g(mp, 'head')
        fr, fl, fh = g(fp, 'Right-wrist'), g(fp, 'Left-wrist'), g(fp, 'Head')
        rel = lambda child, parent: child.multiply(parent.inverse())
        goal_l = unreal.Transform(ml.translation, fl.rotation.rotator(), unreal.Vector(1, 1, 1))
        R[pose] = dict(has_ik_hand_gun=has_gun, n_manny_bones=len(names),
                       manny={'gun': T(mg), 'hand_r': T(mr), 'hand_l': T(ml), 'head': T(mh)},
                       furina={'rw': T(fr), 'lw': T(fl), 'head': T(fh)},
                       right_wrist_gap_cm=round((fr.translation - mr.translation).length(), 2),
                       left_wrist_gap_cm=round((fl.translation - ml.translation).length(), 2),
                       head_gap_cm=round((fh.translation - mh.translation).length(), 2),
                       gun_in_furina_rw=T(rel(mg, fr)), lgoal_in_furina_rw=T(rel(goal_l, fr)),
                       manny_shoulders={'r': T(g(mp, 'upperarm_r')), 'l': T(g(mp, 'upperarm_l')), 'neck': T(g(mp, 'neck_01'))},
                       furina_shoulders={'r': T(g(fp, 'Right-arm')), 'l': T(g(fp, 'Left-arm')), 'neck': T(g(fp, 'Neck')), 'chest': T(g(fp, 'Chest'))},
                       hand_r_in_gun=T(rel(mr, mg)), hand_l_in_gun=T(rel(ml, mg)),
                       furina_rw_in_gun=T(rel(fr, mg)), furina_lw_in_gun=T(rel(fl, mg)))
except Exception:
    R['error'] = traceback.format_exc()
json.dump(R, open(os.path.join(D, 'fp_measure.json'), 'w'), indent=1)
print('FP_MEASURE_DONE')
