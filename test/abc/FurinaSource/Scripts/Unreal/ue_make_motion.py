"""Writes AS_Furina_Idle and AS_Furina_Walk from Data/ue_<mode>_tracks.json (rewrites tracks in place, never deletes)."""
import unreal, json, traceback, os
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {'log': []}
def log(*a): res['log'].append(' '.join(str(x) for x in a))
eal = unreal.EditorAssetLibrary
try:
    ref = json.load(open(os.path.join(D, 'ue_ref.json'), encoding='utf-8'))
    sk = unreal.load_asset('/Game/Furina/SK_Furina'); skel = sk.get_editor_property('skeleton')
    for mode, name in (('idle', 'AS_Furina_Idle'), ('walk', 'AS_Furina_Walk')):
        d = json.load(open(os.path.join(D, 'ue_%s_tracks.json' % mode), encoding='utf-8'))
        path = '/Game/Furina/Anim/' + name
        if eal.does_asset_exist(path):
            seq = unreal.load_asset(path)
        else:
            f = unreal.AnimSequenceFactory(); f.set_editor_property('target_skeleton', skel); f.set_editor_property('preview_skeletal_mesh', sk)
            seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/Furina/Anim', unreal.AnimSequence, f)
        ctrl = seq.get_editor_property('controller')
        N = d['frames']
        ctrl.open_bracket(unreal.Text(name), True)
        try: ctrl.remove_all_bone_tracks(True)
        except Exception as e: log('remove', repr(e))
        ctrl.set_frame_rate(unreal.FrameRate(30, 1), True)
        ctrl.set_number_of_frames(unreal.FrameNumber(N if mode == 'walk' else N - 1), True)
        for i, b in enumerate(d['bones']):
            r = ref[b]
            ctrl.add_bone_curve(b, True)
            pos = [unreal.Vector(*h) for h in d['hips']] if b == 'Hips' else [unreal.Vector(*r['p'])] * N
            rots = [unreal.Quat(*d['rot'][k][i]) for k in range(N)]
            if mode == 'walk':   # exact cycle: repeat the first key at the end so the loop closes
                pos = pos + [pos[0]]; rots = rots + [rots[0]]
            ctrl.set_bone_track_keys(b, pos, rots, [unreal.Vector(*r['s'])] * len(rots), True)
        ctrl.close_bracket(True)
        names = [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(seq, unreal.RawCurveTrackTypes.RCT_FLOAT)]
        if 'IdleBlink' in names:   # blinking is driven by the Control Rig now (Unity timing, idle only)
            unreal.AnimationLibrary.remove_curve(seq, 'IdleBlink', False)
        eal.save_asset(path)
        log(name, 'frames', N, 'length', seq.get_play_length(), 'curves', [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(seq, unreal.RawCurveTrackTypes.RCT_FLOAT)])
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(D, 'ue_make_motion.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('MAKE_MOTION_DONE')
