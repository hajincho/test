"""Rewrite only the walk pelvis track; preserve gait rotations and all footstep notifies."""
import unreal,os,json,traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={}
try:
    d=json.load(open(os.path.join(D,'ue_walk_tracks.json'),encoding='utf-8'))
    ref=json.load(open(os.path.join(D,'ue_ref.json'),encoding='utf-8'))
    seq=unreal.load_asset('/Game/Furina/Anim/AS_Furina_Walk')
    before=[ev.export_text() for ev in unreal.AnimationLibrary.get_animation_notify_events(seq)]
    i=d['bones'].index('Hips')
    pos=[unreal.Vector(*p) for p in d['hips']];pos.append(pos[0])
    rot=[unreal.Quat(*row[i]) for row in d['rot']];rot.append(rot[0])
    scales=[unreal.Vector(*ref['Hips']['s'])]*len(pos)
    ctrl=seq.get_editor_property('controller')
    ctrl.open_bracket(unreal.Text('Remove non-periodic pelvis drop at the walk loop seam'),True)
    ctrl.set_bone_track_keys('Hips',pos,rot,scales,True)
    ctrl.close_bracket(True)
    after=[ev.export_text() for ev in unreal.AnimationLibrary.get_animation_notify_events(seq)]
    assert before==after
    R['notifies_preserved']=True
    R['length']=seq.get_play_length()
    R['stage_only']=os.path.exists(os.path.join(D,'walk_blink_stage_only'))
    if not R['stage_only']:assert unreal.EditorAssetLibrary.save_loaded_asset(seq,False)
    R['ok']=True
except Exception:R['error']=traceback.format_exc()
with open(os.path.join(D,'walk_loop_applied.json'),'w',encoding='utf-8') as f:json.dump(R,f,indent=1)
