"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 푸리나 폰에 LyraHeroComponent 추가.
이유: ULyraPawnExtensionComponent::InitializeAbilitySystem 은 LyraHeroComponent 만 호출한다(LyraHeroComponent.cpp:164). 없으면 폰의 ASC 가 초기화되지 않아 체력이 0/0 이고
HealthSet/팀/어빌리티가 폰에 연결되지 않는다(PIE 프로브: 푸리나 health [0,0], 마네킹 봇 [100,100]).   -> Data/lyra_furina_add_hero.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_furina_add_hero.json'
R = {}
P = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
try:
    bp = unreal.load_asset(P)
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    hs = {str(L.get_variable_name(L.get_data(h))): h for h in S.k2_gather_subobject_data_for_blueprint(bp)}
    R['before'] = sorted(hs)
    if 'LyraHero' not in hs and not any(isinstance(L.get_associated_object(L.get_data(h)), unreal.LyraHeroComponent) for h in hs.values()):
        root = S.k2_gather_subobject_data_for_blueprint(bp)[0]
        h, err = S.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.LyraHeroComponent, blueprint_context=bp)); R['add_err'] = str(err)
        S.rename_subobject(h, unreal.Text('LyraHero')); R['added'] = True
    else: R['added'] = 'exists'
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); R['error_nodes'] = [n.get_name() for n in ed.list_nodes_with_errors()][:20]
    R['after'] = sorted(str(L.get_variable_name(L.get_data(h))) for h in S.k2_gather_subobject_data_for_blueprint(bp))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_ADD_HERO', R.get('added'), R.get('status'), R.get('saved'), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
