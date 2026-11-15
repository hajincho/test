import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
R['classes']=[n for n in dir(unreal) if any(k in n for k in ('BlendSpace','Blendspace'))]
R['methods']={cn:{n:getattr(getattr(unreal,cn),n).__doc__ for n in dir(getattr(unreal,cn)) if any(s in n.lower() for s in ('sample','blend','parameter'))} for cn in R['classes'] if any(s in cn for s in ('Library','Subsystem','Factory'))}
b=unreal.load_asset('/Game/Furina/ABP_Furina');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'AnimGraph');R['animnodes']=[{'name':n.get_name(),'class':n.get_class().get_name(),'title':str(n.get_node_title()),'inputs':[(str(p.get_pin_name()),[(v.get_owning_node().get_name(),str(v.get_pin_name())) for v in p.list_connected_pins()]) for p in n.list_input_pins()]} for n in ed.list_all_nodes() if n.get_class().get_name().startswith('AnimGraphNode')]
R['actions']=[s for s in ed.list_available_nodes([]) if any(k in s.lower() for k in ('blendspace','블렌드','inert','관성'))]
json.dump(R,open(os.path.join(D,'tfp_api.json'),'w'),indent=1,ensure_ascii=False)
