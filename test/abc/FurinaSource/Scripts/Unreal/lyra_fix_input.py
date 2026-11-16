"""LYRA 에디터(헤드리스): 푸리나 폰 BeginPlay 의 입력 매핑 추가 경로가 `GetController -> Cast To PlayerController` 라서, Lyra(폰 스폰 -> BeginPlay -> 그 뒤 possess)에서는
컨트롤러가 비어 IMC(이동/사격/재장전...)가 추가되지 않는다. `GetPlayerController(0)` 을 캐스트 입력으로 연결해 고친다. 컴파일/저장. -> Data/lyra_fix_input.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fix_input.json'
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    cast = nodes['K2Node_DynamicCast_0']; getc = nodes['K2Node_CallFunction_9']
    R['cast_exec_from'] = [c.get_owning_node().get_name() + ' ' + str(c.get_owning_node().get_node_title()).replace('\n', ' ') for c in cast.find_input_pin('execute').list_connected_pins()]
    R['getc_title'] = str(getc.get_node_title())
    if 'FIN_GetPC0' not in nodes:
        pc = ed.add_call_function_node('/Script/Engine.GameplayStatics:GetPlayerController'); pc.rename('FIN_GetPC0'); pc.find_input_pin('PlayerIndex').set_pin_value('0')
        obj = cast.find_input_pin('Object'); obj.break_pin_links()
        assert unreal.BlueprintGraphPinLibrary.try_create_connection(pc.find_result_pin(), obj), 'link'
        R['rewired'] = True
    else: R['rewired'] = 'already'
    R['cast_object_from'] = [c.get_owning_node().get_name() for c in cast.find_input_pin('Object').list_connected_pins()]
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIX_INPUT', R)
import sys
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')    # 헤드리스 실행에서만 종료, 열린 에디터에서는 `py <파일> keep`
