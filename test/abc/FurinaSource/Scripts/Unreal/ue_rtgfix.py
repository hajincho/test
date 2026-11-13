import unreal, json, traceback, os, math
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {'log': []}
def log(*a): res['log'].append(' '.join(str(x) for x in a))
try:
    rtg = unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
    rc = unreal.IKRetargeterController.get_controller(rtg)
    T = unreal.RetargetSourceOrTarget.TARGET
    # Root Motion op would pin Furina's Hips (her top-most joint) to the ground root.
    for k in range(rc.get_num_retarget_ops()):
        if str(rc.get_op_name(k)) == 'Root Motion':
            rc.set_retarget_op_enabled(k, False); log('disabled Root Motion', k)
    # Hips keep their own rest rotation; normalise every other auto-aligned offset.
    fpose = unreal.load_asset('/Game/Furina/SK_Furina').get_editor_property('skeleton').get_reference_pose()
    names = [str(n) for n in unreal.AnimPoseExtensions.get_bone_names(fpose)]
    fixed = 0
    for n in names:
        q = rc.get_rotation_offset_for_retarget_pose_bone(n, T)
        l = math.sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w)
        if n == 'Hips':
            rc.set_rotation_offset_for_retarget_pose_bone(n, unreal.Quat(0, 0, 0, 1), T); log('Hips reset, was len', l)
        elif abs(l - 1) > 1e-4 and l > 1e-6:
            rc.set_rotation_offset_for_retarget_pose_bone(n, unreal.Quat(q.x / l, q.y / l, q.z / l, q.w / l), T); fixed += 1
    log('normalized', fixed)
    log('ops', [(str(rc.get_op_name(k)), rc.get_retarget_op_enabled(k)) for k in range(rc.get_num_retarget_ops())])
    unreal.EditorAssetLibrary.save_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_rtgfix.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('RTGFIX_DONE')
