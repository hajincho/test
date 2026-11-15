import unreal,os,json,runpy
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph')
ev=next((n for n in e.list_all_nodes() if n.get_name()=='M4_RequestReload'),None)
if not ev:ev=e.add_custom_event_node('FurinaRequestReload');ev.rename('M4_RequestReload')
gate=next(n for n in e.list_all_nodes() if n.get_name()=='M4_ReloadGate');assert unreal.BlueprintGraphPinLibrary.try_create_connection(ev.find_then_pin(),gate.find_execute_pin());del e,ev,gate
unreal.BlueprintEditorLibrary.compile_blueprint(b);assert unreal.EditorAssetLibrary.save_loaded_asset(b,False)
runpy.run_path(os.path.join(D,'..','Scripts','Unreal','ue_combat_warnings.py'),run_name='__main__')
