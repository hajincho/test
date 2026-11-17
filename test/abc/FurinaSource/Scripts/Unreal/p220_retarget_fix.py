"""Lyra Manny 전용 IK 리그/리타게터를 만들어(기존 IK_Manny/RTG_Manny_To_Furina 복제 후 소스 메시를 Lyra SKM_Manny 로 지정) 권총 애니 전체를 다시 리타게팅(덮어쓰기). 단계마다 저장."""
import unreal, json, traceback
EAL = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools()
R = {'log': []}
dest = '/Game/Furina/P220/Retarget'
try:
    assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(), 'PIE running'
    source = unreal.load_asset('/Game/Characters/Heroes/Mannequin/Meshes/SKM_Manny'); target = unreal.load_asset('/Game/Furina/SK_Furina')
    if not EAL.does_directory_exist(dest): EAL.make_directory(dest)
    p = dest + '/IK_LyraManny'
    rig = unreal.load_asset(p) if EAL.does_asset_exist(p) else T.duplicate_asset('IK_LyraManny', dest, unreal.load_asset('/Game/Furina/Retarget/IK_Manny'))
    unreal.IKRigController.get_controller(rig).set_skeletal_mesh(source); R['log'].append(['rig', EAL.save_loaded_asset(rig, False)])
    p = dest + '/RTG_LyraManny_To_Furina'
    rtg = unreal.load_asset(p) if EAL.does_asset_exist(p) else T.duplicate_asset('RTG_LyraManny_To_Furina', dest, unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina'))
    c = unreal.IKRetargeterController.get_controller(rtg)
    c.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, rig); c.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, source); c.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, rig)
    R['log'].append(['rtg', EAL.save_loaded_asset(rtg, False)])
    items = []
    for root in ('/Game/Characters/Heroes/Mannequin/Animations/Locomotion/Pistol', '/Game/Weapons/Pistol/Animations'):
        for a in EAL.list_assets(root, recursive=True, include_folder=False):
            o = unreal.load_asset(a)
            if isinstance(o, (unreal.AnimSequence, unreal.AnimMontage, unreal.BlendSpace)): items.append(EAL.find_asset_data(a))
    out = unreal.IKRetargetBatchOperation.duplicate_and_retarget(items, source, target, rtg, search='MM_', replace='Furina_', target_path='/Game/Furina/P220/Anim', use_source_path=False, include_referenced_assets=True, overwrite_existing_files=True)
    R['count'] = len(out)
    for a in out: EAL.save_asset(str(a.package_name))
except Exception: R['error'] = traceback.format_exc()[-900:]
print('P220_RETARGET_FIX', json.dumps(R, default=str, ensure_ascii=False))
