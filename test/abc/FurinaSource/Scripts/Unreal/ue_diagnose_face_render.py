"""Read-only isolated editor render: open, forced blink, then AnimBP blink."""
import unreal,os,json,time,traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
S=os.path.abspath(os.path.join(D,'..','..','Saved','Screenshots','WindowsEditor'))
os.makedirs(S,exist_ok=True)
try:
    perf=unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings')
    unreal.get_default_object(perf).set_editor_property('throttle_cpu_when_not_foreground',False)
except Exception:pass
R={'frames':[],'screenshots':[]}
state={'phase':'setup','n':0,'start':time.monotonic()}
def finish(error=None):
    if error:R['error']=error
    try:unreal.unregister_slate_post_tick_callback(state['h'])
    except Exception:pass
    with open(os.path.join(D,'face_render_diagnosis.json'),'w',encoding='utf-8') as f:json.dump(R,f,indent=1,default=str)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
def prop(o,n):
    try:return str(o.get_editor_property(n))
    except Exception as e:return str(e)
def shot(label):
    path=os.path.join(S,'BlinkDiag_'+label+'.png')
    state['capture'].capture_scene()
    unreal.RenderingLibrary.export_render_target(state['world'],state['rt'],S,'BlinkDiag_'+label+'.png')
    R['screenshots'].append(path)
def tick(dt):
    try:
        if time.monotonic()-state['start']>90:finish('render timeout');return
        state['n']+=1
        if state['phase']=='setup':
            if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
                unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play();return
            unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
            eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            a=eas.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(0,0,0),unreal.Rotator())
            comp=a.skeletal_mesh_component
            sk=unreal.load_asset('/Game/Furina/SK_Furina')
            comp.set_skinned_asset_and_update(sk)
            R['render_static_before']=prop(comp,'render_static')
            comp.set_render_static(False)
            comp.set_update_animation_in_editor(True)
            comp.play_animation(unreal.load_asset('/Game/Furina/Anim/AS_Furina_Idle'),True)
            comp.set_play_rate(0)
            comp.set_position(0,False)
            comp.set_editor_property('visibility_based_anim_tick_option',unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
            state['comp']=comp
            R['mesh']={n:prop(sk,n) for n in ('post_process_anim_blueprint','nanite_settings','lod_info')}
            R['component']={n:prop(comp,n) for n in ('disable_morph_target','morph_target_curves','force_disable_nanite')}
            R['mesh_api']=[n for n in dir(sk) if any(k in n.lower() for k in ('morph','lod','nanite'))]
            R['mesh_editor_api']=[n for n in dir(unreal.SkeletalMeshEditorSubsystem) if any(k in n.lower() for k in ('morph','lod','nanite'))]
            R['cvars']={n:unreal.SystemLibrary.get_console_variable_int_value(n) for n in ('r.EnableMorphTargets','r.MorphTarget.Mode','r.SkinCache.Mode')}
            light=eas.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,60,200),unreal.Rotator(pitch=-15,yaw=-90,roll=0))
            light.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(1)
            fill=eas.spawn_actor_from_class(unreal.PointLight,unreal.Vector(0,45,145),unreal.Rotator())
            fill.get_component_by_class(unreal.PointLightComponent).set_intensity(.2)
            unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(0,65,141),unreal.Rotator(pitch=0,yaw=-90,roll=0))
            comp.clear_morph_targets()
            a.set_actor_label('FaceProbe_TEMP')
            camera=eas.spawn_actor_from_class(unreal.SceneCapture2D,unreal.Vector(0,65,141),unreal.Rotator(pitch=0,yaw=-90,roll=0))
            camera.set_actor_label('FaceCapture_TEMP')
            capture=camera.get_component_by_class(unreal.SceneCaptureComponent2D)
            rt=unreal.RenderingLibrary.create_render_target2d(editor_world if 'editor_world' in globals() else unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),960,720,unreal.TextureRenderTargetFormat.RTF_RGBA8)
            capture.set_editor_property('texture_target',rt)
            capture.set_editor_property('capture_every_frame',False)
            capture.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
            capture.set_editor_property('fov_angle',60)
            pp=capture.get_editor_property('post_process_settings')
            for name,value in (('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',0),('auto_exposure_max_brightness',0),('override_bloom_intensity',True),('bloom_intensity',0)):
                pp.set_editor_property(name,value)
            capture.set_editor_property('post_process_settings',pp)
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
            state.update(phase='wait_game',n=0);return
        if state['phase']=='wait_game':
            world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            if not world:return
            actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.SkeletalMeshActor)
            actor=next((a for a in actors if a.get_actor_label()=='FaceProbe_TEMP'),None)
            if not actor:return
            state['comp']=actor.skeletal_mesh_component
            state['comp'].set_render_static(False)
            state['comp'].play_animation(unreal.load_asset('/Game/Furina/Anim/AS_Furina_Idle'),True)
            state['comp'].set_play_rate(1)
            state['world']=world
            camera=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.SceneCapture2D) if a.get_actor_label()=='FaceCapture_TEMP')
            capture=camera.get_component_by_class(unreal.SceneCaptureComponent2D)
            rt=capture.get_editor_property('texture_target')
            pp=capture.get_editor_property('post_process_settings')
            for name,value in (('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',0),('auto_exposure_max_brightness',0),('override_bloom_intensity',True),('bloom_intensity',0)):
                pp.set_editor_property(name,value)
            capture.set_editor_property('post_process_settings',pp)
            capture.set_editor_property('post_process_blend_weight',1)
            state['capture']=capture;state['rt']=rt
            state.update(phase='open',n=0);return
        comp=state['comp']
        if state['phase']=='open' and state['n']>=60:
            shot('Open');state.update(phase='force',n=0);comp.set_morph_target('IdleBlink',1,False);return
        if state['phase']=='force' and state['n']>=20:
            R['forced_morph']=comp.get_morph_target('IdleBlink')
            R['forced_component']=comp.get_path_name()
            R['forced_hips']=str(comp.get_socket_location('Hips'))
            R['forced_instance']=str(comp.get_anim_instance())
            R['material_after_render']={n:prop(unreal.load_asset('/Game/Furina/Materials/M_Furina_Opaque'),n) for n in ('used_with_morph_targets','used_with_skeletal_mesh')}
            shot('ForcedClosed');state.update(phase='force_cpu',n=0)
            unreal.SystemLibrary.execute_console_command(state['world'],'r.MorphTarget.Mode 0')
            unreal.SystemLibrary.execute_console_command(state['world'],'r.SkinCache.Mode 0')
            return
        if state['phase']=='force_cpu' and state['n']>=30:
            shot('ForcedClosedCPU');state.update(phase='auto',n=0)
            unreal.SystemLibrary.execute_console_command(state['world'],'r.MorphTarget.Mode 1')
            unreal.SystemLibrary.execute_console_command(state['world'],'r.SkinCache.Mode 1')
            comp.clear_morph_targets()
            comp.set_anim_instance_class(unreal.load_object(None,'/Game/Furina/ABP_Furina.ABP_Furina_C'))
            return
        if state['phase']=='auto':
            ai=comp.get_anim_instance()
            if ai:
                v=ai.get_curve_value('IdleBlink')
                R['frames'].append({'n':state['n'],'curve':v,'override':comp.get_morph_target('IdleBlink'),'active':[str(n) for n in ai.get_active_curve_names(unreal.AnimCurveType.MORPH_TARGET_CURVE)]})
                if v>.98:
                    R['auto_render_settings']={n:unreal.SystemLibrary.get_console_variable_int_value(n) for n in ('r.MorphTarget.Mode','r.SkinCache.Mode')}
                    shot('AutoClosed');state.update(phase='finish',n=0);return
            if state['n']>=600:finish('AnimBP blink never closed');return
        if state['phase']=='finish' and state['n']>=10:finish()
    except Exception:finish(traceback.format_exc())
state['h']=unreal.register_slate_post_tick_callback(tick)
