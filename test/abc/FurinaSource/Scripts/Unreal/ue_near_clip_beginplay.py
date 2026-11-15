"""Guarantees the 2 cm near clip plane at runtime (2026-11-15): ThirdPersonCharacter_BP BeginPlay -> ExecuteConsoleCommand 'r.SetNearClipPlane 2'
(the DefaultEngine.ini NearClipPlane=4 entry only applies after a restart; the rear sight of the iron sights is ~7 cm from the eye in ADS)."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    names = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'FPN_NearClip' not in names:
        begin = ed.find_event_node('ReceiveBeginPlay') or unreal.BlueprintEditorLibrary.add_event_override(bp, 'ReceiveBeginPlay', unreal.IntPoint(0, 0))
        ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); begin = ed.find_event_node('ReceiveBeginPlay')
        cmd = ed.add_call_function_node('/Script/Engine.KismetSystemLibrary:ExecuteConsoleCommand'); assert cmd; cmd.rename('FPN_NearClip')
        cmd.find_input_pin('Command').set_pin_value('r.SetNearClipPlane 2')
        old = list(begin.find_then_pin().list_connected_pins()); begin.find_then_pin().break_pin_links()
        assert unreal.BlueprintGraphPinLibrary.try_create_connection(begin.find_then_pin(), cmd.find_execute_pin())
        for p in old: assert unreal.BlueprintGraphPinLibrary.try_create_connection(cmd.find_then_pin(), p)
        R['added'] = True
    del ed, names
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\near_clip_beginplay.json', 'w'), indent=1)
print('NEAR_CLIP', R.get('status'), R.get('error', '')[:300])
