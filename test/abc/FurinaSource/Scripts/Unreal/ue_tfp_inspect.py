import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
for path,graph in [('/Game/Furina/FP/BP_FurinaHUD','EventGraph'),('/Game/Furina/ABP_Furina','AnimGraph'),('/Game/Furina/M4/BP_223Case','EventGraph')]:
 b=unreal.load_asset(path);e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,graph)
 R[path]=[(n.get_name(),str(n.get_node_title()),[(str(p.get_pin_name()),str(p.get_pin_value()),[(x.get_owning_node().get_name(),str(x.get_pin_name())) for x in p.list_connected_pins()]) for p in n.list_all_pins()]) for n in e.list_all_nodes() if 'Loop' in n.get_name() or 'FP' in n.get_name() or 'Case' in path]
R['caseCDO']=str(unreal.get_default_object(unreal.load_asset('/Game/Furina/M4/BP_223Case').generated_class()).get_actor_scale3d())
json.dump(R,open(os.path.join(D,'tfp_inspect.json'),'w'),indent=1)

