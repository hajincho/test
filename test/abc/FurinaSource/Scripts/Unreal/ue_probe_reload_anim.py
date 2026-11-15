"""Reload animations: weapon (A_FP_WEP_AssaultRifle_Reload: Magazine / Bolt bones), Manny hands (A_FP_AssaultRifle_Reload: hand_l, hand_r)
in component space every 6 frames -> Data/reload_anim.json"""
import unreal, json
def main():
    R = {}; APE = unreal.AnimPoseExtensions; opts = unreal.AnimPoseEvaluationOptions(); W = unreal.AnimPoseSpaces.WORLD
    for path, bones in (('/Game/Furina/FP/Weapon/A_FP_WEP_AssaultRifle_Reload', ('Magazine', 'Bolt', 'Grip')),
                        ('/Game/Furina/FP/Manny/A_FP_AssaultRifle_Reload', ('hand_l', 'hand_r', 'ik_hand_gun'))):
        a = unreal.load_asset(path)
        if a is None: R[path] = None; continue
        n = unreal.AnimationLibrary.get_num_frames(a)
        rows = []
        for f in list(range(0, n, 6)) + [n - 1]:
            pose = APE.get_anim_pose_at_frame(a, f, opts); names = [str(x) for x in APE.get_bone_names(pose)]
            row = {'f': f}
            for b in bones:
                if b in names: t = APE.get_bone_pose(pose, b, W); row[b] = [round(v, 1) for v in t.translation.to_tuple()] + [round(t.rotation.rotator().pitch), round(t.rotation.rotator().yaw), round(t.rotation.rotator().roll)]
            rows.append(row)
        R[path] = dict(frames=n, length=a.get_play_length(), rate=a.get_editor_property('rate_scale'), rows=rows); del a
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\reload_anim.json', 'w'), indent=1)
    print('RELOAD_ANIM')
main(); del main
