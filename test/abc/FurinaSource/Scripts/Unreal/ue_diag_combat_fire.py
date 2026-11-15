import unreal,json
b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');nodes={n.get_name():n for n in e.list_all_nodes()}
ev=e.add_custom_event_node('FurinaInspectFire');prev=ev.find_then_pin()
for var,source in [('DiagAim','K2Node_FPF_AimingF'),('DiagCanFire','K2Node_FPF_CanFire'),('DiagShoulder','K2Node_FPF_ShOnF'),('DiagReady','M4_Ready')]:
 e.add_member_variable(var,unreal.BlueprintEditorLibrary.get_basic_type_by_name('bool'),'false');n=e.add_set_member_variable_node(var);assert unreal.BlueprintGraphPinLibrary.try_create_connection(prev,n.find_execute_pin());assert unreal.BlueprintGraphPinLibrary.try_create_connection(nodes[source].find_result_pin(),n.find_input_pin(var));prev=n.find_then_pin()
del e,n,nodes,ev,prev
unreal.BlueprintEditorLibrary.compile_blueprint(b)
