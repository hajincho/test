"""Verify the actual player walk and visible blink; all changes are temporary PIE state."""
import unreal,os,json,time,traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
OUT=os.path.abspath(os.path.join(D,'..','..','Saved','Screenshots','WindowsEditor')).replace('\\','/')
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
s={'phase':'start','started':time.monotonic(),'rows':[],'shots':[]}
s['camera_before']=editor.get_level_viewport_camera_info()
def shot(world,label):
    unreal.SystemLibrary.execute_console_command(world,'HighResShot 960x720 filename="'+OUT+'/WalkBlinkFinal_'+label+'.png"')
    s['shots'].append(label)
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(s['h'])
    R={'error':error,'rows':s['rows'],'screenshots':s['shots'],'diagnostics':s.get('diagnostics',{})}
    a=[r for r in s['rows'] if 4<=r['t']<=9 and 110<r['speed']<130 and r['walk']>.99 and r['idle']<.01]
    gaps=[abs(a[i]['hips_z']-a[i-1]['hips_z']) for i in range(1,len(a)) if a[i]['t']-a[i-1]['t']<.025]
    R['steady_walk_frames']=len(a);R['max_steady_walk_height_step_cm']=max(gaps,default=999)
    R['peak_blink']=max((r['blink'] for r in s['rows']),default=0)
    R['peak_rendered_morph']=max((r['morph'] for r in s['rows']),default=0)
    R['ok']=error is None and len(a)>100 and R['max_steady_walk_height_step_cm']<.8 and R['peak_rendered_morph']>.98
    with open(os.path.join(D,'walk_blink_runtime_validation.json'),'w',encoding='utf-8') as f:json.dump(R,f,indent=1)
    level.editor_request_end_play()
    editor.set_level_viewport_camera_info(*s['camera_before'])
    print('WALK_BLINK_RUNTIME_DONE',R['ok'],error or '')
def tick(dt):
    try:
        if s['phase']=='start':
            if time.monotonic()-s['started']<3:return
            level.editor_play_simulate();s['phase']='wait';return
        w=editor.get_game_world()
        if not w:return
        pawn=unreal.GameplayStatics.get_player_pawn(w,0)
        if not isinstance(pawn,unreal.Character):
            pawn=next((p for p in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Character) if any(c.get_name()=='FurinaMesh' for c in p.get_components_by_class(unreal.SkeletalMeshComponent))),None)
        if not pawn:
            if time.monotonic()-s['started']>60:finish('Furina character not found')
            return
        mesh=next(c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='FurinaMesh')
        pc=unreal.GameplayStatics.get_player_controller(w,0)
        if s['phase']=='wait':
            def props(obj,names):
                out={}
                for n in names:
                    try:out[n]=str(obj.get_editor_property(n))
                    except Exception:pass
                return out
            s['diagnostics']={'world':w.get_path_name(),'pawn':pawn.get_path_name(),
                'characters':[p.get_path_name() for p in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Character)],
                'actor':props(pawn,('custom_time_dilation','primary_actor_tick','hidden')),
                'mesh':props(mesh,('pause_anims','no_skeleton_update','global_anim_rate_scale','primary_component_tick','anim_class','visible','render_static')),
                'movement':props(pawn.character_movement,('movement_mode','active','primary_component_tick')),
                'mesh_tick':mesh.is_component_tick_enabled(),'movement_tick':pawn.character_movement.is_component_tick_enabled()}
            if pc:pc.possess(pawn)
            else:pawn.spawn_default_controller()
            pawn.set_editor_property('use_controller_rotation_yaw',False)
            mesh.set_editor_property('visibility_based_anim_tick_option',unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
            # This project's start-menu widget pauses PIE on BeginPlay.
            # Unpause only this temporary test world, never change the menu asset.
            unreal.GameplayStatics.set_game_paused(w,False)
            s.update(phase='run',time=0,world_start=unreal.GameplayStatics.get_time_seconds(w))
        unreal.GameplayStatics.set_game_paused(w,False)
        t=unreal.GameplayStatics.get_time_seconds(w)-s['world_start'];s['time']=t
        if time.monotonic()-s['started']>75:
            finish('game world failed to advance during runtime verification');return
        pawn.character_movement.max_walk_speed=120
        if 3<=t<9.5:pawn.add_movement_input(unreal.Vector(1,0,0),1,True)
        if pc:
            pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=180,roll=0))
            for boom in pawn.get_components_by_class(unreal.SpringArmComponent):
                boom.set_editor_property('target_arm_length',85)
                boom.set_editor_property('socket_offset',unreal.Vector(0,0,mesh.get_socket_location('Head').z+6-pawn.get_actor_location().z))
        eye_target=mesh.get_socket_location('Head')+unreal.Vector(0,0,6)
        eye_camera=eye_target+unreal.Vector(85,0,0)
        editor.set_level_viewport_camera_info(eye_camera,unreal.MathLibrary.find_look_at_rotation(eye_camera,eye_target))
        ai=mesh.get_anim_instance()
        if ai:
            row={'t':round(t,4),'speed':pawn.get_velocity().length(),'walk':ai.get_curve_value('FurinaWalk'),'idle':ai.get_curve_value('FurinaIdle'),'blink':ai.get_curve_value('IdleBlink'),'morph':mesh.get_morph_target('IdleBlink'),
                 'hips_z':mesh.get_socket_transform('Hips',unreal.RelativeTransformSpace.RTS_COMPONENT).translation.z}
            s['rows'].append(row)
            if t>=1 and 'Open' not in s['shots']:shot(w,'Open')
            if row['morph']>.98 and 'Closed' not in s['shots']:shot(w,'Closed')
        if t>=10.5:finish()
    except Exception:finish(traceback.format_exc())
s['h']=unreal.register_slate_post_tick_callback(tick)
