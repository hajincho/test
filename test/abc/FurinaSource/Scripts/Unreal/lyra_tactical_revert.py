"""Lyra 에디터(`py <파일>`): 전술(잔탄이 남은) 재장전을 옛 3.0초 방식(장전손잡이 안 당김)으로 되돌린다. 긴급(잔탄 0) 재장전은 그대로.
 AS/AM_Furina_FP_Reload 곡선을 reload_curves_new.json(원래 값)과 RifleReload [0,0.35:1,2.6:1,3.0:0] 으로 되돌리고, 손잡이용 곡선 BoltBack/HandleBack/HandleFp 는 지운다.
 (사본은 /Game/Furina/Backups/*_pre_tactical, 장전손잡이를 당기는 전술 곡선은 Data/tactical_reload_curves.json 에 남아 있다.)  재생 속도와 타이머는 lyra_tactical_bp.py revert.   -> Data/lyra_tactical_revert.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; A = '/Game/Furina/FP/Anim/'
R = {}
def run():
    c = json.load(open(D + r'\reload_curves_new.json'))
    AL = unreal.AnimationLibrary; F = unreal.RawCurveTrackTypes.RCT_FLOAT; E = unreal.EditorAssetLibrary
    ms_t = [k[0] for k in c['magstate']]; ms_v = [float(k[1]) for k in c['magstate']]
    spec = (('ReloadLX', c['times'], c['LX']), ('ReloadLY', c['times'], c['LY']), ('ReloadLZ', c['times'], c['LZ']), ('MagState', ms_t, ms_v), ('RifleReload', [0.0, 0.35, 2.6, 3.0], [0.0, 1.0, 1.0, 0.0]))
    for nm in ('AS_Furina_FP_Reload', 'AM_Furina_FP_Reload'):
        a = unreal.load_asset(A + nm); low = {str(h).lower(): str(h) for h in AL.get_animation_curve_names(a, F)}
        for cn, ts, vs in spec:
            use = low.get(cn.lower(), cn)
            if cn.lower() in low: AL.remove_curve(a, low[cn.lower()], False)
            AL.add_curve(a, use, F, False); AL.add_float_curve_keys(a, use, ts, vs)
        for cn in ('BoltBack', 'HandleBack', 'HandleFp'):
            if cn.lower() in low: AL.remove_curve(a, low[cn.lower()], False)
        R[nm] = {'curves': [str(x) for x in AL.get_animation_curve_names(a, F)], 'saved': bool(E.save_loaded_asset(a, False))}
        del a
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\lyra_tactical_revert.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_TACTICAL_REVERT', R.get('error', 'ok')[-200:])
import gc; gc.collect()
