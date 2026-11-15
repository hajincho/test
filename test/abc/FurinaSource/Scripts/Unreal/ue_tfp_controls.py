import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 E=unreal.EditorAssetLibrary;T=unreal.AssetToolsHelpers.get_asset_tools();b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');nodes={n.get_name():n for n in ed.list_all_nodes()}
 def w(a,c):assert a.is_valid() and c.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,c)
 def fn(name,path):
  n=next((n for n in ed.list_all_nodes() if n.get_name()==name),None)
  if not n:n=ed.add_call_function_node(path);assert n,path;n.rename(name)
  return n
 ia=unreal.load_asset('/Game/Furina/Input/IA_FurinaCrouch');ia.set_editor_property('triggers',[]);ia.set_editor_property('modifiers',[]);ia.set_editor_property('value_type',unreal.InputActionValueType.BOOLEAN);E.save_loaded_asset(ia,False)
 p='/Game/Furina/Input/IMC_FurinaStance';imc=unreal.load_asset(p) if E.does_asset_exist(p) else T.create_asset('IMC_FurinaStance','/Game/Furina/Input',unreal.InputMappingContext,None);imc.unmap_all();key=unreal.Key();key.set_editor_property('key_name','C');imc.map_key(ia,key);E.save_loaded_asset(imc,False)
 original=[n for n in ed.list_all_nodes() if n.get_name()!='TFP_AddStanceContext' and n.find_input_pin('MappingContext').is_valid()]
 assert original,'No mapping-context registration found'
 original=original[0];add=fn('TFP_AddStanceContext','/Script/EnhancedInput.EnhancedInputSubsystemInterface:AddMappingContext');assert add.find_input_pin('MappingContext').set_pin_value(p+'.IMC_FurinaStance');add.find_input_pin('Priority').set_pin_value('100')
 for p0 in original.find_self_pin().list_connected_pins():w(p0,add.find_self_pin())
 targets=[p0 for p0 in original.find_then_pin().list_connected_pins() if p0.get_owning_node()!=add];original.find_then_pin().break_pin_links();w(original.find_then_pin(),add.find_execute_pin())
 for p0 in targets:w(add.find_then_pin(),p0)
 # Camera: 700 * .67 = 469, and another 50% reduction while shouldered.
 sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);lib=unreal.SubobjectDataBlueprintFunctionLibrary
 for h in sub.k2_gather_subobject_data_for_blueprint(b):
  if str(lib.get_variable_name(lib.get_data(h)))=='CameraBoom':lib.get_associated_object(lib.get_data(h)).set_editor_property('target_arm_length',469.)
 for node,pin,value in [('K2Node_FPT_Lat0','B','0'),('K2Node_FPT_Lat1','B','110'),('K2Node_FPT_TgtZ','A','20')]:assert nodes[node].find_input_pin(pin).set_pin_value(value)
 target=fn('TFP_ArmTarget','/Script/Engine.KismetMathLibrary:SelectFloat');target.find_input_pin('A').set_pin_value('234.5');target.find_input_pin('B').set_pin_value('469');w(nodes['K2Node_FPT_TPSh'].find_result_pin(),target.find_input_pin('bPickA'))
 smooth=fn('TFP_ArmSmooth','/Script/Engine.KismetMathLibrary:FInterpTo');w(nodes['K2Node_FPT_ArmLen'].find_output_pin('TargetArmLength'),smooth.find_input_pin('Current'));w(target.find_result_pin(),smooth.find_input_pin('Target'));w(nodes['K2Node_FPT_Tick'].find_output_pin('DeltaSeconds'),smooth.find_input_pin('DeltaTime'));smooth.find_input_pin('InterpSpeed').set_pin_value('10')
 setter=next((n for n in ed.list_all_nodes() if n.get_name()=='TFP_SetArm'),None)
 if not setter:setter=ed.add_set_member_variable_node('TargetArmLength','/Script/Engine.SpringArmComponent');setter.rename('TFP_SetArm')
 w(nodes['K2Node_FPT_GetBoomT'].find_output_pin('CameraBoom'),setter.find_self_pin());w(smooth.find_result_pin(),setter.find_input_pin('TargetArmLength'));w(nodes['K2Node_FPT_SetFov'].find_then_pin(),setter.find_execute_pin())
 ev=next((n for n in ed.list_all_nodes() if str(n.get_node_title())=='FurinaToggleCrouch'),None)
 if not ev:ev=ed.add_custom_event_node('FurinaToggleCrouch')
 w(ev.find_then_pin(),nodes['K2Node_FPT_CrB'].find_execute_pin());R['registration']=original.get_name()
 del ed,nodes,original,add,target,smooth,setter,ev,targets
 unreal.BlueprintEditorLibrary.compile_blueprint(b);R['status']=str(b.get_editor_property('status'));R['ok']=b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
 if R['ok']:R['saved']=E.save_loaded_asset(b,False)
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_controls.json'),'w'),indent=1)
