"""Lyra 권총 애니메이션(Manny 스켈레톤)을 기존 RTG_Manny_To_Furina 로 Furina 에 리타게팅 (새로 만들지 않고 지정된 Lyra 애니 사용).
대상: 권총 장착/사격/재장전 몽타주 + 정지/걷기/조깅 시퀀스.  결과 -> /Game/Furina/P220/Anim/*  (이름 접두 AS_/AM_ -> *_Furina_)"""
import unreal, json, traceback
EAL = unreal.EditorAssetLibrary
R = {'log': []}
try:
    assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(), 'PIE running'
    source = unreal.load_asset('/Game/Characters/Heroes/Mannequin/Meshes/SKM_Manny'); target = unreal.load_asset('/Game/Furina/SK_Furina')
    rtg = unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina'); assert source and target and rtg, 'assets'
    names = ['/Game/Weapons/Pistol/Animations/AM_MM_Pistol_Equip', '/Game/Weapons/Pistol/Animations/AM_MM_Pistol_Fire', '/Game/Weapons/Pistol/Animations/AM_MM_Pistol_Reload', '/Game/Weapons/Pistol/Animations/AM_MM_Pistol_DryFire']
    loc = '/Game/Characters/Heroes/Mannequin/Animations/Locomotion/Pistol/'
    for n in ('MM_Pistol_Idle_Hipfire', 'MM_Pistol_Idle_ADS', 'MM_Pistol_Walk_Fwd', 'MM_Pistol_Walk_Bwd', 'MM_Pistol_Walk_Left', 'MM_Pistol_Walk_Right', 'MM_Pistol_Jog_Fwd', 'MM_Pistol_Jog_Bwd', 'MM_Pistol_Jog_Left', 'MM_Pistol_Jog_Right', 'MM_Pistol_Crouch_Idle', 'MM_Pistol_Crouch_Walk_Fwd'):
        names.append(loc + n)
    items = []
    for p in names:
        if EAL.does_asset_exist(p): items.append(EAL.find_asset_data(p))
        else: R['log'].append('missing ' + p)
    dest = '/Game/Furina/P220/Anim'
    out = unreal.IKRetargetBatchOperation.duplicate_and_retarget(items, source, target, rtg, search='MM_', replace='Furina_', target_path=dest, use_source_path=False, include_referenced_assets=True, overwrite_existing_files=True)
    R['count'] = len(out); R['assets'] = [str(x.package_name) for x in out]
    for a in out: EAL.save_asset(str(a.package_name))
except Exception: R['error'] = traceback.format_exc()[-1200:]
print('P220_RETARGET', json.dumps(R, default=str, ensure_ascii=False)[:3500])
