"""Use TFP velocity blend spaces for all grounded lower-body motion, including slow aiming."""
import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 b=unreal.load_asset('/Game/Furina/ABP_Furina');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph')
 def w(a,c):assert a.is_valid() and c.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,c)
 def ensure_var(name):
  if name not in [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(b)]:assert e.add_member_variable(name,unreal.BlueprintEditorLibrary.get_basic_type_by_name('real'),'0')
 for name in ('TFPSpeed','TFPDirection','TFPCrouch','TFPGround'):ensure_var(name)
 def fn(name,path):
  n=next((n for n in e.list_all_nodes() if n.get_name()==name),None)
  if not n:n=e.add_call_function_node(path);assert n,path;n.rename(name)
  return n
 owner=fn('TFPOwner','/Script/Engine.AnimInstance:TryGetPawnOwner');velocity=fn('TFPVelocity','/Script/Engine.Actor:GetVelocity');rotation=fn('TFPRotation','/Script/Engine.Actor:K2_GetActorRotation');speed=fn('TFPHorizontalSpeed','/Script/Engine.KismetMathLibrary:VSizeXY');direction=fn('TFPDirectionCalc','/Script/AnimGraphRuntime.KismetAnimationLibrary:CalculateDirection');movement=fn('TFPMovement','/Script/Engine.Pawn:GetMovementComponent');ground=fn('TFPOnGround','/Script/Engine.NavMovementComponent:IsMovingOnGround');crouch=fn('TFPIsCrouched','/Script/Engine.NavMovementComponent:IsCrouching')
 for a,c in [(owner.find_result_pin(),velocity.find_self_pin()),(owner.find_result_pin(),rotation.find_self_pin()),(owner.find_result_pin(),movement.find_self_pin()),(velocity.find_result_pin(),speed.find_input_pin('A')),(velocity.find_result_pin(),direction.find_input_pin('Velocity')),(rotation.find_result_pin(),direction.find_input_pin('BaseRotation')),(movement.find_result_pin(),ground.find_self_pin()),(movement.find_result_pin(),crouch.find_self_pin())]:w(a,c)
 update=e.find_event_node('BlueprintUpdateAnimation');previous=update.find_then_pin()
 existing=next((n for n in e.list_all_nodes() if n.get_name()=='CacheTFPGround'),None)
 old=list(existing.find_then_pin().list_connected_pins()) if existing else list(previous.list_connected_pins())
 old=[p for p in old if not p.get_owning_node().get_name().startswith('CacheTFP')];previous.break_pin_links()
 for name,value,interp in [('TFPSpeed',speed.find_result_pin(),12),('TFPDirection',direction.find_result_pin(),0),('TFPCrouch',crouch.find_result_pin(),10),('TFPGround',ground.find_result_pin(),15)]:
  n=next((n for n in e.list_all_nodes() if n.get_name()=='Cache'+name),None)
  if not n:n=e.add_set_member_variable_node(name);n.rename('Cache'+name)
  if name in ('TFPCrouch','TFPGround'):
   conv=fn(name+'Float','/Script/Engine.KismetMathLibrary:Conv_BoolToDouble');w(value,conv.find_input_pin('InBool'));value=conv.find_result_pin()
  if interp:
   get=e.add_get_member_variable_node(name);smooth=fn(name+'Smooth','/Script/Engine.KismetMathLibrary:FInterpTo');w(get.find_output_pin(name),smooth.find_input_pin('Current'));w(value,smooth.find_input_pin('Target'));w(update.find_output_pin('DeltaTimeX'),smooth.find_input_pin('DeltaTime'));smooth.find_input_pin('InterpSpeed').set_pin_value(str(interp));value=smooth.find_result_pin()
  w(previous,n.find_execute_pin());w(value,n.find_input_pin(name));previous=n.find_then_pin()
 for p in old:w(previous,p)
 ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'AnimGraph');nodes={n.get_name():n for n in ed.list_all_nodes()}
 stand=nodes['TFPStanding'];duck=nodes['TFPCrouching']
 for n in (stand,duck):
  for pin,var in [('X','TFPDirection'),('Y','TFPSpeed')]:get=ed.add_get_member_variable_node(var);w(get.find_output_pin(var),n.find_input_pin(pin))
 groundblend=nodes['AnimGraphNode_TwoWayBlend_1'];crouchblend=nodes['AnimGraphNode_TwoWayBlend_0']
 for n,var in [(groundblend,'TFPGround'),(crouchblend,'TFPCrouch')]:
  v=n.get_editor_property('blend_node');text=v.export_text().replace('AlphaInputType=Curve','AlphaInputType=Float').replace('AlphaInputType=Bool','AlphaInputType=Float');assert v.import_text(text);n.set_editor_property('blend_node',v)
  options=list(n.get_editor_property('show_pin_for_properties'))
  for i,o in enumerate(options):
   if str(o.get_editor_property('PropertyName'))=='Alpha':o.set_editor_property('bShowPin',True);options[i]=o
  n.set_editor_property('show_pin_for_properties',options);oldf=n.get_editor_property('initial_update_function').copy();tmp=oldf.copy();tmp.import_text('(MemberName="FurinaReconstructTemporary")');n.set_editor_property('initial_update_function',tmp);n.set_editor_property('initial_update_function',oldf)
  get=ed.add_get_member_variable_node(var);w(get.find_output_pin(var),n.find_input_pin('Alpha'))
 w(stand.find_output_pin('Pose'),crouchblend.find_input_pin('A'));w(duck.find_output_pin('Pose'),crouchblend.find_input_pin('B'));w(crouchblend.find_output_pin('Pose'),groundblend.find_input_pin('B'));w(groundblend.find_output_pin('Pose'),nodes['AnimGraphNode_LayeredBoneBlend_FP'].find_input_pin('BasePose'))
 del e,ed,nodes,stand,duck,groundblend,crouchblend,n,get,v,options,owner,velocity,rotation,speed,direction,movement,ground,crouch,previous,old,update,value
 unreal.BlueprintEditorLibrary.compile_blueprint(b);R['status']=str(b.get_editor_property('status'));R['ok']=b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
 if R['ok']:R['saved']=unreal.EditorAssetLibrary.save_loaded_asset(b,False)
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_locomotion.json'),'w'),indent=1)
