import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {'log': []}
def log(*a): res['log'].append(' '.join(str(x) for x in a))
eal = unreal.EditorAssetLibrary
try:
    d = json.load(open(os.path.join(S, 'ue_idle_tracks.json'), encoding='utf-8'))
    ref = json.load(open(os.path.join(S, 'ue_ref.json'), encoding='utf-8'))
    sk = unreal.load_asset('/Game/Furina/SK_Furina'); skel = sk.get_editor_property('skeleton')
    path = '/Game/Furina/Anim/AS_Furina_Idle'
    # never delete an asset the AnimBP has loaded: rewrite its tracks in place
    if eal.does_asset_exist(path):
        seq = unreal.load_asset(path)
    else:
        f = unreal.AnimSequenceFactory(); f.set_editor_property('target_skeleton', skel); f.set_editor_property('preview_skeletal_mesh', sk)
        seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset('AS_Furina_Idle', '/Game/Furina/Anim', unreal.AnimSequence, f)
    ctrl = seq.get_editor_property('controller')
    N = d['frames']
    ctrl.open_bracket(unreal.Text('Furina idle'), True)
    try: ctrl.remove_all_bone_tracks(True)
    except Exception as e: log('remove tracks', repr(e))
    ctrl.set_frame_rate(unreal.FrameRate(30, 1), True)
    ctrl.set_number_of_frames(unreal.FrameNumber(N - 1), True)
    for i, b in enumerate(d['bones']):
        r = ref[b]
        ctrl.add_bone_curve(b, True)
        if b == 'Hips':
            pos = [unreal.Vector(*h) for h in d['hips']]
        else:
            pos = [unreal.Vector(*r['p'])] * N
        rots = [unreal.Quat(*d['rot'][k][i]) for k in range(N)]
        scl = [unreal.Vector(*r['s'])] * N
        ctrl.set_bone_track_keys(b, pos, rots, scl, True)
    ctrl.close_bracket(True)
    log('length', seq.get_play_length())
    # Unity blink morph (IdleBlink) as a curve
    try:
        if 'IdleBlink' in [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(seq, unreal.RawCurveTrackTypes.RCT_FLOAT)]:
            unreal.AnimationLibrary.remove_curve(seq, 'IdleBlink', False)
        unreal.AnimationLibrary.add_curve(seq, 'IdleBlink', unreal.RawCurveTrackTypes.RCT_FLOAT, False)
        unreal.AnimationLibrary.add_float_curve_keys(seq, 'IdleBlink', [k / 30.0 for k in range(N)], [v / 100.0 for v in d['blink']])
        log('blink curve ok')
    except Exception as e: log('blink', repr(e))
    try:
        if hasattr(skel, 'set_curve_meta_data_morph_target'): log('morph meta', skel.set_curve_meta_data_morph_target('IdleBlink', True))
        else: log('skel curve methods', [m for m in dir(skel) if 'curve' in m.lower()])
    except Exception as e: log('meta', repr(e))
    eal.save_asset(path)
    # Mark Manny's idle so Furina knows when Manny is idling
    idle = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/Idle_Anim')
    names = [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(idle, unreal.RawCurveTrackTypes.RCT_FLOAT)]
    if 'FurinaIdle' not in names:
        unreal.AnimationLibrary.add_curve(idle, 'FurinaIdle', unreal.RawCurveTrackTypes.RCT_FLOAT, False)
        L = idle.get_play_length()
        unreal.AnimationLibrary.add_float_curve_keys(idle, 'FurinaIdle', [0.0, L], [1.0, 1.0])
    eal.save_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/Idle_Anim')
    log('manny idle curves', [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(idle, unreal.RawCurveTrackTypes.RCT_FLOAT)])
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_make_idle.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('MAKE_IDLE_DONE')
