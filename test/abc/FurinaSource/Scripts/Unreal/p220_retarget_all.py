"""Lyra 권총 애니메이션 전부(Locomotion/Pistol 107개 + Weapons/Pistol 몽타주/시퀀스)를 RTG_Manny_To_Furina 로 Furina 에 리타게팅."""
import unreal, json, traceback
EAL = unreal.EditorAssetLibrary
R = {'log': []}
try:
    assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(), 'PIE running'
    source = unreal.load_asset('/Game/Characters/Heroes/Mannequin/Meshes/SKM_Manny'); target = unreal.load_asset('/Game/Furina/SK_Furina'); rtg = unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
    items = []; names = []
    for root in ('/Game/Characters/Heroes/Mannequin/Animations/Locomotion/Pistol', '/Game/Weapons/Pistol/Animations'):
        for p in EAL.list_assets(root, recursive=True, include_folder=False):
            o = unreal.load_asset(p)
            if isinstance(o, (unreal.AnimSequence, unreal.AnimMontage, unreal.BlendSpace)):
                items.append(EAL.find_asset_data(p)); names.append(p.split('/')[-1].split('.')[0])
    R['source_count'] = len(items)
    out = unreal.IKRetargetBatchOperation.duplicate_and_retarget(items, source, target, rtg, search='MM_', replace='Furina_', target_path='/Game/Furina/P220/Anim', use_source_path=False, include_referenced_assets=True, overwrite_existing_files=False)
    R['count'] = len(out)
    for a in out: EAL.save_asset(str(a.package_name))
    R['total_in_dest'] = len(EAL.list_assets('/Game/Furina/P220/Anim', recursive=True))
except Exception: R['error'] = traceback.format_exc()[-900:]
print('P220_RETARGET_ALL', json.dumps(R, default=str, ensure_ascii=False)[:1500])
