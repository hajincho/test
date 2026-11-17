"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 푸리나 폰의 LyraHeroComponent 템플릿 DefaultInputMappings 에 푸리나 IMC 등록.
이유: ULyraHeroComponent::InitializePlayerInput 이 ClearAllMappings() 로 기존 매핑을 지운 뒤 DefaultInputMappings 만 다시 넣는다(LyraHeroComponent.cpp:244-266).
푸리나 BP 가 BeginPlay 에서 넣은 Default_IMC / IMC_FurinaStance 가 그때 지워져 V·좌클릭 등 커스텀 입력이 죽는다.   -> Data/lyra_furina_hero_imc.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_furina_hero_imc.json'
R = {}
P = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
IMCS = [('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC', 0), ('/Game/Furina/Input/IMC_FurinaStance', 100)]
try:
    bp = unreal.load_asset(P)
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    comp = None
    for h in S.k2_gather_subobject_data_for_blueprint(bp):
        o = L.get_associated_object(L.get_data(h))
        if isinstance(o, unreal.LyraHeroComponent): comp = o
    R['comp'] = str(comp)
    entries = []
    for path, prio in IMCS:
        e = unreal.InputMappingContextAndPriority()
        e.set_editor_property('input_mapping', unreal.load_asset(path)); e.set_editor_property('priority', prio)
        try: e.set_editor_property('b_register_with_settings', False)
        except Exception as ex: R['reg_err'] = str(ex)[:100]
        entries.append(e)
    comp.set_editor_property('default_input_mappings', entries)
    R['after'] = [str(x.get_editor_property('input_mapping')) + ' p' + str(x.get_editor_property('priority')) for x in comp.get_editor_property('default_input_mappings')]
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_HERO_IMC', R.get('after'), R.get('saved'), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
