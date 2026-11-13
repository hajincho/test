"""Temporary live hair verification; stop PIE and restore the viewport afterward."""
import unreal, os, json, time, math, traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
TIPS=['F_17_1_L','F_17_1_R','CF_2_L','CF_2_R','DM_5_1']
state={'phase':'open','started':time.monotonic(),'rows':[],'images':[]}
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
state['camera_before']=editor.get_level_viewport_camera_info()

def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    R={'error':error,'rows':state['rows'],'screenshots':state['images']}
    if R['rows']:
        R['max_speed']=max(r['speed'] for r in R['rows'])
        R['flow_range']=[min(r['flow'] for r in R['rows']),max(r['flow'] for r in R['rows'])]
        R['peak_blink']=max(r['blink'] for r in R['rows'])
        R['phases']={}
        for label,lo,hi in (('idle',1.5,3.5),('walk',6,7.9),('run',10,12.9),('stopped',19,22)):
            a=[r for r in R['rows'] if lo<=r['t']<=hi]
            if not a:continue
            R['phases'][label]={}
            for n in TIPS:
                mean=[sum(r[n][j] for r in a)/len(a) for j in range(3)]
                R['phases'][label][n]={'sway_radius_cm':max(math.dist(r[n],mean) for r in a),'max_sample_step_cm':max((math.dist(a[i][n],a[i-1][n]) for i in range(1,len(a))),default=0)}
        R['ok']=error is None and R['max_speed']>500 and R['flow_range'][1]<=1.001
    with open(os.path.join(D,'soft_hair_runtime.json'),'w',encoding='utf-8') as f:json.dump(R,f,indent=1)
    level.editor_request_end_play()
    editor.set_level_viewport_camera_info(*state['camera_before'])
    print('SOFT_HAIR_RUNTIME_DONE',R.get('ok',False),error or '')

def tick(delta):
    try:
        if state['phase']=='open':
            if time.monotonic()-state['started']<3:return
            level.editor_play_simulate();state['phase']='wait';return
        w=editor.get_game_world()
        if not w:return
        pawn=unreal.GameplayStatics.get_player_pawn(w,0)
        if not isinstance(pawn,unreal.Character):
            pawn=next((p for p in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Character) if any(c.get_name()=='FurinaMesh' for c in p.get_components_by_class(unreal.SkeletalMeshComponent))),None)
        if not pawn:
            if time.monotonic()-state['started']>60:finish('Furina character not found')
            return
        comp=next(c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='FurinaMesh')
        if state['phase']=='wait':
            pc=unreal.GameplayStatics.get_player_controller(w,0)
            if pc:pc.possess(pawn)
            else:pawn.spawn_default_controller()
            comp.set_editor_property('visibility_based_anim_tick_option',unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
            state.update(phase='run',elapsed=0,frames=0,origin=pawn.get_actor_location(),direction=1)
        state['elapsed']+=unreal.GameplayStatics.get_world_delta_seconds(w);state['frames']+=1;t=state['elapsed']
        moving=4<=t<17
        pawn.character_movement.max_walk_speed=600 if 8<=t<13 else 120
        if moving:
            dx=pawn.get_actor_location().x-state['origin'].x
            if abs(dx)>250:state['direction']=-1 if dx>0 else 1
            pawn.add_movement_input(unreal.Vector(state['direction'],0,0),1,True)
        ai=comp.get_anim_instance()
        if ai and state['frames']%2==0:
            hx=comp.get_socket_transform('Head',unreal.RelativeTransformSpace.RTS_WORLD)
            row={'t':round(t,4),'speed':pawn.get_velocity().length(),'flow':ai.get_curve_value('HairFlow'),'blink':ai.get_curve_value('IdleBlink')}
            for n in TIPS:row[n]=list(hx.inverse_transform_location(comp.get_socket_location(n)).to_tuple())
            state['rows'].append(row)
        # Inspect the same upper-body view in all three motion states.
        loc=pawn.get_actor_location()
        camera=loc+unreal.Vector(-230,145,80);target=loc+unreal.Vector(0,0,35)
        editor.set_level_viewport_camera_info(camera,unreal.MathLibrary.find_look_at_rotation(camera,target))
        for label,at in (('Idle',3),('Walk',7),('Run',11),('Run2',11.35),('Run3',11.7)):
            if t>=at and label not in state['images']:
                state['images'].append(label)
                path=os.path.abspath(os.path.join(D,'..','..','Saved','Screenshots','WindowsEditor','HairSoft_'+label+'.png')).replace('\\','/')
                unreal.SystemLibrary.execute_console_command(w,'HighResShot 960x720 filename="'+path+'"')
        if t>=22:finish()
    except Exception:finish(traceback.format_exc())
state['handle']=unreal.register_slate_post_tick_callback(tick)
