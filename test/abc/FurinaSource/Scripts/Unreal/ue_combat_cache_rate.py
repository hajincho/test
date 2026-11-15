import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
 b=unreal.load_asset('/Game/Furina/ABP_Furina');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph')
 if 'FurinaWalkRate' not in [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(b)]:assert e.add_member_variable('FurinaWalkRate',unreal.BlueprintEditorLibrary.get_basic_type_by_name('float'),'1.0')
 def fn(name,path):
  n=next((n for n in e.list_all_nodes() if n.get_name()==name),None)
  if not n:n=e.add_call_function_node(path);assert n,path;n.rename(name)
  return n
 def w(a,c):assert a.is_valid() and c.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,c)
 event=e.find_event_node('BlueprintUpdateAnimation') or unreal.BlueprintEditorLibrary.add_event_override(b,'BlueprintUpdateAnimation',unreal.IntPoint(0,0))
 owner=fn('WalkRateOwner','/Script/Engine.AnimInstance:TryGetPawnOwner');velocity=fn('WalkRateVelocity','/Script/Engine.Actor:GetVelocity');speed=fn('WalkRateSpeed','/Script/Engine.KismetMathLibrary:VSizeXY');ratio=fn('WalkRateRatio','/Script/Engine.KismetMathLibrary:Divide_DoubleDouble');clamp=fn('WalkRateClamp','/Script/Engine.KismetMathLibrary:FClamp')
 w(owner.find_result_pin(),velocity.find_self_pin());w(velocity.find_result_pin(),speed.find_input_pin('A'));w(speed.find_result_pin(),ratio.find_input_pin('A'));ratio.find_input_pin('B').set_pin_value('120');w(ratio.find_result_pin(),clamp.find_input_pin('Value'));clamp.find_input_pin('Min').set_pin_value('.05');clamp.find_input_pin('Max').set_pin_value('1.5')
 setter=next((n for n in e.list_all_nodes() if n.get_name()=='CacheWalkRate'),None)
 if not setter:setter=e.add_set_member_variable_node('FurinaWalkRate');setter.rename('CacheWalkRate')
 old=[p for p in event.find_then_pin().list_connected_pins() if p.get_owning_node()!=setter];event.find_then_pin().break_pin_links();w(event.find_then_pin(),setter.find_execute_pin());w(clamp.find_result_pin(),setter.find_input_pin('FurinaWalkRate'))
 for p in old:w(setter.find_then_pin(),p)
 a=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'AnimGraph');seq=next(n for n in unreal.AnimationLibrary.get_nodes_of_class(b,unreal.AnimGraphNode_SequencePlayer,True) if 'AS_Furina_Walk' in n.get_editor_property('node').export_text());get=a.add_get_member_variable_node('FurinaWalkRate');get.rename('CachedWalkRate');seq.find_input_pin('PlayRate').break_pin_links();w(get.find_output_pin('FurinaWalkRate'),seq.find_input_pin('PlayRate'));a.remove_nodes([n for n in a.list_all_nodes() if n.get_name() in ('FurinaWalkVelocity','FurinaWalkSpeed','FurinaWalkRate','FurinaWalkRateClamp')])
 del e,a,event,owner,velocity,speed,ratio,clamp,setter,old,seq,get
 unreal.BlueprintEditorLibrary.compile_blueprint(b);assert b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR;assert unreal.EditorAssetLibrary.save_loaded_asset(b,False)
 json.dump({'status':str(b.get_editor_property('status')),'ok':True},open(os.path.join(D,'combat_cached_rate.json'),'w'))
main()
