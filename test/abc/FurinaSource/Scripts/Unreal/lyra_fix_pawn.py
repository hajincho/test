"""Editor(Lyra, PIE 중지 후): HeroData_Furina.PawnClass 를 진짜 푸리나 폰(Blueprints/ThirdPersonCharacter_BP)으로 고친다. (이전엔 JumpPadCharacterBP 변종을 잘못 지정)
-> Data/lyra_fix_pawn.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fix_pawn.json'
R = {}
try:
    a = unreal.load_asset('/Game/Furina/Lyra/HeroData_Furina')
    cls = unreal.load_class(None, '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP.ThirdPersonCharacter_BP_C'); assert cls
    R['before'] = str(a.get_editor_property('pawn_class')); a.set_editor_property('pawn_class', cls)
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(a, False); R['after'] = str(a.get_editor_property('pawn_class'))
    d = unreal.get_default_object(cls)
    R['has_ammo_prop'] = [p for p in ('FurinaAmmo', 'FurinaReserve', 'FurinaReloading') if p in [str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'))]]
    R['auto_possess_player'] = str(d.get_editor_property('auto_possess_player')); R['auto_possess_ai'] = str(d.get_editor_property('auto_possess_ai')); R['ai_controller_class'] = str(d.get_editor_property('ai_controller_class'))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIX_PAWN', R)
