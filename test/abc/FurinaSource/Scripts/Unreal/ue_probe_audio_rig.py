import unreal, os, json, traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={}
def p(o,n):
    try:return str(o.get_editor_property(n))
    except Exception as e:return str(e)
try:
    for path in ('/Game/3DPlatformerGameBundle/Audio/Cues/Footsteps2_Cue','/Game/3DPlatformerGameBundle/Audio/Cues/Footsteps_Cue'):
        a=unreal.load_asset(path)
        R[path]={'properties':{k:p(a,k) for k in ('first_node','all_nodes','duration','volume_multiplier','pitch_multiplier')},'dependencies':list(unreal.EditorAssetLibrary.find_package_referencers_for_asset(path,False))}
        R[path]['nodes']=[]
        try:
            for n in a.get_editor_property('all_nodes'):
                R[path]['nodes'].append({'name':n.get_name(),'class':n.get_class().get_name(), 'props':{k:p(n,k) for k in ('child_nodes','sound_wave','looping','input','volume_min','volume_max','pitch_min','pitch_max')}})
        except Exception:pass
    rig=unreal.load_asset('/Game/Furina/CR_FurinaSecondary').create_control_rig()
    h=rig.get_hierarchy()
    R['hierarchy_methods']={n:getattr(h,n).__doc__ for n in dir(h) if any(k in n for k in ('curve','transform','reset'))}
    R['anim_api']={n:getattr(unreal.AnimationLibrary,n).__doc__ for n in dir(unreal.AnimationLibrary) if any(k in n for k in ('bone_pose','notify_event','curve_meta_data_morph'))}
    R['rig_execute']=rig.execute('Forwards Solve')
    R['rig_h_keys']=len(h.get_all_keys(True))
except Exception:R['error']=traceback.format_exc()
with open(os.path.join(D,'character_audio_rig.json'),'w',encoding='utf-8') as f:json.dump(R,f,ensure_ascii=False,indent=1,default=str)
