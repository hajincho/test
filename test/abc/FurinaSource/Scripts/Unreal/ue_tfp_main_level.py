"""Final input and instruction visibility checks on the actual startup level; no original map save."""
import unreal,json,os,time,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';S={'phase':'setup','start':time.monotonic(),'checks':{},'diag':{}};ED=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def finish(error=None):
 unreal.unregister_slate_post_tick_callback(S['h']);json.dump({'checks':S['checks'],'diagnostics':S['diag'],'error':error,'ok':not error and all(S['checks'].values())},open(os.path.join(D,'tfp_main_level.json'),'w'),indent=1);LE.editor_request_end_play()
def tick(dt):
 if S.get('busy'):return
 S['busy']=True
 try:
  if time.monotonic()-S['start']>75:finish('timeout');return
  if S['phase']=='setup':
   S['phase']='loading';assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/3DPlatformerGameBundle/Levels/ExampleLevel');LE.editor_request_begin_play();S['phase']='wait';return
  if S['phase']=='wait':
   w=ED.get_game_world()
   if not w:return
   pc=unreal.GameplayStatics.get_player_controller(w,0);p=unreal.GameplayStatics.get_player_character(w,0) if pc else None
   if not isinstance(p,unreal.Character):return
   S.update(world=w,pc=pc,pawn=p,phase='settle',at=unreal.GameplayStatics.get_time_seconds(w));return
  w=S['world'];p=S['pawn'];t=unreal.GameplayStatics.get_time_seconds(w)-S['at'];unreal.GameplayStatics.set_game_paused(w,False)
  if S['phase']=='settle' and t>2:
   S['diag']['pawn']=p.get_path_name();S['diag']['rail']=p.get_editor_property('Grind_Rail_Component_BP').get_editor_property('UsingRail?');S['diag']['mode']=str(p.character_movement.movement_mode);S['diag']['can_crouch']=p.can_crouch();S['diag']['nav']=str(p.character_movement.get_editor_property('nav_agent_props'))
   cls=unreal.load_asset('/Game/3DPlatformerGameBundle/Widgets/Guide_Widget_WBP').generated_class();guides=unreal.WidgetLibrary.get_all_widgets_of_class(w,cls,False);S['diag']['guide_count']=len(guides);S['checks']['main_guide_collapsed']=all(x.get_visibility()==unreal.SlateVisibility.COLLAPSED for x in guides)
   allwidgets=unreal.WidgetLibrary.get_all_widgets_of_class(w,unreal.UserWidget,False);S['diag']['widgets']=[(x.get_class().get_path_name(),str(x.get_visibility())) for x in allwidgets]
   notes=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.TextRenderActor);S['diag']['text_actor_count']=len(notes);S['checks']['world_notes_hidden']=all(a.get_editor_property('hidden') for a in notes)
   S['diag']['subsystems']=[x.get_path_name() for x in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if not x.get_name().startswith('Default__')];S['input']=next(x for x in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if not x.get_name().startswith('Default__') and x.has_mapping_context(unreal.load_asset('/Game/Furina/Input/IMC_FurinaStance'))==100);S['ia']=unreal.load_asset('/Game/Furina/Input/IA_FurinaCrouch');S['before']=p.character_movement.is_crouching();S['input'].inject_input_vector_for_action(S['ia'],unreal.Vector(1,0,0),[],[]);S['phase']='crouch';S['at']=unreal.GameplayStatics.get_time_seconds(w)
  elif S['phase']=='crouch':
   S['input'].inject_input_vector_for_action(S['ia'],unreal.Vector(1 if t<.1 else 0,0,0),[],[])
   if t>.8:
    S['checks']['C_toggles_on_actual_map']=p.character_movement.is_crouching()!=S['before'];mesh=p.get_editor_property('FurinaMesh');S['diag']['wants_crouch']=p.character_movement.get_editor_property('bWantsToCrouch');S['diag']['crouch_weight']=mesh.get_anim_instance().get_editor_property('TFPCrouch');S['diag']['capsule_half_height']=p.capsule_component.get_scaled_capsule_half_height();S['checks']['actual_crouch_pose']=S['diag']['crouch_weight']>.95;finish()
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
S['h']=unreal.register_slate_post_tick_callback(tick)
