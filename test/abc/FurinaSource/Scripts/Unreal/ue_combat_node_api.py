import unreal,json
bp=unreal.load_asset('/Game/Furina/ABP_Furina');g=unreal.BlueprintEditorLibrary.list_graphs(bp)
n=unreal.AnimationLibrary.get_nodes_of_class(bp,unreal.AnimGraphNode_ModifyCurve,True)[0]
R={'graph_api':[k for k in dir(g[0]) if not k.startswith('_')], 'node_api':[k for k in dir(n) if not k.startswith('_')]}
for k in ('nodes','Nodes'):
 try:R[k]=str(g[0].get_editor_property(k))[:200]
 except Exception as e:R[k]=str(e)
R['blueprint_api']={k:getattr(unreal.BlueprintEditorLibrary,k).__doc__ for k in dir(unreal.BlueprintEditorLibrary) if any(x in k for x in ('reconstruct','refresh','variable'))}
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\combat_node_api.json','w'),indent=1)
