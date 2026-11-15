import unreal,runpy,os,uuid
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource';b=unreal.load_asset('/Game/Furina/ABP_Furina');variables=('TFPSpeed','TFPDirection','TFPCrouch','TFPGround','TFPHandWalk','TFPHandIdle');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');old=next(n for n in e.list_all_nodes() if n.get_name()=='CacheTFPHandIdle');continuation=[(p.get_owning_node().get_name(),str(p.get_pin_name())) for p in old.find_then_pin().list_connected_pins()]
for graph in ('EventGraph','AnimGraph'):
 ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,graph);kill=[n for n in ed.list_all_nodes() if n.get_class().get_name() in ('K2Node_VariableGet','K2Node_VariableSet') and any(n.find_output_pin(v).is_valid() or n.find_input_pin(v).is_valid() for v in variables)]
 if kill:
  for n in kill:n.rename('RemovedTFP_'+uuid.uuid4().hex)
  ed.remove_nodes(kill)
for name in variables:e.remove_member_variable(name);e.add_member_variable(name,unreal.BlueprintEditorLibrary.get_basic_type_by_name('real'),'0')
del e,ed,old,kill
for script in ('ue_tfp_locomotion.py','ue_tfp_hands.py'):runpy.run_path(os.path.join(D,'Scripts','Unreal',script),run_name='__main__')
e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');nodes={n.get_name():n for n in e.list_all_nodes()}
for name,pin in continuation:assert unreal.BlueprintGraphPinLibrary.try_create_connection(nodes['CacheTFPHandIdle'].find_then_pin(),nodes[name].find_input_pin(pin))
del e,nodes
unreal.BlueprintEditorLibrary.compile_blueprint(b);assert b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR;assert unreal.EditorAssetLibrary.save_loaded_asset(b,False)
