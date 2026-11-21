"""Lyra 에디터(`py <파일> [태그]`, 화면에 보이게 실행): PIE 시작 후 무기창 상태를 0.2초마다 기록(실제 키/클릭 수동 확인용).
 기록: Data/lyra_weapon_menu_watch_<태그>.json  {log: [[t, 활성, NationIndex, 커서]...]}  - 'stop' 파일(Data/wm_watch_stop)이 생기면 PIE 종료"""
import unreal, json, sys, time, traceback, os
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_weapon_menu_watch_%s.json' % TAG; STOP = D + '/wm_watch_stop'
if os.path.exists(STOP): os.remove(STOP)
R = {'tag': TAG, 'log': []}; S = {'st': 'open', 't': 0, 'last': None, 'lt': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'play'; S['t'] = now + 4; return
        if st == 'play':
            if now >= S['t']: LES().editor_request_begin_play(); S['st'] = 'run'; S['t0'] = now
            return
        if st == 'run':
            if os.path.exists(STOP) or now - S['t0'] > 600:
                R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h']); return
            if now - S['lt'] < 0.2: return
            S['lt'] = now
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
            pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
            if p is None: return
            m = p.get_editor_property('FurinaWeaponMenu')
            cur = (bool(m and m.is_activated()), m.get_editor_property('NationIndex') if m else None, pc.get_editor_property('show_mouse_cursor') if pc else None)
            if cur != S['last']:
                S['last'] = cur; R['log'].append([round(now - S['t0'], 2)] + list(cur)); save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_WM_WATCH armed', TAG)
