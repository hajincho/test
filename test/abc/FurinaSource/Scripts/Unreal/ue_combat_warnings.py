import unreal,json
b=unreal.load_asset('/Game/Furina/ABP_Furina');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'AnimGraph');R={'warnings':[(n.get_name(),n.error_msg) for n in e.list_nodes_with_warnings()]};json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\combat_warnings.json','w'),indent=1)
