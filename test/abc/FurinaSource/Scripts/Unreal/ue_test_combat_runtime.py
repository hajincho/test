"""Fresh-load PIE integration test in an unsaved isolated room; no project/map edits."""
import unreal,os,json,time,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';OUT=os.path.abspath(os.path.join(D,'..','..','Saved','Screenshots','WindowsEditor'));os.makedirs(OUT,exist_ok=True)
ED=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);S={'phase':'setup','start':time.monotonic(),'checks':{},'images':[]}
def finish(error=None):
 unreal.unregister_slate_post_tick_callback(S['h']);R={'checks':S['checks'],'images':S['images'],'error':error,'ok':not error and bool(S['checks']) and all(S['checks'].values())}
 for k in ('initial_rounds','reload_rounds','foot_error_cm','crouch_speed','case_count','rounds_after_five'):R[k]=S.get(k)
 R['diagnostics']=S.get('diagnostics',{})
 json.dump(R,open(os.path.join(D,'combat_runtime.json'),'w'),indent=1);LE.editor_request_end_play();unreal.EditorPythonScripting.set_keep_python_script_alive(True)
def flag(tag):return next(c for c in S['pawn'].get_components_by_tag(unreal.ActorComponent,tag))
def ammo():return S['pawn'].get_editor_property('FurinaAmmo')
def shot():S['pawn'].call_method('FurinaRifleShot')
def capture(label):
 S['capture'].capture_scene();unreal.RenderingLibrary.export_render_target(S['world'],S['rt'],OUT,'Combat_'+label+'.png');S['images'].append(os.path.join(OUT,'Combat_'+label+'.png'))
def tick(dt):
 try:
  if time.monotonic()-S['start']>110:finish('runtime test timeout');return
  if S['phase']=='setup':
   unreal.EditorLoadingAndSavingUtils.new_blank_map(False);a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
   floor=a.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-10));floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(30,30,.2))
   pawn=a.spawn_actor_from_class(unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP').generated_class(),unreal.Vector(0,0,96));pawn.set_actor_label('CombatTest_TEMP')
   light=a.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,200),unreal.Rotator(pitch=-40,yaw=180));light.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(2)
   fill=a.spawn_actor_from_class(unreal.PointLight,unreal.Vector(200,100,160));fill.get_component_by_class(unreal.PointLightComponent).set_intensity(.2)
   pos=unreal.Vector(80,260,155);target=unreal.Vector(0,0,115);cam=a.spawn_actor_from_class(unreal.SceneCapture2D,pos,unreal.MathLibrary.find_look_at_rotation(pos,target));cam.set_actor_label('CombatCapture_TEMP');cap=cam.get_component_by_class(unreal.SceneCaptureComponent2D);rt=unreal.RenderingLibrary.create_render_target2d(ED.get_editor_world(),1200,900,unreal.TextureRenderTargetFormat.RTF_RGBA8);cap.set_editor_property('texture_target',rt);cap.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR);cap.set_editor_property('fov_angle',60)
   # Use normal PIE: SIE marks its PlayerState as spectator-only and refuses
   # possession, so player movement/crouch and the weapon attachment never start.
   LE.editor_request_begin_play();S['phase']='wait';return
  if S['phase']=='wait':
   world=ED.get_game_world()
   if not world:return
   pawn=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Character) if a.get_actor_label()=='CombatTest_TEMP'),None)
   if not pawn:return
   pc=unreal.GameplayStatics.get_player_controller(world,0);pc.possess(pawn);unreal.GameplayStatics.set_game_paused(world,False);pawn.character_movement.set_movement_mode(unreal.MovementMode.MOVE_WALKING)
   for c in pawn.get_components_by_class(unreal.ActorComponent):
    if 'Homing' in c.get_name():c.set_component_tick_enabled(False)
   mesh=next(c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='FurinaMesh');cam=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.SceneCapture2D) if a.get_actor_label()=='CombatCapture_TEMP');cap=cam.get_component_by_class(unreal.SceneCaptureComponent2D)
   for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent):c.set_editor_property('visibility_based_anim_tick_option',unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
   pp=cap.get_editor_property('post_process_settings')
   for k,v in [('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',0),('auto_exposure_max_brightness',0),('override_bloom_intensity',True),('bloom_intensity',0)]:pp.set_editor_property(k,v)
   cap.set_editor_property('post_process_settings',pp)
   S.update(phase='stand',world=world,pawn=pawn,mesh=mesh,capture=cap,rt=cap.get_editor_property('texture_target'),phase_start=unreal.GameplayStatics.get_time_seconds(world));S['initial_rounds']=ammo()
   gun=next(c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='FurinaRifle')
   S['diagnostics']={'gun_asset':str(gun.get_skinned_asset()),'gun_scale':str(gun.get_world_transform()),'gun_grip':str(gun.get_socket_transform('Grip')),'can_crouch':str(pawn.can_crouch()),'nav':str(pawn.character_movement.get_editor_property('nav_agent_props'))}
   return
  w=S['world'];p=S['pawn'];cm=p.character_movement;t=unreal.GameplayStatics.get_time_seconds(w)-S['phase_start'];unreal.GameplayStatics.set_game_paused(w,False)
  cm.activate(True);cm.set_component_tick_enabled(True)
  def phase(name):S.update(phase=name,phase_start=unreal.GameplayStatics.get_time_seconds(w))
  if S['phase']=='stand' and t>1.5:
   S['checks']['starts_with_30']=ammo()==30;S['feet_before']={n:S['mesh'].get_socket_location(n).z for n in ('Left-ankle','Right-ankle')};gun=next(c for c in p.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='FurinaRifle');S['diagnostics']['gun_standing']=str(gun.get_world_transform());S['diagnostics']['mesh_standing']=str(S['mesh'].get_world_transform());S['diagnostics']['cm_active']=cm.is_active();capture('Standing');S['lastshot']=-1;S['shots']=0;phase('firefive')
  elif S['phase']=='firefive':
   if S['shots']<5 and t-S['lastshot']>.09:
    shot();S['shots']+=1;S['lastshot']=t
    cls=unreal.load_asset('/Game/Furina/M4/BP_M4Flash').generated_class();S['checks']['muzzle_flash_spawns']=len(unreal.GameplayStatics.get_all_actors_of_class(w,cls))>0
   if S['shots']==5 and t>1:
    S['rounds_after_five']=ammo();S['checks']['five_shots_consume_five']=ammo()==25
    cls=unreal.load_asset('/Game/Furina/M4/BP_223Case').generated_class();S['case_count']=len(unreal.GameplayStatics.get_all_actors_of_class(w,cls));S['checks']['empty_cases_spawn']=S['case_count']>=4
    p.call_method('FurinaRequestReload');before=ammo();shot();S['checks']['reload_blocks_shot']=ammo()==before and p.get_editor_property('FurinaReloading');phase('reload')
  elif S['phase']=='reload' and t>3.2:
   S['reload_rounds']=ammo();S['checks']['reload_refills_30']=ammo()==30 and not p.get_editor_property('FurinaReloading')
   cm.velocity=unreal.Vector(90,0,0);before=ammo();shot();S['checks']['moving_hip_blocked']=ammo()==before
   unreal.SystemLibrary.set_timer(p,'FurinaRifleShot',60,True)
   cm.velocity=unreal.Vector(600,0,0);shot();S['checks']['sprint_enters_shoulder_without_shot']=flag('FurinaShoulder').is_active() and ammo()==before;cm.stop_movement_immediately();phase('shoulder')
  elif S['phase']=='shoulder' and t>.5:
   flag('FurinaShoulderAuto').set_active(False);flag('FurinaShoulder').set_active(True)
   p.call_method('FurinaInspectFire');S['diagnostics']['fire_conditions']={n:p.get_editor_property(n) for n in ('DiagAim','DiagCanFire','DiagShoulder','DiagReady')}
   S['diagnostics']['shoulder_component']=str(flag('FurinaShoulder').get_path_name());S['diagnostics']['shoulder_property']=str(p.get_editor_property('FurinaShoulder').get_path_name());S['diagnostics']['shoulder_active']=flag('FurinaShoulder').is_active()
   gun=next(c for c in p.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='FurinaRifle');S['diagnostics']['gun_after_reload']=str(gun.get_world_transform());S['diagnostics']['grip_after_reload']=str(gun.get_socket_transform('Grip'));S['diagnostics']['feet_before']=S['feet_before']
   capture('Shoulder');cm.velocity=unreal.Vector(60,0,0);before=ammo();shot();S['checks']['moving_shoulder_can_fire']=ammo()==before-1;cm.stop_movement_immediately();unreal.SystemLibrary.clear_timer(p,'FurinaRifleShot');flag('FurinaShoulder').set_active(False);flag('FurinaShoulderAuto').set_active(False);S['diagnostics']['mode_before_crouch']=str(cm.get_editor_property('movement_mode'));S['diagnostics']['can_crouch_now']=p.can_crouch();p.crouch();S['diagnostics']['wants_crouch']=str(cm.get_editor_property('bWantsToCrouch'));phase('crouch')
  elif S['phase']=='crouch' and t>1:
   S['diagnostics']['feet_crouched']={n:S['mesh'].get_socket_location(n).z for n in S['feet_before']};S['diagnostics']['crouch_curves']={n:S['mesh'].get_anim_instance().get_curve_value(n) for n in ('Crouch','FurinaIdle','FurinaWalk')};S['diagnostics']['mesh_crouched']=str(S['mesh'].get_world_transform())
   S['crouch_speed']=cm.get_editor_property('max_walk_speed_crouched');S['checks']['crouch_walk_speed_90']=abs(S['crouch_speed']-90)<.1;S['checks']['crouch_capsule_58']=abs(p.capsule_component.get_scaled_capsule_half_height()-58)<.1;capture('Crouching');S['foot_error_cm']=max(abs(S['mesh'].get_socket_location(n).z-S['feet_before'][n]) for n in S['feet_before']);S['diagnostics']['crouching']=cm.is_crouching();S['diagnostics']['mode_crouched']=str(cm.get_editor_property('movement_mode'));p.un_crouch();phase('empty');S['lastshot']=-1
  elif S['phase']=='empty':
   if t-S['lastshot']>.09:shot();S['lastshot']=t
   if ammo()==0:
    shot();S['checks']['empty_magazine_stops_at_zero']=ammo()==0;finish()
   elif t>7:finish('failed to empty magazine')
 except Exception:finish(traceback.format_exc())
S['h']=unreal.register_slate_post_tick_callback(tick);unreal.EditorPythonScripting.set_keep_python_script_alive(True)


