"""Lyra 에디터(`py <파일> [태그]`, run_ue_probe.ps1): 독일 무기 스태틱 메시를 에디터 월드 하늘 위에 줄지어 놓고(저장 안 함) 뷰포트 카메라로 캡처.
 -> Data/de_lineup_<태그>_<a|b>.png, Data/lyra_de_weapons_lineup_<태그>.json"""
import unreal, json, sys, time, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_de_weapons_lineup_%s.json' % TAG
G1 = ['kar98k', 'g43', 'stg44', 'mp40', 'mp38', 'mg42', 'mg34', 'pzb39', 'panzerfaust', 'panzerschreck']
G2 = ['p38', 'p08', 'pp', 'zf4', 'zf39', 'zf41', 'panzerschreck_rocket', 'mortar_shell', 'ammo_7_92x94', 'mauser_clip', 'grw34']
R = {'tag': TAG}; S = {'st': 'open', 't': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str)
UES = lambda: unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); EAS = lambda: unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def place(keys, z0, spacing, scale=1.0):
    acts = []
    for i, k in enumerate(keys):
        sm = unreal.load_asset('/Game/Furina/Weapons/Germany/%s/SM_DE_%s' % (k, k))
        a = EAS().spawn_actor_from_object(sm, unreal.Vector(0, 0, z0 - i * spacing), unreal.Rotator(0, 0, 0))   # 총구(+Y) = 화면 왼쪽(카메라 +X 에서 -X 를 봄)
        a.set_actor_scale3d(unreal.Vector(scale, scale, scale)); acts.append(a)
    return acts
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'spawn'; S['t'] = now + 3; return
        if st == 'spawn' and now >= S['t']:
            S['a1'] = place(G1, 20000, 40); S['st'] = 'cam1'; S['t'] = now + 25; return
        if st == 'cam1':
            UES().set_level_viewport_camera_info(unreal.Vector(340, 0, 20000 - 180), unreal.Rotator(roll=0, pitch=0, yaw=180))
            if now < S['t']: return
            unreal.SystemLibrary.execute_console_command(None, 'HighResShot 2 filename="%s/de_lineup_%s_a.png"' % (D, TAG)); S['st'] = 'swap'; S['t'] = now + 4; return
        if st == 'swap' and now >= S['t']:
            for a in S['a1']: a.destroy_actor()
            S['a2'] = place(G2, 30000, 14); S['st'] = 'cam2'; S['t'] = now + 20; return
        if st == 'cam2':
            UES().set_level_viewport_camera_info(unreal.Vector(135, 0, 30000 - 70), unreal.Rotator(roll=0, pitch=0, yaw=180))
            if now < S['t']: return
            unreal.SystemLibrary.execute_console_command(None, 'HighResShot 2 filename="%s/de_lineup_%s_b.png"' % (D, TAG)); S['st'] = 'end'; S['t'] = now + 5; return
        if st == 'end' and now >= S['t']:
            for a in S['a2']: a.destroy_actor()
            R['done'] = True; save(); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); R['done'] = True; save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_DE_LINEUP armed', TAG)
