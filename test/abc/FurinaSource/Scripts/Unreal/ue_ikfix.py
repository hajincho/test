import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {'log': []}
def log(*a): res['log'].append(' '.join(str(x) for x in a))
try:
    rig = unreal.load_asset('/Game/Furina/Retarget/IK_Furina')
    c = unreal.IKRigController.get_controller(rig)
    while c.get_num_solvers() > 0:
        log('remove solver', c.remove_solver(0))
    # Two-bone leg fit per side (the Unity FitLeg): hips and pelvis are never touched by IK.
    for side in ('Left', 'Right'):
        i = c.add_solver('/Script/IKRig.IKRigLimbSolver')
        log(side, 'limb solver', i)
        log('root', c.set_root_bone(side + '-leg', i))
        log('connect', c.connect_goal_to_solver(side + 'FootGoal', i))
    # Arms stay FK like in Unity; disconnect is implicit (no solver uses the hand goals).
    unreal.EditorAssetLibrary.save_asset('/Game/Furina/Retarget/IK_Furina')
    rtg = unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
    rc = unreal.IKRetargeterController.get_controller(rtg)
    n = rc.get_num_retarget_ops()
    log('ops', [(rc.get_op_name(k), rc.get_retarget_op_enabled(k)) for k in range(n)])
    unreal.EditorAssetLibrary.save_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_ikfix.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('IKFIX_DONE')
