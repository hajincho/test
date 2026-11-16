"""Editor(Lyra): Data/reload_curves_new.json 의 곡선을 AS_Furina_FP_Reload / AM_Furina_FP_Reload 에 적용 (ReloadLX/LY/LZ + MagState). 총 3.0초 재장전.
-> FurinaSource/Data/lyra_reload_apply.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
R = {}
try:
    c = json.load(open(D + r'\reload_curves_new.json'))
    AL = unreal.AnimationLibrary; F = unreal.RawCurveTrackTypes.RCT_FLOAT
    ms_t = [k[0] for k in c['magstate']]; ms_v = [float(k[1]) for k in c['magstate']]
    for name in ('AS_Furina_FP_Reload', 'AM_Furina_FP_Reload'):
        a = unreal.load_asset('/Game/Furina/FP/Anim/' + name)
        have = [str(x) for x in AL.get_animation_curve_names(a, F)]
        low = {h.lower(): h for h in have}      # AS 의 곡선 이름은 소문자('reloadlx')라 대소문자 무시로 찾아 지운다
        for cn, vals in (('ReloadLX', c['LX']), ('ReloadLY', c['LY']), ('ReloadLZ', c['LZ'])):
            if cn.lower() in low: AL.remove_curve(a, low[cn.lower()], False)
            AL.add_curve(a, cn, F, False); AL.add_float_curve_keys(a, cn, c['times'], vals)
        if 'magstate' in low: AL.remove_curve(a, low['magstate'], False)
        AL.add_curve(a, 'MagState', F, False); AL.add_float_curve_keys(a, 'MagState', ms_t, ms_v)
        R[name] = dict(length=a.get_play_length(), curves=[str(x) for x in AL.get_animation_curve_names(a, F)], saved=unreal.EditorAssetLibrary.save_loaded_asset(a, False))
        del a
    R['events'] = c['events']; R['max_abs'] = c['max_abs']
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\lyra_reload_apply.json', 'w'), indent=1, default=str); print('LYRA_RELOAD_APPLY', R.get('error', 'ok')[-300:])
