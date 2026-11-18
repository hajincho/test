"""Lyra 에디터(`py <파일>`): 전술 재장전(AS/AM_Furina_FP_Reload) 곡선을 Data/tactical_reload_curves.json 으로 바꾼다(0~2.4초는 기존 그대로, 2.4~3.133초에 장전손잡이 당기기). 먼저 원본 곡선을 /Game/Furina/Backups/ 에 복제.
 재생 속도 0.85 와 타이머 시간은 BP 쪽(lyra_tactical_bp.py).   -> Data/lyra_tactical_reload_apply.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; A = '/Game/Furina/FP/Anim/'
R = {}
def run():
    c = json.load(open(D + r'\tactical_reload_curves.json'))
    AL = unreal.AnimationLibrary; F = unreal.RawCurveTrackTypes.RCT_FLOAT; E = unreal.EditorAssetLibrary
    for nm in ('AS_Furina_FP_Reload', 'AM_Furina_FP_Reload'):
        if not E.does_asset_exist('/Game/Furina/Backups/%s_pre_tactical' % nm): R['bk_' + nm] = bool(E.duplicate_asset(A + nm, '/Game/Furina/Backups/%s_pre_tactical' % nm))
    ms_t = [k[0] for k in c['magstate']]; ms_v = [float(k[1]) for k in c['magstate']]
    spec = (('ReloadLX', c['times'], c['LX']), ('ReloadLY', c['times'], c['LY']), ('ReloadLZ', c['times'], c['LZ']), ('MagState', ms_t, ms_v),
            ('BoltBack', [k[0] for k in c['boltback']], [k[1] for k in c['boltback']]), ('HandleBack', [k[0] for k in c['handleback']], [k[1] for k in c['handleback']]),
            ('HandleFp', [k[0] for k in c['handlefp']], [k[1] for k in c['handlefp']]), ('RifleReload', [k[0] for k in c['riflereload']], [k[1] for k in c['riflereload']]))
    for nm in ('AS_Furina_FP_Reload', 'AM_Furina_FP_Reload'):
        a = unreal.load_asset(A + nm); low = {str(h).lower(): str(h) for h in AL.get_animation_curve_names(a, F)}
        for cn, ts, vs in spec:
            use = low.get(cn.lower(), cn)
            if cn.lower() in low: AL.remove_curve(a, low[cn.lower()], False)
            AL.add_curve(a, use, F, False); AL.add_float_curve_keys(a, use, ts, vs)
        R[nm] = {'curves': [str(x) for x in AL.get_animation_curve_names(a, F)], 'len': a.get_play_length(), 'saved': bool(E.save_loaded_asset(a, False))}
        del a
    R['rate'] = c['rate']; R['real_seconds'] = c['real_seconds']
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\lyra_tactical_reload_apply.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_TACTICAL_APPLY', R.get('error', 'ok')[-200:])
import gc; gc.collect()
