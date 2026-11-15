import unreal,json
bp=unreal.load_asset('/Game/Furina/ABP_Furina');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'AnimGraph')
R={'actions':[str(x) for x in ed.list_available_nodes([]) if any(y in str(x) for y in ('커브','곡선','Curve','Self','자신','자체'))]}
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\combat_anim_actions.json','w'),ensure_ascii=False,indent=1)
