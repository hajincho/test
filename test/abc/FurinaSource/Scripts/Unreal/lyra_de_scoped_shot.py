"""Lyra 에디터(`py <파일> [태그]`, run_ue_probe.ps1): 조준경 합본 3종을 에디터 월드 하늘 위에 놓고(저장 안 함) 오른쪽-뒤 3/4 시점으로 확대 캡처(엔진 재질 그대로).
 -> Data/de_scoped_<태그>_<키>.png, Data/lyra_de_scoped_shot_<태그>.json"""
import unreal, json, sys, time, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_de_scoped_shot_%s.json' % TAG
KEYS = ['g43', 'g43_zf4'] if TAG.startswith('chk') else ['kar98k_zf39', 'kar98k_zf41', 'g43_zf4']; R = {'tag': TAG}; S = {'st': 'open', 't': 0, 'i': 0}
UES = lambda: unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); EAS = lambda: unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str)
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'spawn'; S['t'] = now + 3; return
        if st == 'spawn' and now >= S['t']:
            k = KEYS[S['i']]; sm = unreal.load_asset('/Game/Furina/Weapons/Germany/%s/SM_DE_%s' % (k, k))
            S['a'] = EAS().spawn_actor_from_object(sm, unreal.Vector(0, 0, 20000), unreal.Rotator(0, 0, 0)); S['st'] = 'cam'; S['t'] = now + 12; return
        if st == 'cam':
            # 조준경 부근(원본 y -5~20 -> UE y 5~-20, 중심 -6), 총의 오른쪽(-X) 뒤에서 위로 비스듬히
            tgt = unreal.Vector(0, -4, 20000 + 10); cam = unreal.Vector(-48, -38, 20000 + 30)
            UES().set_level_viewport_camera_info(cam, unreal.MathLibrary.find_look_at_rotation(cam, tgt))
            if now < S['t']: return
            unreal.SystemLibrary.execute_console_command(None, 'HighResShot 1600x900 filename="%s/de_scoped_%s_%s.png"' % (D, TAG, KEYS[S['i']])); S['st'] = 'next'; S['t'] = now + 4; return
        if st == 'next' and now >= S['t']:
            S['a'].destroy_actor(); S['i'] += 1
            if S['i'] < len(KEYS): S['st'] = 'spawn'; S['t'] = now + 0.5; return
            R['done'] = True; save(); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); R['done'] = True; save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_DE_SCOPED_SHOT armed', TAG)
