"""Lyra 에디터(`py <파일>`, PIE 중지 상태): AS/AM_Furina_FP_ReloadEmpty 의 길이와 RifleReload 곡선을 점검하고 2.0초(60프레임)에 맞춘다.
 시도: 몽타주 길이 재계산(calculate_sequence_length), RifleReload 곡선을 기존 키 모양대로 2.0초에서 끝나게 다시 씀. -> Data/lyra_empty_reload_len.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; A = '/Game/Furina/FP/Anim/'
R = {}
try:
    AL = unreal.AnimationLibrary; F = unreal.RawCurveTrackTypes.RCT_FLOAT; E = unreal.EditorAssetLibrary
    for nm in ('AS_Furina_FP_Reload', 'AM_Furina_FP_Reload', 'AS_Furina_FP_ReloadEmpty', 'AM_Furina_FP_ReloadEmpty'):
        a = unreal.load_asset(A + nm); row = {'len': a.get_play_length()}
        for cn in [str(x) for x in AL.get_animation_curve_names(a, F)]:
            if cn.lower() == 'riflereload':
                try: row['RifleReload_keys'] = [str(k) for k in AL.get_float_keys(a, cn)][:3] if hasattr(AL, 'get_float_keys') else 'no get_float_keys'
                except Exception as e: row['key_err'] = str(e)[:80]
                try:
                    t, v = AL.get_float_keys(a, cn); row['RifleReload'] = [[round(x, 3), round(y, 3)] for x, y in zip(t, v)]
                except Exception as e: row['key_err2'] = str(e)[:80]
                row['curve_name'] = cn
        R[nm] = row
    amo = unreal.load_asset(A + 'AM_Furina_FP_ReloadEmpty'); asq = unreal.load_asset(A + 'AS_Furina_FP_ReloadEmpty')
    try: amo.set_editor_property('sequence_length', 2.0); R['seq_len_set'] = True
    except Exception as e: R['seq_len_set'] = 'err ' + str(e)[:80]
    try: R['sections'] = [[str(amo.get_section_name(i))] for i in range(amo.get_num_sections())]
    except Exception as e: R['sec_err'] = str(e)[:80]
    R['am_len_after_calc'] = amo.get_play_length()
    R['am_props'] = [n for n in dir(amo) if any(k in n.lower() for k in ('length', 'section', 'blend', 'sequence'))][:40]
    ASK = 'riflereload'
    for a in (asq, amo):
        nm = next((str(x) for x in AL.get_animation_curve_names(a, F) if str(x).lower() == ASK), None)
        if nm:
            AL.remove_curve(a, nm, False); AL.add_curve(a, nm, F, False); AL.add_float_curve_keys(a, nm, [0.0, 0.0333, 1.9, 2.0], [0.0, 1.0, 1.0, 0.0])
    R['saved'] = [bool(E.save_loaded_asset(asq, False)), bool(E.save_loaded_asset(amo, False))]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\lyra_empty_reload_len.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_EMPTY_RELOAD_LEN', R.get('error', 'ok')[-300:])
