"""Real reload motion (2026-11-15). The FPS template reload (A_FP_AssaultRifle_Reload, 94 frames @30 fps) already is: pull the magazine, let it drop,
take a fresh one from the waist, bring it up and push it in. Furina's old reload only lerped her left hand to a fixed magazine point.
Now the Manny left-hand path relative to the rifle (gun-local axes, delta from frame 0) is written as three float curves
ReloadLX / ReloadLY / ReloadLZ (cm, x left / y forward / z up of the gun frame) on AS_Furina_FP_Reload and AM_Furina_FP_Reload.
CR_FurinaSecondary adds them to the left-hand goal (gun frame), so the hand follows the template path while the rifle's own reload animation
(Magazine bone: out, drop, new magazine up from below, seated) plays in sync. usage: py ue_reload_motion.py [scale 0.9]"""
import unreal, json, os, sys
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CURVES = ('ReloadLX', 'ReloadLY', 'ReloadLZ')
def main():
    k = float(sys.argv[1]) if len(sys.argv) > 1 else 0.9
    APE = unreal.AnimPoseExtensions; opts = unreal.AnimPoseEvaluationOptions(); W = unreal.AnimPoseSpaces.WORLD
    src = unreal.load_asset('/Game/Furina/FP/Manny/A_FP_AssaultRifle_Reload')
    n = unreal.AnimationLibrary.get_num_frames(src)
    rel = []
    for f in range(n):
        pose = APE.get_anim_pose_at_frame(src, f, opts)
        gun = APE.get_bone_pose(pose, 'ik_hand_gun', W); hand = APE.get_bone_pose(pose, 'hand_l', W)
        r = hand.multiply(gun.inverse())
        rel.append(r.translation)
    base = rel[0]
    times = [f / 30.0 for f in range(n)]
    cols = [[round((rel[f] - base).x * k, 3) for f in range(n)], [round((rel[f] - base).y * k, 3) for f in range(n)], [round((rel[f] - base).z * k, 3) for f in range(n)]]
    A = '/Game/Furina/FP/Anim/'; R = {'k': k, 'frames': n, 'max': [round(max(abs(v) for v in c), 1) for c in cols]}
    for name in ('AS_Furina_FP_Reload', 'AM_Furina_FP_Reload'):
        a = unreal.load_asset(A + name)
        have = [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(a, unreal.RawCurveTrackTypes.RCT_FLOAT)]
        for c, vals in zip(CURVES, cols):
            if c in have: unreal.AnimationLibrary.remove_curve(a, c, False)
            unreal.AnimationLibrary.add_curve(a, c, unreal.RawCurveTrackTypes.RCT_FLOAT, False)
            unreal.AnimationLibrary.add_float_curve_keys(a, c, times, vals)
        R[name] = dict(length=a.get_play_length(), curves=[str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(a, unreal.RawCurveTrackTypes.RCT_FLOAT)])
        R[name]['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(a, False); del a
    json.dump(dict(R, path=[[round(v, 2) for v in col[::6]] for col in cols]), open(os.path.join(D, 'reload_motion.json'), 'w'), indent=1)
    print('RELOAD_MOTION', R)
    del src
main(); del main
