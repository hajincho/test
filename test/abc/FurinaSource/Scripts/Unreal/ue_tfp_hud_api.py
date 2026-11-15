import unreal,json
b=unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');R={'self':[s for s in e.list_available_nodes([]) if any(x in s for x in ('셀프','자신','SelfReference'))]};json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\tfp_hud_api.json','w'),indent=1,ensure_ascii=False)
