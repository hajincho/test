import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {'log': []}
def log(*a): res['log'].append(' '.join(str(x) for x in a))
try:
    rtg = unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
    rc = unreal.IKRetargeterController.get_controller(rtg)
    names = [str(rc.get_op_name(k)) for k in range(rc.get_num_retarget_ops())]
    if 'IK Chains' not in names:
        for t in ('/Script/IKRig.IKRetargetIKChainsOp', 'IKRetargetIKChainsOp'):
            try:
                r = rc.add_retarget_op(t); log('add', t, r); break
            except Exception as e: log('add fail', t, repr(e))
        names = [str(rc.get_op_name(k)) for k in range(rc.get_num_retarget_ops())]
        ik = names.index('IK Chains') if 'IK Chains' in names else -1
        run = names.index('Run IK Rig')
        if ik > run:
            log('move', rc.move_retarget_op_in_stack(ik, run))
        try: rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, unreal.load_asset('/Game/Furina/Retarget/IK_Manny'))
        except Exception as e: log(repr(e))
        try: rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, unreal.load_asset('/Game/Furina/Retarget/IK_Furina'))
        except Exception as e: log(repr(e))
        try: rc.reset_chain_settings_in_all_ops() if False else None
        except Exception: pass
    log('ops', [str(rc.get_op_name(k)) for k in range(rc.get_num_retarget_ops())])
    unreal.EditorAssetLibrary.save_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_ikops.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('IKOPS_DONE')
