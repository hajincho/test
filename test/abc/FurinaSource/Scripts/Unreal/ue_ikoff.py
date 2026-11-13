import unreal, json, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
rtg = unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
rc = unreal.IKRetargeterController.get_controller(rtg)
log = []
for k in range(rc.get_num_retarget_ops()):
    n = str(rc.get_op_name(k))
    if n in ('Retarget IK Goals', 'Run IK Rig'):
        rc.set_retarget_op_enabled(k, False)
    log.append((n, rc.get_retarget_op_enabled(k)))
unreal.EditorAssetLibrary.save_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
json.dump(log, open(os.path.join(S, 'ue_ikoff.json'), 'w'))
print('IKOFF_DONE')
