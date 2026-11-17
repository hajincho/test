"""최종 에셋 명칭을 P220 으로: /Game/Furina/P200 -> /Game/Furina/P220, SM_P200_*/M_P200/T_P200_* -> *_P220_*.  이후 의존 에셋 저장."""
import unreal, json, traceback
EAL = unreal.EditorAssetLibrary
R = {'log': []}
try:
    assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(), 'PIE running'
    old, new = '/Game/Furina/P200', '/Game/Furina/P220'
    if EAL.does_directory_exist(new): R['log'].append('P220 dir already exists')
    else: R['log'].append(['rename_dir', EAL.rename_directory(old, new)])
    for a, b in (('SM_P200_Slide', 'SM_P220_Slide'), ('SM_P200_Frame', 'SM_P220_Frame'), ('M_P200', 'M_P220'), ('T_P200_Albedo', 'T_P220_Albedo'), ('T_P200_Metallic', 'T_P220_Metallic'), ('T_P200_Normal', 'T_P220_Normal'), ('T_P200_Roughness', 'T_P220_Roughness')):
        if EAL.does_asset_exist(new + '/' + a): R['log'].append([a, EAL.rename_asset(new + '/' + a, new + '/' + b)])
    R['assets'] = [str(x) for x in EAL.list_assets(new, recursive=True)]
    for p in ('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP', '/Game/Furina/FP/BP_FurinaHUD'):
        bp = unreal.load_asset(p); unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['log'].append([p.split('/')[-1], str(bp.get_editor_property('status'))])
    R['save_dir'] = EAL.save_directory('/Game/Furina', only_if_is_dirty=True, recursive=True)
    R['save_pawn'] = EAL.save_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP', only_if_is_dirty=False)
    R['save_hud'] = EAL.save_asset('/Game/Furina/FP/BP_FurinaHUD', only_if_is_dirty=False)
    R['save_imc'] = EAL.save_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC', only_if_is_dirty=False)
except Exception: R['error'] = traceback.format_exc()[-1200:]
print('P200_RENAME', json.dumps(R, default=str, ensure_ascii=False)[:3000])
