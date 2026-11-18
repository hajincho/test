"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 긴급(빈 탄창) 재장전 애니메이션 자산을 만든다.
 - AS_Furina_FP_Reload / AM_Furina_FP_Reload 를 AS_Furina_FP_ReloadEmpty / AM_Furina_FP_ReloadEmpty 로 복제 (뼈 애니메이션은 템플릿 재장전을 그대로 쓰고 CR 이 손을 곡선으로 덮어쓴다)
 - Data/empty_reload_curves.json (Scripts/Tools/build_empty_reload_curves.py) 의 곡선으로 ReloadLX/LY/LZ, MagState, BoltBack 을 두 자산에 쓴다
 - 몽타주 구간을 2.0초(60프레임, 30fps)로 자른다
   -> Data/lyra_empty_reload_apply.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; A = '/Game/Furina/FP/Anim/'
R = {}
try:
    c = json.load(open(D + r'\empty_reload_curves.json'))
    AL = unreal.AnimationLibrary; F = unreal.RawCurveTrackTypes.RCT_FLOAT; E = unreal.EditorAssetLibrary
    for src, dst in (('AS_Furina_FP_Reload', 'AS_Furina_FP_ReloadEmpty'), ('AM_Furina_FP_Reload', 'AM_Furina_FP_ReloadEmpty')):
        if not E.does_asset_exist(A + dst): R['dup_' + dst] = bool(E.duplicate_asset(A + src, A + dst))
    asq = unreal.load_asset(A + 'AS_Furina_FP_ReloadEmpty'); amo = unreal.load_asset(A + 'AM_Furina_FP_ReloadEmpty')
    R['as_len_before'] = asq.get_play_length(); R['am_len_before'] = amo.get_play_length()
    ms_t = [k[0] for k in c['magstate']]; ms_v = [float(k[1]) for k in c['magstate']]; bt = [k[0] for k in c['boltback']]; bv = [k[1] for k in c['boltback']]; ht = [k[0] for k in c['handleback']]; hv = [k[1] for k in c['handleback']]; ft = [k[0] for k in c['handlefp']]; fv = [k[1] for k in c['handlefp']]
    for a in (asq, amo):
        have = [str(x) for x in AL.get_animation_curve_names(a, F)]; low = {h.lower(): h for h in have}
        for cn, ts, vs in (('ReloadLX', c['times'], c['LX']), ('ReloadLY', c['times'], c['LY']), ('ReloadLZ', c['times'], c['LZ']), ('MagState', ms_t, ms_v), ('BoltBack', bt, bv), ('HandleBack', ht, hv), ('HandleFp', ft, fv)):
            if cn.lower() in low: AL.remove_curve(a, low[cn.lower()], False)
            AL.add_curve(a, cn, F, False); AL.add_float_curve_keys(a, cn, ts, vs)
        R[a.get_name()] = dict(curves=[str(x) for x in AL.get_animation_curve_names(a, F)])
    # 몽타주: 슬롯 트랙의 구간을 새 AS 로 바꾸고 2.0초로 자른다
    tracks = amo.get_editor_property('slot_anim_tracks'); R['n_tracks'] = len(tracks)
    seg_info = []
    for tr in tracks:
        t = tr.get_editor_property('anim_track'); segs = t.get_editor_property('anim_segments')
        for s in segs:
            seg_info.append({'ref': str(s.get_editor_property('anim_reference')), 'start': s.get_editor_property('anim_start_time'), 'end': s.get_editor_property('anim_end_time'), 'rate': s.get_editor_property('anim_play_rate')})
            s.set_editor_property('anim_reference', asq); s.set_editor_property('anim_end_time', float(c['seconds'])); R['seg_after'] = [s.get_editor_property('anim_start_time'), s.get_editor_property('anim_end_time')]
        t.set_editor_property('anim_segments', segs); tr.set_editor_property('anim_track', t)
    amo.set_editor_property('slot_anim_tracks', tracks)
    R['segments_before'] = seg_info
    for attr in ('blend_in', 'blend_out'):
        try: R[attr] = str(amo.get_editor_property(attr))
        except Exception as e: R[attr + '_err'] = str(e)[:60]
    R['am_len_after'] = amo.get_play_length(); R['as_len_after'] = asq.get_play_length()
    R['saved'] = [bool(E.save_loaded_asset(asq, False)), bool(E.save_loaded_asset(amo, False))]
    R['events'] = c['events']
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\lyra_empty_reload_apply.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_EMPTY_RELOAD_APPLY', R.get('error', 'ok')[-300:])
