import unreal,json
b=unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD')
def fix():
 e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');ns={n.get_name():n for n in e.list_all_nodes()};d=ns['TFPTest_Draw'];d.rename('TFPTest_DiscardedDraw');e.remove_nodes([d]);ev=e.add_custom_event_node('FurinaTestFinishHUD');ev.rename('TFPTest_FinishHUD');assert unreal.BlueprintGraphPinLibrary.try_create_connection(ev.find_then_pin(),ns['TFPTest_End'].find_execute_pin())
fix();unreal.BlueprintEditorLibrary.compile_blueprint(b);json.dump({'ok':b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR,'status':str(b.get_editor_property('status'))},open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\tfp_hud_fixture.json','w'))
