import unreal,os,json,math,traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={}
try:
    seq=unreal.load_asset('/Game/Furina/Anim/AS_Furina_Walk')
    N=40;L=seq.get_play_length()
    pts=[unreal.AnimationLibrary.get_bone_pose_for_time(seq,'Hips',k*L/N,False).translation for k in range(N)]
    v=[pts[(i+1)%N].z-pts[i].z for i in range(N)]
    R['seam_step_cm']=abs(v[-1]);R['max_step_cm']=max(map(abs,v))
    R['max_acceleration_cm_per_frame2']=max(abs(v[i]-v[(i-1)%N]) for i in range(N))
    R['footstep_count']=len(unreal.AnimationLibrary.get_animation_notify_events(seq))
    R['walk_ok']=R['max_step_cm']<.7 and R['max_acceleration_cm_per_frame2']<.25 and R['footstep_count']==2
    material=unreal.load_asset('/Game/Furina/Materials/M_Furina_Opaque')
    R['shader_morph_enabled']=material.get_editor_property('used_with_morph_targets')
    R['shader_skin_enabled']=material.get_editor_property('used_with_skeletal_mesh')
    bp=unreal.load_asset('/Game/Furina/ABP_Furina')
    ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
    event=ed.find_event_node('BlueprintPostEvaluateAnimation')
    R['post_evaluate_connected']=bool(event and event.find_then_pin().list_connected_pins())
    R['blueprint_status']=str(bp.get_editor_property('status'))
    R['ok']=R['walk_ok'] and R['shader_morph_enabled'] and R['shader_skin_enabled'] and R['post_evaluate_connected'] and bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
except Exception:R['error']=traceback.format_exc()
with open(os.path.join(D,'walk_blink_asset_validation.json'),'w',encoding='utf-8') as f:json.dump(R,f,indent=1,default=str)
