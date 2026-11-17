"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 1인칭에서 오래 떨어지면 3인칭으로 바뀌는 문제 수정.
원인: 푸리나 폰 EventGraph 의 시점 타이머(K2Node_FPV_Upd, 0.05초)가 Forced = (레일/집라인/레일점프) OR AirFast 로 3인칭을 강제한다.
 AirFast = (공중) AND (속도(3D, 낙하 속도 포함) + 3인칭일 때 +10000 보정 > 1200). 낙하 속도가 1200cm/s 를 넘으면 강제 3인칭, 3인칭이 되면 보정으로 착지할 때까지 유지.
수정: K2Node_FPV_Forced.B 에서 AirFast 연결을 끊고 false 로 둔다(레일/집라인/레일점프 강제 3인칭은 그대로).   -> Data/lyra_fix_fall_view.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fix_fall_view.json'
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    f = nodes['K2Node_FPV_Forced']; pin = f.find_input_pin('B')
    R['before'] = [str(pin.get_pin_value()), [c.get_owning_node().get_name() for c in pin.list_connected_pins()]]
    pin.break_pin_links(); R['set'] = bool(pin.set_pin_value('false'))
    R['after'] = [str(pin.get_pin_value()), [c.get_owning_node().get_name() for c in pin.list_connected_pins()]]
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['error_nodes'] = [n.get_name() for n in ed.list_nodes_with_errors()][:10]
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIX_FALL', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
