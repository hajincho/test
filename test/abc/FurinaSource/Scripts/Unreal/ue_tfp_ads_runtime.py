"""Fresh-load PIE integration test in an unsaved isolated room; no project/map edits."""
import unreal,os,json,time,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';OUT=os.path.abspath(os.path.join(D,'..','..','Saved','Screenshots','WindowsEditor'));os.makedirs(OUT,exist_ok=True)
ED=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);S={'phase':'setup','start':time.monotonic(),'checks':{},'images':[]}
bgmat=unreal.new_object(unreal.Material);bgmat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);exp=unreal.MaterialEditingLibrary.create_material_expression(bgmat,unreal.MaterialExpressionConstant3Vector);exp.set_editor_property('constant',unreal.LinearColor(.25,.25,.25,1));unreal.MaterialEditingLibrary.connect_material_property(exp,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR);unreal.MaterialEditingLibrary.recompile_material(bgmat)
def finish(error=None):
 unreal.unregister_slate_post_tick_callback(S['h']);R={'checks':S['checks'],'images':S['images'],'error':error,'ok':not error and bool(S['checks']) and all(S['checks'].values())}
 for k in ('initial_rounds','reload_rounds','foot_error_cm','crouch_speed','case_count','rounds_after_five','samples'):R[k]=S.get(k)
 R['diagnostics']=S.get('diagnostics',{})
 json.dump(R,open(os.path.join(D,'tfp_ads_runtime.json'),'w'),indent=1);LE.editor_request_end_play();unreal.EditorPythonScripting.set_keep_python_script_alive(True)
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
   bg=a.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(1000,0,200));bg.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));bg.set_actor_scale3d(unreal.Vector(.1,40,40))
   light=a.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,200),unreal.Rotator(pitch=-40,yaw=180));light.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(2)
   fill=a.spawn_actor_from_class(unreal.PointLight,unreal.Vector(200,100,160));fill.get_component_by_class(unreal.PointLightComponent).set_intensity(2)
   pos=unreal.Vector(80,260,155);target=unreal.Vector(0,0,115);cam=a.spawn_actor_from_class(unreal.SceneCapture2D,pos,unreal.MathLibrary.find_look_at_rotation(pos,target));cam.set_actor_label('CombatCapture_TEMP');cap=cam.get_component_by_class(unreal.SceneCaptureComponent2D);rt=unreal.RenderingLibrary.create_render_target2d(ED.get_editor_world(),1200,900,unreal.TextureRenderTargetFormat.RTF_RGBA8);cap.set_editor_property('texture_target',rt);cap.set_editor_property('capture_every_frame',False);cap.set_editor_property('capture_on_movement',False);cap.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR);cap.set_editor_property('fov_angle',60)
   # Use normal PIE: SIE marks its PlayerState as spectator-only and refuses
   # possession, so player movement/crouch and the weapon attachment never start.
   assert unreal.EditorLoadingAndSavingUtils.save_map(ED.get_editor_world(),'/Game/Furina/QA/TFPValidation');bg.static_mesh_component.set_material(0,bgmat)
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
  if S['phase']=='stand':
   flag('FurinaFPWanted').set_active(True);flag('FurinaADS').set_active(True);p.call_method('FurinaViewUpdate')
   if t>.8:
    cam=p.get_editor_property('FPCamera');S['diagnostics']['components']=[(c.get_name(),c.is_active(),[str(x) for x in c.component_tags]) for c in p.get_components_by_class(unreal.ActorComponent) if c.get_name().startswith(('Furina','FP','Follow'))];gr=p.get_editor_property('Grind_Rail_Component_BP');S['diagnostics']['grind']={k:gr.get_editor_property(k) for k in ('UsingRail?','UsingZipline?','RailJumpActive?')};S['diagnostics']['ground']=cm.is_moving_on_ground();S['diagnostics']['cam']=str(cam.get_world_transform());S['diagnostics']['curves']={k:S['mesh'].get_anim_instance().get_curve_value(k) for k in ('AimADS','ViewTP')}
    S['capture'].set_world_location_and_rotation(cam.get_world_location(),cam.get_world_rotation(),False,False);S['capture'].set_editor_property('fov_angle',60);capture('TFPADS_Actual');S['checks']['fp_active']=cam.is_active();gun=p.get_editor_property('FurinaRifle');S['diagnostics']['sight_points']={k:str(cam.get_world_transform().inverse_transform_location(gun.get_world_transform().transform_location(unreal.Vector(*v)))) for k,v in {'rear':[.14139,-11.757165,9.98355],'front':[.0809,30.61,9.8145863]}.items()};hud=S['pc'].get_hud();hud.call_method('FurinaTestRenderHUD');hud.call_method('ReceiveDrawHUD',(1280,720));hud.call_method('FurinaTestFinishHUD');shot();phase('case')
  elif S['phase']=='case':
   cam=p.get_editor_property('FPCamera');S['capture'].set_world_location_and_rotation(cam.get_world_location(),cam.get_world_rotation(),False,False)
   for threshold,label in [(0.01,'01'),(.05,'05'),(.12,'12')]:
    if t>threshold and not S.get('case'+label):capture('TFPActualCase'+label);S['case'+label]=True
   if t>.2:
    cases=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_asset('/Game/Furina/M4/BP_223Case').generated_class());S['checks']['visible_case_actor']=bool(cases);S['diagnostics']['case_positions']=[str(c.get_component_by_class(unreal.StaticMeshComponent).get_world_location()) for c in cases];finish()
 except Exception:finish(traceback.format_exc())
 finally:S['in_tick']=False
S['h']=unreal.register_slate_post_tick_callback(tick);unreal.EditorPythonScripting.set_keep_python_script_alive(True)
