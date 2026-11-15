"""Fresh-load PIE integration test in an unsaved isolated room; no project/map edits."""
import unreal,os,json,time,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';OUT=os.path.abspath(os.path.join(D,'..','..','Saved','Screenshots','WindowsEditor'));os.makedirs(OUT,exist_ok=True)
ED=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);S={'phase':'setup','start':time.monotonic(),'checks':{},'images':[]}
def finish(error=None):
 unreal.unregister_slate_post_tick_callback(S['h']);R={'checks':S['checks'],'images':S['images'],'error':error,'ok':not error and bool(S['checks']) and all(S['checks'].values())}
 for k in ('initial_rounds','reload_rounds','foot_error_cm','crouch_speed','case_count','rounds_after_five','samples'):R[k]=S.get(k)
 R['diagnostics']=S.get('diagnostics',{})
 json.dump(R,open(os.path.join(D,'tfp_runtime.json'),'w'),indent=1);LE.editor_request_end_play();unreal.EditorPythonScripting.set_keep_python_script_alive(True)
def flag(tag):return S['pawn'].get_editor_property(tag) if tag=='FurinaFPWanted' else next(c for c in S['pawn'].get_components_by_tag(unreal.ActorComponent,tag))
def ammo():return S['pawn'].get_editor_property('FurinaAmmo')
def shot():S['pawn'].call_method('FurinaRifleShot')
def capture(label):
 S['capture'].capture_scene();unreal.RenderingLibrary.export_render_target(S['world'],S['rt'],OUT,'Combat_'+label+'.png');S['images'].append(os.path.join(OUT,'Combat_'+label+'.png'))
def tick(dt):
 if S.get('in_tick'):return
 S['in_tick']=True
 try:
  if time.monotonic()-S['start']>110:finish('runtime test timeout');return
  if S['phase']=='setup':
   S['phase']='busy'
   grbp=unreal.load_asset('/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP');unreal.get_default_object(grbp.generated_class()).set_editor_property('UsingRail?',False)
   unreal.EditorLoadingAndSavingUtils.new_blank_map(False);a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
   floor=a.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-10));floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(30,30,.2))
   pawn=a.spawn_actor_from_class(unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP').generated_class(),unreal.Vector(0,0,96));pawn.set_actor_label('CombatTest_TEMP')
   light=a.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,200),unreal.Rotator(pitch=-40,yaw=180));light.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(2)
   fill=a.spawn_actor_from_class(unreal.PointLight,unreal.Vector(200,100,160));fill.get_component_by_class(unreal.PointLightComponent).set_intensity(2)
   pos=unreal.Vector(80,260,155);target=unreal.Vector(0,0,115);cam=a.spawn_actor_from_class(unreal.SceneCapture2D,pos,unreal.MathLibrary.find_look_at_rotation(pos,target));cam.set_actor_label('CombatCapture_TEMP');cap=cam.get_component_by_class(unreal.SceneCaptureComponent2D);rt=unreal.RenderingLibrary.create_render_target2d(ED.get_editor_world(),1200,900,unreal.TextureRenderTargetFormat.RTF_RGBA8);cap.set_editor_property('texture_target',rt);cap.set_editor_property('capture_every_frame',False);cap.set_editor_property('capture_on_movement',False);cap.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR);cap.set_editor_property('fov_angle',60)
   # Use normal PIE: SIE marks its PlayerState as spectator-only and refuses
   # possession, so player movement/crouch and the weapon attachment never start.
   LE.editor_request_begin_play();S['phase']='wait';return
  if S['phase']=='wait':
   world=ED.get_game_world()
   if not world:return
   pawn=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Character) if a.get_actor_label()=='CombatTest_TEMP'),None)
   if not pawn:return
   pc=unreal.GameplayStatics.get_player_controller(world,0);pc.possess(pawn);pawn.call_method('FurinaTestClearTraversal');pc.set_control_rotation(unreal.Rotator());gr=pawn.get_editor_property('Grind_Rail_Component_BP');gr.set_component_tick_enabled(False);unreal.GameplayStatics.set_game_paused(world,False);pawn.character_movement.set_movement_mode(unreal.MovementMode.MOVE_WALKING)
   for c in pawn.get_components_by_class(unreal.ActorComponent):
    if 'Homing' in c.get_name():c.set_component_tick_enabled(False)
   mesh=next(c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='FurinaMesh');cam=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.SceneCapture2D) if a.get_actor_label()=='CombatCapture_TEMP');cap=cam.get_component_by_class(unreal.SceneCaptureComponent2D)
   for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent):c.set_editor_property('visibility_based_anim_tick_option',unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
   pp=cap.get_editor_property('post_process_settings')
   for k,v in [('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',0),('auto_exposure_max_brightness',0),('override_bloom_intensity',True),('bloom_intensity',0)]:pp.set_editor_property(k,v)
   cap.set_editor_property('post_process_settings',pp)
   S.update(phase='stand',world=world,pawn=pawn,mesh=mesh,capture=cap,rt=cap.get_editor_property('texture_target'),phase_start=unreal.GameplayStatics.get_time_seconds(world));S['pc']=pc;S['input']=next(x for x in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if not x.get_name().startswith('Default__'));S['ia']=unreal.load_asset('/Game/Furina/Input/IA_FurinaCrouch');S['samples']=[];S['diagnostics']={};S['initial_rounds']=ammo()
   gun=next(c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='FurinaRifle')
   S['diagnostics']={'gun_asset':str(gun.get_skinned_asset()),'gun_scale':str(gun.get_world_transform()),'gun_grip':str(gun.get_socket_transform('Grip')),'can_crouch':str(pawn.can_crouch()),'nav':str(pawn.character_movement.get_editor_property('nav_agent_props'))}
   return
  w=S['world'];p=S['pawn'];cm=p.character_movement;t=unreal.GameplayStatics.get_time_seconds(w)-S['phase_start'];unreal.GameplayStatics.set_game_paused(w,False)
  cm.activate(True);cm.set_component_tick_enabled(True)
  def phase(name):S.update(phase=name,phase_start=unreal.GameplayStatics.get_time_seconds(w))
  def inject(value):S['input'].inject_input_vector_for_action(S['ia'],unreal.Vector(value,0,0),[],[])
  def move():p.add_movement_input(unreal.Vector(1,0,0),1,True)
  def feet():return {n:S['mesh'].get_socket_location(n).z for n in ('Left-ankle','Right-ankle')}
  def snap(label,fp=False):
   if fp:
    fc=next(c for c in p.get_components_by_class(unreal.CameraComponent) if c.get_name()=='FPCamera');S['capture'].set_world_location_and_rotation(fc.get_world_location(),fc.get_world_rotation(),False,False);S['capture'].set_editor_property('fov_angle',fc.field_of_view)
   else:
    pos=p.get_actor_location()+unreal.Vector(100,260,40);target=p.get_actor_location()+unreal.Vector(0,0,15);S['capture'].set_world_location_and_rotation(pos,unreal.MathLibrary.find_look_at_rotation(pos,target),False,False)
   capture(label)
  if S['phase']=='stand' and t>1.5:
   S['checks']['initial_30_120']=ammo()==30 and p.get_editor_property('FurinaReserve')==120
   S['checks']['stance_context_priority_100']=S['input'].has_mapping_context(unreal.load_asset('/Game/Furina/Input/IMC_FurinaStance'))==100
   S['feet_before']=feet();snap('TFPStanding');inject(1);phase('crouch')
  elif S['phase']=='crouch':
   if t<.15:inject(1)
   else:inject(0)
   if t>1.1:
    S['checks']['input_C_crouches']=cm.is_crouching();S['checks']['crouch_pose_weight']=S['mesh'].get_anim_instance().get_editor_property('TFPCrouch')>.95;S['checks']['ground_pose_weight']=S['mesh'].get_anim_instance().get_editor_property('TFPGround')>.95;S['checks']['crouch_capsule_58']=abs(p.capsule_component.get_scaled_capsule_half_height()-58)<.1;S['checks']['crouch_walk_90']=abs(cm.max_walk_speed_crouched-90)<.1
    S['diagnostics']['feet_stand']=S['feet_before'];S['diagnostics']['feet_crouch']=feet();S['diagnostics']['anim_crouch']={k:S['mesh'].get_anim_instance().get_editor_property(k) for k in ('TFPCrouch','TFPGround','TFPSpeed')};snap('TFPCrouching');inject(1);phase('standup')
  elif S['phase']=='standup':
   if t<.15:inject(1)
   else:inject(0)
   if t>.8:S['checks']['input_C_stands']=not cm.is_crouching();phase('walk')
  elif S['phase'] in ('walk','shoulderwalk'):
   move();ai=S['mesh'].get_anim_instance();local=S['mesh'].get_world_transform().inverse_transform_location(S['mesh'].get_socket_location('Right-ankle'));S['samples'].append({'phase':S['phase'],'t':t,'speed':p.get_velocity().length(),'cached':ai.get_editor_property('TFPSpeed'),'ground':ai.get_editor_property('TFPGround'),'foot':[local.x,local.y,local.z]})
   if t>2:
    rows=[r for r in S['samples'] if r['phase']==S['phase'] and r['t']>.6];span=max(r['foot'][1] for r in rows)-min(r['foot'][1] for r in rows);S['diagnostics'][S['phase']]={'foot_swing_cm':span,'last':rows[-1]};S['checks'][S['phase']+'_feet_move']=span>5;snap('TFP'+S['phase'])
    if S['phase']=='walk':flag('FurinaShoulderAuto').set_active(False);flag('FurinaShoulder').set_active(True);unreal.SystemLibrary.set_timer(p,'FurinaRifleShot',60,True);phase('shoulderwalk')
    else:
     S['checks']['shoulder_speed_60']=abs(cm.max_walk_speed-60)<.1;boom=p.get_editor_property('CameraBoom');S['checks']['shoulder_arm_234_5']=abs(boom.target_arm_length-234.5)<.5;S['diagnostics']['shoulder_offset']=str(boom.socket_offset);cm.stop_movement_immediately();unreal.SystemLibrary.clear_timer(p,'FurinaRifleShot');flag('FurinaShoulder').set_active(False);flag('FurinaADS').set_active(True);flag('FurinaFPWanted').set_active(True);p.call_method('FurinaViewUpdate');phase('ads')
  elif S['phase']=='ads' and t>1:
   snap('TFPADS',True);S['diagnostics']['fp_wanted']=flag('FurinaFPWanted').is_active();S['diagnostics']['fp_active']=flag('FurinaFPCamera').is_active();S['diagnostics']['hud']=str(S['pc'].get_hud());unreal.SystemLibrary.execute_console_command(w,'Shot showui',S['pc']);shot();S['case_shot_time']=unreal.GameplayStatics.get_time_seconds(w);phase('case')
  elif S['phase']=='case':
   cls=unreal.load_asset('/Game/Furina/M4/BP_223Case').generated_class();cases=unreal.GameplayStatics.get_all_actors_of_class(w,cls)
   if cases:
    body=cases[-1].get_component_by_class(unreal.StaticMeshComponent);S['diagnostics'].setdefault('case_frames',[]).append({'t':t,'velocity':str(body.get_physics_linear_velocity()),'location':str(body.get_world_location())})
   if t>.01 and not S.get('case0'):snap('TFPCase01',True);S['case0']=True
   if t>.05 and not S.get('case1'):snap('TFPCase05',True);S['case1']=True
   if t>.12 and not S.get('case2'):snap('TFPCase12',True);S['case2']=True
   if t>.25:
    S['checks']['case_ejects']=bool(cases) and any('240' in r['velocity'] for r in []) if False else bool(cases) and body.get_physics_linear_velocity().length()>50
    flag('FurinaADS').set_active(False);flag('FurinaFPWanted').set_active(False);S['lastshot']=-1;S['shots']=1;phase('firefive')
  elif S['phase']=='firefive':
   if S['shots']<5 and t-S['lastshot']>.12:shot();S['shots']+=1;S['lastshot']=t
   if S['shots']==5 and t>1:
    S['checks']['five_shots_25_120']=ammo()==25 and p.get_editor_property('FurinaReserve')==120;p.call_method('FurinaRequestReload');phase('reload')
  elif S['phase']=='reload' and t>3.3:
   S['checks']['reload_30_115']=ammo()==30 and p.get_editor_property('FurinaReserve')==115
   boom=p.get_editor_property('CameraBoom');S['checks']['normal_arm_469']=abs(boom.target_arm_length-469)<.5
   S['diagnostics']['final_ammo']=[ammo(),p.get_editor_property('FurinaReserve')];finish()
 except Exception:finish(traceback.format_exc())
 finally:S['in_tick']=False
S['h']=unreal.register_slate_post_tick_callback(tick);unreal.EditorPythonScripting.set_keep_python_script_alive(True)
