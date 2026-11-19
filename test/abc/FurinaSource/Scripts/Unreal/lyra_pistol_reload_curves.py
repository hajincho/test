"""Lyra 에디터(`py <파일>`, PIE 중지 상태): Furina_Pistol_Reload(권총 재장전 시퀀스, 2.0초)에 1인칭 왼손 경로 곡선 PRX/PRY/PRZ 를 쓴다.
 값 = Armpist.fbx FPS_Pistol_Reload_easy 의 왼손(Hand_L, 프레임 무게중심 기준, 소총 컴포넌트 축 X왼쪽·Y앞·Z위)의 0프레임 대비 변화량 cm (Data/pistol_reload_hand.json,
 Scripts/Blender/extract_pistol_reload_hand.py).  시간은 FBX 1.317초 -> 시퀀스 2.0초로 늘린다.   백업: /Game/Furina/Backups/Furina_Pistol_Reload_pre_fp
 곡선은 TP 에서는 쓰이지 않는다(권총 3인칭은 CR Alpha 0).   -> Data/lyra_pistol_reload_curves.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
R = {}
try:
    src = json.load(open(D + r'\pistol_reload_hand.json'))['actions']['FPS_Pistol_Reload_easy']; rows = src['rows']; base = rows[0]['hl']; SEC = 2.0; K = SEC / src['seconds']
    E = unreal.EditorAssetLibrary; AL = unreal.AnimationLibrary; F = unreal.RawCurveTrackTypes.RCT_FLOAT
    P = '/Game/Furina/P220/Anim/Furina_Pistol_Reload'; B = '/Game/Furina/Backups/Furina_Pistol_Reload_pre_fp'
    if not E.does_asset_exist(B): R['backup'] = bool(E.duplicate_asset(P, B))
    a = unreal.load_asset(P); R['len'] = a.get_play_length()
    ts = [round(r['t'] * K, 4) for r in rows]
    ts = [min(t, a.get_play_length() - 0.001) for t in ts]
    have = {str(x).lower(): str(x) for x in AL.get_animation_curve_names(a, F)}
    for i, cn in enumerate(('PRX', 'PRY', 'PRZ')):
        if cn.lower() in have: AL.remove_curve(a, have[cn.lower()], False)
        vs = [float(r['hl'][i] - base[i]) for r in rows]
        AL.add_curve(a, cn, F, False); AL.add_float_curve_keys(a, cn, ts, vs)
    R['curves'] = [str(x) for x in AL.get_animation_curve_names(a, F)]; R['n_keys'] = len(ts); R['t_last'] = ts[-1]
    R['saved'] = bool(E.save_loaded_asset(a, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\lyra_pistol_reload_curves.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PISTOL_RELOAD_CURVES', R.get('error', 'ok')[-300:])
import gc; gc.collect()
