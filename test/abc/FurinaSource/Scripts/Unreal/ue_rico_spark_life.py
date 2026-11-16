"""BP_RicoSpark: the class-default InitialLifeSpan 0.1 set from Python was not saved (spawned instances had life span 0), so the life span is now set at runtime: EventGraph BeginPlay -> SetLifeSpan(0.1).
usage: py ue_rico_spark_life.py [seconds]  (PIE stopped) -> Data/rico_spark_life.json"""
import unreal, json, os, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
LIFE = sys.argv[1] if len(sys.argv) > 1 else '0.1'
def main():
    R = {}
    bp = unreal.load_asset('/Game/Furina/M4/BP_RicoSpark'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'RS_SetLife' not in nodes:
        begin = ed.find_event_node('ReceiveBeginPlay') or unreal.BlueprintEditorLibrary.add_event_override(bp, 'ReceiveBeginPlay', unreal.IntPoint(0, 0)); assert begin
        n = ed.add_call_function_node('/Script/Engine.Actor:SetLifeSpan'); assert n; n.rename('RS_SetLife')
        assert unreal.BlueprintGraphPinLibrary.try_create_connection(begin.find_then_pin(), n.find_execute_pin()); R['added'] = True
    else: n = nodes['RS_SetLife']
    assert n.find_input_pin('InLifespan').set_pin_value(LIFE); R['life'] = n.find_input_pin('InLifespan').get_pin_value()
    del ed, nodes, n
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'rico_spark_life.json'), 'w'), indent=1); print('RICO_SPARK_LIFE', R.get('error', R.get('status'))[-300:])
