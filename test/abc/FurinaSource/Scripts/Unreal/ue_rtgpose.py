import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    rtg = unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
    rc = unreal.IKRetargeterController.get_controller(rtg)
    T = unreal.RetargetSourceOrTarget.TARGET
    res['pose_name'] = str(rc.get_current_retarget_pose_name(T))
    res['root_offset_T'] = str(rc.get_root_offset_in_retarget_pose(T))
    res['root_offset_S'] = str(rc.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.SOURCE))
    for b in ['Hips', 'Spine', 'Left-leg', 'Left-arm', 'Left-shoulder', 'Head']:
        res['rot_' + b] = str(rc.get_rotation_offset_for_retarget_pose_bone(b, T))
    for k in range(rc.get_num_retarget_ops()):
        name = rc.get_op_name(k)
        try:
            oc = rc.get_op_controller(k)
            res['op_%d' % k] = (str(name), str(oc.get_class().get_name()), str(oc.get_settings().export_text())[:1500] if hasattr(oc, 'get_settings') else None)
        except Exception as e:
            res['op_%d' % k] = (str(name), repr(e))
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_rtgpose.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('RTGPOSE_DONE')
