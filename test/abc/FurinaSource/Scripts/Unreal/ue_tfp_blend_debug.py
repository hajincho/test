import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
for path in ['/Game/Furina/TFP/BS_FurinaStanding','/Game/Furina/TFP/BS_FurinaCrouching']:
 a=unreal.load_asset(path);R[path]={'samples':[x.export_text() for x in a.get_editor_property('SampleData')][:12],'api':[n for n in dir(a) if any(x in n for x in ('sample','resam','triang','validate'))]}
b=unreal.load_asset('/Game/Furina/ABP_Furina');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'AnimGraph');R['nodes']=[(n.get_name(),n.get_editor_property('node').export_text()) for n in e.list_all_nodes() if n.get_name() in ('TFPStanding','TFPCrouching')];json.dump(R,open(os.path.join(D,'tfp_blend_debug.json'),'w'),indent=1)
