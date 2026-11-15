import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
R={'api':{n:getattr(unreal.BlueprintGraphEditor,n).__doc__ for n in dir(unreal.BlueprintGraphEditor) if not n.startswith('_')}}
bp=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
R['nodes']=[(n.get_name(),str(n.get_node_title())) for n in ed.list_all_nodes()]
R['status']=str(bp.get_editor_property('status'))
sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);lib=unreal.SubobjectDataBlueprintFunctionLibrary
R['components']={}
for h in sub.k2_gather_subobject_data_for_blueprint(bp):
 d=lib.get_data(h);n=str(lib.get_variable_name(d));o=lib.get_associated_object(d)
 if n=='CameraBoom':R['boom']=o.get_editor_property('target_arm_length')
 R['components'][n]=str(o)
json.dump(R,open(os.path.join(D,'combat_probe.json'),'w'),indent=1)


