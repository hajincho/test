import unreal,json,traceback,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 bp=unreal.load_asset('/Game/Furina/ABP_Furina');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'AnimGraph')
 seq=next(n for n in unreal.AnimationLibrary.get_nodes_of_class(bp,unreal.AnimGraphNode_SequencePlayer,True) if 'AS_Furina_Walk' in n.get_editor_property('node').export_text())
 options=seq.get_editor_property('show_pin_for_properties')
 for i,p in enumerate(options):
  if str(p.get_editor_property('PropertyName'))=='PlayRate':
   p.set_editor_property('bShowPin',True);options[i]=p
 seq.set_editor_property('show_pin_for_properties',options)
 old=seq.get_editor_property('initial_update_function').copy();temp=old.copy();temp.import_text('(MemberName="FurinaReconstructTemporary")');seq.set_editor_property('initial_update_function',temp);seq.set_editor_property('initial_update_function',old)
 def fn(name,path):
  n=next((a for a in ed.list_all_nodes() if a.get_name()==name),None)
  if not n:n=ed.add_call_function_node(path);assert n,path;n.rename(name)
  return n
 def w(a,b):assert a.is_valid() and b.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,b)
 owner=fn('FurinaCrouchOwner','/Script/Engine.AnimInstance:TryGetPawnOwner');vel=fn('FurinaWalkVelocity','/Script/Engine.Actor:GetVelocity');speed=fn('FurinaWalkSpeed','/Script/Engine.KismetMathLibrary:VSizeXY');ratio=fn('FurinaWalkRate','/Script/Engine.KismetMathLibrary:Divide_DoubleDouble');clamp=fn('FurinaWalkRateClamp','/Script/Engine.KismetMathLibrary:FClamp')
 w(owner.find_result_pin(),vel.find_self_pin());w(vel.find_result_pin(),speed.find_input_pin('A'));w(speed.find_result_pin(),ratio.find_input_pin('A'));ratio.find_input_pin('B').set_pin_value('120');w(ratio.find_result_pin(),clamp.find_input_pin('Value'));clamp.find_input_pin('Min').set_pin_value('.05');clamp.find_input_pin('Max').set_pin_value('1.5');w(clamp.find_result_pin(),seq.find_input_pin('PlayRate'))
 del ed,seq,owner,vel,speed,ratio,clamp
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);R['status']=str(bp.get_editor_property('status'));R['ok']=bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'combat_walk_rate.json'),'w'),indent=1)
