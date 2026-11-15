"""Dumps notify events (name, time) of the bundle Manny run/walk anims and the BS scale settings -> Data/manny_notifies.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
P = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/'
R = {}
try:
    for n in ('Run_Fwd_Anim', 'Walk_Fwd_Anim'):
        a = unreal.load_asset(P + n); ev = []
        for e in unreal.AnimationLibrary.get_animation_notify_events(a):
            ev.append([str(e.get_editor_property('notify_name')) if hasattr(e, 'get_editor_property') else str(e), round(e.get_editor_property('trigger_time_offset'), 3) if False else None])
        R[n] = dict(len=a.get_editor_property('sequence_length'), rate_scale=a.get_editor_property('rate_scale'), events=[str(x) for x in unreal.AnimationLibrary.get_animation_notify_events(a)][:12])
    bs = unreal.load_asset(P + 'WalkRun_BlendSpace')
    R['bs'] = {k: str(bs.get_editor_property(k)) for k in ('axis_to_scale_animation', 'notify_trigger_mode', 'interpolation_time')}
    R['bs_params'] = [str(bs.get_editor_property('blend_parameters')[0])]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\manny_notifies.json', 'w'), indent=1); print('MANNY_NOTIFIES', R.get('error', 'ok')[:300])
