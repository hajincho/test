import unreal,json
b=unreal.load_asset('/Game/Furina/M4/BP_223Case')
def tune():
 e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');n=next(n for n in e.list_all_nodes() if n.get_name()=='TFPCaseDirection');assert n.find_input_pin('Direction').set_pin_value('-140,180,130')
tune();unreal.BlueprintEditorLibrary.compile_blueprint(b);assert unreal.EditorAssetLibrary.save_loaded_asset(b,False);json.dump({'ok':True,'ejection_cm_s':[-140,180,130]},open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\tfp_case_final.json','w'))
