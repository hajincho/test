"""Reopen verification: temporary PIE walk/run input, then return to edit mode."""
import unreal, os, json, time, traceback, math
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
state={'started':time.monotonic(),'phase':'open','rows':[],'images':[]}

def finish(error=None):
    try:unreal.unregister_slate_post_tick_callback(state['handle'])
    except Exception:pass
    result={'error':error,'rows':state['rows'],'screenshots':state['images']}
    if state['rows']:
        rows=state['rows']
        result['peak_blink']=max(r['blink'] for r in rows)
        moving=[r for r in rows if r['speed']>80]
        result['peak_moving_blink']=max((r['blink'] for r in moving),default=0)
        result['morph_was_active']=any(r['blink']>.1 and r['morph_active'] for r in rows)
        result['max_speed']=max(r['speed'] for r in rows)
        result['moving_samples']=len(moving)
    with open(os.path.join(D,'character_fix_runtime.json'),'w',encoding='utf-8') as f:json.dump(result,f,indent=1,default=str)
    try:unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    except Exception:pass
    print('CHARACTER_FIX_RUNTIME_DONE',error or 'OK')

def tick(delta):
    try:
        if state['phase']=='open':
            if time.monotonic()-state['started']<3:return
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
            state['phase']='wait';state['wait_started']=time.monotonic();return
        w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if not w:
            if time.monotonic()-state.get('wait_started',state['started'])>60:finish('PIE world was not available')
            return
        pawn=unreal.GameplayStatics.get_player_pawn(w,0)
        if not pawn:
            chars=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Character)
            pawn=next((p for p in chars if any(c.get_name()=='FurinaMesh' for c in p.get_components_by_class(unreal.SkeletalMeshComponent))),None)
        if not pawn:
            if time.monotonic()-state.get('wait_started',state['started'])>60:finish('Player pawn was not available')
            return
        if state['phase']=='wait':
            state['phase']='run';state['elapsed']=0;state['frames']=0
            state['origin']=pawn.get_actor_location();state['original_speed']=pawn.character_movement.max_walk_speed
        dt=unreal.GameplayStatics.get_world_delta_seconds(w)
        state['elapsed']+=dt;state['frames']+=1;t=state['elapsed']
        speed=0 if t<3 or t>=15 else (600 if 7<=t<11 else 120)
        pawn.character_movement.max_walk_speed=600 if speed==600 else 120
        if speed:
            # Stay within a small area while exercising both transition directions.
            dx=pawn.get_actor_location().x-state['origin'].x
            if abs(dx)>380:state['dir']=-1 if dx>0 else 1
            pawn.add_movement_input(unreal.Vector(state.get('dir',1),0,0),1,True)
        comp=next(c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='FurinaMesh')
        ai=comp.get_anim_instance()
        if ai and state['frames']%2==0:
            xf=comp.get_world_transform()
            row={'t':round(t,3),'speed':round(pawn.get_velocity().length(),2),'blink':ai.get_curve_value('IdleBlink'),'walk':ai.get_curve_value('FurinaWalk'),'idle':ai.get_curve_value('FurinaIdle'),
                 'morph_active':'IdleBlink' in [str(n) for n in ai.get_active_curve_names(unreal.AnimCurveType.MORPH_TARGET_CURVE)]}
            for side in ('Left','Right'):
                row[side]=[list(xf.inverse_transform_location(comp.get_socket_location(side+s)).to_tuple()) for s in ('-leg','-knee','-ankle')]
            state['rows'].append(row)
        for phase,at in (('idle',2),('walk',5),('run',9)):
            if t>=at and phase not in state['images']:
                state['images'].append(phase)
                unreal.SystemLibrary.execute_console_command(w,'HighResShot 1')
        if t>=20:finish()
    except Exception:finish(traceback.format_exc())
state['handle']=unreal.register_slate_post_tick_callback(tick)
