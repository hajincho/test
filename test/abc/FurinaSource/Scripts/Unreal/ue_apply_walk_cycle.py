"""Rewrites AS_Furina_Walk from Data/ue_walk_tracks.json (Unity walk frames 92..131: the 40-frame window whose loop seam
matches to 0.0 deg; the old 80..119 window made the right foot jump ~8 cm back while swinging forward at the seam).
Footstep notifies (FurinaWalkSteps) are re-placed at the new forward-most ankle frames; other notifies are untouched."""
import unreal, os, json, traceback
D = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Data'))
R = {}
try:
    d = json.load(open(os.path.join(D, 'ue_walk_tracks.json'), encoding='utf-8'))
    ref = json.load(open(os.path.join(D, 'ue_ref.json'), encoding='utf-8'))
    seq = unreal.load_asset('/Game/Furina/Anim/AS_Furina_Walk')
    N = d['frames']
    ctrl = seq.get_editor_property('controller')
    ctrl.open_bracket(unreal.Text('Walk cycle from seamless Unity window'), True)
    ctrl.remove_all_bone_tracks(True)
    ctrl.set_frame_rate(unreal.FrameRate(30, 1), True)
    ctrl.set_number_of_frames(unreal.FrameNumber(N), True)
    for i, b in enumerate(d['bones']):
        r = ref[b]
        ctrl.add_bone_curve(b, True)
        pos = [unreal.Vector(*h) for h in d['hips']] if b == 'Hips' else [unreal.Vector(*r['p'])] * N
        rots = [unreal.Quat(*d['rot'][k][i]) for k in range(N)]
        pos = pos + [pos[0]]; rots = rots + [rots[0]]          # exact cycle: the last key repeats the first
        ctrl.set_bone_track_keys(b, pos, rots, [unreal.Vector(*r['s'])] * len(rots), True)
    ctrl.close_bracket(True)
    # footsteps: forward-most ankle (same convention as ue_apply_character_fixes.py)
    steps = json.load(open(os.path.join(D, 'walk_cycle_steps.json'), encoding='utf-8'))
    track = 'FurinaWalkSteps'
    if track in [str(n) for n in unreal.AnimationLibrary.get_animation_notify_track_names(seq)]:
        unreal.AnimationLibrary.remove_animation_notify_events_by_track(seq, track)
    else:
        unreal.AnimationLibrary.add_animation_notify_track(seq, track, unreal.LinearColor(.25, .6, 1, 1))
    cue = unreal.load_asset('/Game/3DPlatformerGameBundle/Audio/Cues/Footsteps2_Cue')
    R['walk_notifies'] = []
    for bone, frame in steps.items():
        notify = unreal.AnimNotify_PlaySound(outer=seq)
        notify.set_editor_property('sound', cue)
        notify.set_editor_property('volume_multiplier', .28)
        notify.set_editor_property('pitch_multiplier', 1.05)
        notify.set_editor_property('follow', True)
        notify.set_editor_property('attach_name', bone)
        ev = unreal.AnimNotifyEvent()
        ev.set_editor_property('notify', notify)
        ev.set_editor_property('trigger_weight_threshold', .5)
        ev.set_editor_property('notify_name', 'FurinaWalkStep')
        unreal.AnimationLibrary.add_animation_notify_event_from_source(seq, frame / 30.0, ev, track)
        R['walk_notifies'].append({'bone': bone, 'time': frame / 30.0})
    R['length'] = seq.get_play_length()
    R['notify_tracks'] = [str(n) for n in unreal.AnimationLibrary.get_animation_notify_track_names(seq)]
    assert unreal.EditorAssetLibrary.save_loaded_asset(seq, False)
    R['ok'] = True
except Exception:
    R['error'] = traceback.format_exc()
json.dump(R, open(os.path.join(D, 'walk_cycle_applied.json'), 'w', encoding='utf-8'), indent=1)
print('WALK_CYCLE_APPLIED', R.get('ok'))
