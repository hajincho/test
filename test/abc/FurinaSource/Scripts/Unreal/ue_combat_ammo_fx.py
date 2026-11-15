"""Blueprint-only magazine, reload gate, muzzle flash and physical empty-case ejection."""
import unreal,os,json,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';DEST='/Game/Furina/M4';R={}
def main():
 E=unreal.EditorAssetLibrary;T=unreal.AssetToolsHelpers.get_asset_tools();S=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);L=unreal.SubobjectDataBlueprintFunctionLibrary
 def wire(a,b):assert a.is_valid() and b.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,b)
 def part(bp,name,cls,parent):
  hs={str(L.get_variable_name(L.get_data(h))):h for h in S.k2_gather_subobject_data_for_blueprint(bp)}
  if name not in hs:
   h,err=S.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs.get(parent,next(iter(hs.values()))),new_class=cls,blueprint_context=bp));assert not str(err),str(err);S.rename_subobject(h,unreal.Text(name));hs[name]=h
  return L.get_associated_object(L.get_data(hs[name]))
 def actor(name):
  p=DEST+'/'+name
  if E.does_asset_exist(p):return unreal.load_asset(p)
  f=unreal.BlueprintFactory();f.set_editor_property('parent_class',unreal.Actor);return T.create_asset(name,DEST,unreal.Blueprint,f)
 for name,mesh,scale,life in [('BP_M4Flash','/Engine/BasicShapes/Cone',(.04,.04,.14),.045),('BP_223Case',DEST+'/SM_223Case',(1,1,1),4.)]:
  bp=actor(name);root=part(bp,'FXRoot',unreal.SceneComponent,'DefaultSceneRoot');body=part(bp,'FXMesh',unreal.StaticMeshComponent,'FXRoot');body.set_static_mesh(unreal.load_asset(mesh));body.set_editor_property('relative_scale3d',unreal.Vector(*scale));body.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
  if name=='BP_M4Flash':
   body.set_editor_property('relative_rotation',unreal.Rotator(pitch=0,yaw=0,roll=-90));body.set_material(0,unreal.load_asset(DEST+'/M_MuzzleFlash'));body.set_collision_profile_name('NoCollision');body.set_editor_property('cast_shadow',False)
   light=part(bp,'FlashLight',unreal.PointLightComponent,'FXRoot');light.set_editor_property('intensity',700.);light.set_editor_property('attenuation_radius',140.);light.set_editor_property('light_color',unreal.Color(255,130,35,255))
  else:
   body.set_collision_profile_name('PhysicsActor');body.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN,unreal.CollisionResponseType.ECR_IGNORE);body.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY,unreal.CollisionResponseType.ECR_IGNORE);body.set_simulate_physics(True)
   ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
   def n(name,func):
    x=next((a for a in ed.list_all_nodes() if a.get_name()==name),None)
    if not x:x=ed.add_call_function_node(func);assert x;x.rename(name)
    return x
   begin=ed.find_event_node('ReceiveBeginPlay') or unreal.BlueprintEditorLibrary.add_event_override(bp,'ReceiveBeginPlay',unreal.IntPoint(0,0));get=ed.add_get_member_variable_node('FXMesh');vel=n('CaseVelocity','/Script/Engine.PrimitiveComponent:SetPhysicsLinearVelocity');imp=n('CaseSpin','/Script/Engine.PrimitiveComponent:SetPhysicsAngularVelocityInDegrees')
   # Local ejection transformed at spawn to the gun's right/up; physics supplies gravity and bounce.
   right=n('CaseRight','/Script/Engine.Actor:GetActorRightVector');fwd=n('CaseForward','/Script/Engine.Actor:GetActorForwardVector');mul=n('CaseRightSpeed','/Script/Engine.KismetMathLibrary:Multiply_VectorFloat');up=n('CaseUp','/Script/Engine.KismetMathLibrary:Add_VectorVector')
   wire(fwd.find_result_pin(),mul.find_input_pin('A'));mul.find_input_pin('B').set_pin_value('-220');wire(mul.find_result_pin(),up.find_input_pin('A'));up.find_input_pin('B').set_pin_value('0,0,100')
   wire(get.find_output_pin('FXMesh'),vel.find_self_pin());wire(get.find_output_pin('FXMesh'),imp.find_self_pin());wire(up.find_result_pin(),vel.find_input_pin('NewVel'));imp.find_input_pin('NewAngVel').set_pin_value('650,420,900');wire(begin.find_then_pin(),vel.find_execute_pin());wire(vel.find_then_pin(),imp.find_execute_pin())
   del ed,n,begin,get,vel,imp,right,fwd,mul,up
  del root,body
  unreal.BlueprintEditorLibrary.compile_blueprint(bp);assert bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
  unreal.get_default_object(bp.generated_class()).set_editor_property('initial_life_span',life);assert E.save_loaded_asset(bp,False)
 # The character owns ammunition independently of view, aim and crouch state.
 bp=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
 def getnode(name):return next((a for a in ed.list_all_nodes() if a.get_name()==name),None)
 def fn(name,path):
  x=getnode('M4_'+name)
  if not x:x=ed.add_call_function_node(path);assert x,path;x.rename('M4_'+name)
  return x
 def variable(name,setting=False):
  tag='M4_'+('Set' if setting else 'Get')+name;x=getnode(tag)
  if not x:x=(ed.add_set_member_variable_node if setting else ed.add_get_member_variable_node)(name);x.rename(tag)
  return x
 for name,cat,val in [('FurinaAmmo','int','30'),('FurinaReloading','bool','false')]:
  if name not in [str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]:
   typ=unreal.BlueprintEditorLibrary.get_basic_type_by_name(cat);assert ed.add_member_variable(name,typ,val)
 ammo=variable('FurinaAmmo');reloading=variable('FurinaReloading');has=fn('HasAmmo','/Script/Engine.KismetMathLibrary:Greater_IntInt');wire(ammo.find_output_pin('FurinaAmmo'),has.find_input_pin('A'));has.find_input_pin('B').set_pin_value('0')
 no=fn('NotReloading','/Script/Engine.KismetMathLibrary:Not_PreBool');wire(reloading.find_output_pin('FurinaReloading'),no.find_input_pin('A'));ok=fn('Ready','/Script/Engine.KismetMathLibrary:BooleanAND');wire(has.find_result_pin(),ok.find_input_pin('A'));wire(no.find_result_pin(),ok.find_input_pin('B'))
 gate=getnode('M4_FireGate') or ed.add_branch_node();gate.rename('M4_FireGate');wire(ok.find_result_pin(),gate.find_input_pin('Condition'))
 can=getnode('K2Node_FPF_CanB');face=getnode('K2Node_FPF_FaceAim');can.find_output_pin('then').break_pin_links();wire(can.find_output_pin('then'),gate.find_execute_pin());wire(gate.find_output_pin('then'),face.find_execute_pin())
 dec=fn('UseRound','/Script/Engine.KismetMathLibrary:Subtract_IntInt');wire(ammo.find_output_pin('FurinaAmmo'),dec.find_input_pin('A'));dec.find_input_pin('B').set_pin_value('1');sa=variable('FurinaAmmo',True);wire(dec.find_result_pin(),sa.find_input_pin('FurinaAmmo'))
 recoil=getnode('K2Node_FPF_Recoil');recoil.find_then_pin().break_pin_links();wire(recoil.find_then_pin(),sa.find_execute_pin())
 selfnode=next(n for n in ed.list_all_nodes() if n.get_class().get_name()=='K2Node_Self');selfpin=selfnode.find_output_pin('self')
 # Reload requests only start while below capacity and not already reloading.
 full=fn('NotFull','/Script/Engine.KismetMathLibrary:Less_IntInt');wire(ammo.find_output_pin('FurinaAmmo'),full.find_input_pin('A'));full.find_input_pin('B').set_pin_value('30');reloadok=fn('ReloadReady','/Script/Engine.KismetMathLibrary:BooleanAND');wire(full.find_result_pin(),reloadok.find_input_pin('A'));wire(no.find_result_pin(),reloadok.find_input_pin('B'))
 rg=getnode('M4_ReloadGate') or ed.add_branch_node();rg.rename('M4_ReloadGate');wire(reloadok.find_result_pin(),rg.find_input_pin('Condition'))
 montage=getnode('K2Node_FP_ReloadMontage');old=list(montage.find_execute_pin().list_connected_pins());montage.find_execute_pin().break_pin_links()
 for p in old:
  if p.get_owning_node().get_name()!='M4_ReloadTimer':wire(p,rg.find_execute_pin())
 sr=variable('FurinaReloading',True);sr.find_input_pin('FurinaReloading').set_pin_value('true');wire(rg.find_output_pin('then'),sr.find_execute_pin())
 timer=fn('ReloadTimer','/Script/Engine.KismetSystemLibrary:K2_SetTimer');wire(selfpin,timer.find_input_pin('Object'));timer.find_input_pin('FunctionName').set_pin_value('FurinaFinishReload');timer.find_input_pin('Time').set_pin_value('3.0');timer.find_input_pin('bLooping').set_pin_value('false');wire(sr.find_then_pin(),timer.find_execute_pin());wire(timer.find_then_pin(),montage.find_execute_pin())
 finish=getnode('M4_ReloadFinish')
 if not finish:finish=ed.add_custom_event_node('FurinaFinishReload');finish.rename('M4_ReloadFinish')
 done=getnode('M4_FillMagazine') or ed.add_set_member_variable_node('FurinaAmmo');done.rename('M4_FillMagazine');done.find_input_pin('FurinaAmmo').set_pin_value('30');clear=getnode('M4_ReloadDone') or ed.add_set_member_variable_node('FurinaReloading');clear.rename('M4_ReloadDone');clear.find_input_pin('FurinaReloading').set_pin_value('false');wire(finish.find_then_pin(),done.find_execute_pin());wire(done.find_then_pin(),clear.find_execute_pin())
 # Spawn the two visual actors at measured gun points only after a successful shot.
 rifle=getnode('K2Node_FPF_RifleXf');Xf=rifle.find_result_pin();prev=sa.find_then_pin()
 for tag,point,asset in [('Flash',(0,40.625201,4.849452),'BP_M4Flash'),('Case',(-2,-6.75879,4.52615),'BP_223Case')]:
  loc=fn(tag+'Point','/Script/Engine.KismetMathLibrary:TransformLocation');wire(Xf,loc.find_input_pin('T'));loc.find_input_pin('Location').set_pin_value(','.join(map(str,point)))
  rot=fn(tag+'Rotation','/Script/Engine.SceneComponent:K2_GetComponentRotation');wire(getnode('K2Node_FPF_GetRifleM').find_output_pin('FurinaRifle'),rot.find_self_pin());xf=fn(tag+'Transform','/Script/Engine.KismetMathLibrary:MakeTransform');wire(loc.find_result_pin(),xf.find_input_pin('Location'));wire(rot.find_result_pin(),xf.find_input_pin('Rotation'));xf.find_input_pin('Scale').set_pin_value('1,1,1')
  begin=fn(tag+'Spawn','/Script/Engine.GameplayStatics:BeginDeferredActorSpawnFromClass');assert begin.find_input_pin('ActorClass').set_pin_value(DEST+'/'+asset+'.'+asset+'_C');wire(xf.find_result_pin(),begin.find_input_pin('SpawnTransform'));wire(selfpin,begin.find_input_pin('Owner'));begin.find_input_pin('CollisionHandlingOverride').set_pin_value('AlwaysSpawn');wire(prev,begin.find_execute_pin())
  end=fn(tag+'Finish','/Script/Engine.GameplayStatics:FinishSpawningActor');wire(begin.find_result_pin(),end.find_input_pin('Actor'));wire(xf.find_result_pin(),end.find_input_pin('SpawnTransform'));wire(begin.find_then_pin(),end.find_execute_pin());prev=end.find_then_pin()
 R['status_before_compile']=str(bp.get_editor_property('status'))
 # Release graph wrappers before compiling (UE's Python graph wrapper lifetime requirement).
 del ed,ammo,reloading,has,no,ok,gate,can,face,dec,sa,selfnode,selfpin,full,reloadok,rg,montage,old,sr,timer,finish,done,clear,rifle,Xf,prev,loc,rot,xf,begin,end
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);R['status']=str(bp.get_editor_property('status'));R['ok']=bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'combat_ammo_fx.json'),'w'),indent=1)





