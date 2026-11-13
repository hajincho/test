import unreal, json, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
rtg = unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
rc = unreal.IKRetargeterController.get_controller(rtg)
log = []
for k in range(rc.get_num_retarget_ops()):
    n = str(rc.get_op_name(k))
    if n in ('Retarget IK Goals', 'Run IK Rig'): rc.set_retarget_op_enabled(k, True)
    log.append((n, rc.get_retarget_op_enabled(k)))
try: rc.run_op_initial_setup(); log.append('setup ok')
except Exception as e: log.append(repr(e))
rig = unreal.load_asset('/Game/Furina/Retarget/IK_Furina')
c = unreal.IKRigController.get_controller(rig)
log.append(('solvers', c.get_num_solvers(), [c.get_root_bone(i) if hasattr(c, 'get_root_bone') else None for i in range(c.get_num_solvers())]))
log.append(('mesh compatible', c.is_skeletal_mesh_compatible(unreal.load_asset('/Game/Furina/SK_Furina'))))
unreal.EditorAssetLibrary.save_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
json.dump(log, open(os.path.join(S, 'ue_ikon.json'), 'w'), default=str)
print('IKON_DONE')
