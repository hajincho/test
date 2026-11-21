"""Lyra 에디터(`py <파일> [태그]`, run_ue_probe.ps1): 무기 선택창 열기/닫기 확인.
 FurinaWeaponMenuToggle(= Tab 과 같은 경로) 로 열기 -> UI 포함 스크린샷 -> 위젯 CloseMenu(= 위젯의 Tab/Esc 경로) -> 다시 Toggle 열기 -> Toggle 닫기.
 기록: Data/lyra_weapon_menu_probe_<태그>.json, 스크린샷은 Saved/Screenshots 의 새 파일을 Data/wmenu_<태그>_<단계>.png 로 복사"""
import unreal, json, sys, time, traceback, os, glob, shutil
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_weapon_menu_probe_%s.json' % TAG
SS = 'C:/Users/fromj/Downloads/test/test/abc/Saved/Screenshots'
R = {'tag': TAG, 'steps': []}; S = {'st': 'open', 't': 0, 'i': 0, 'shots_before': set()}
STEPS = [('toggle_open', 'toggle'), ('nation1', 'nation:1'), ('nation2', 'nation:2'), ('close_widget', 'close'), ('toggle_open2', 'toggle'), ('toggle_close', 'toggle')]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def allshots(): return set(glob.glob(SS + '/**/*.png', recursive=True))
def state(p, pc):
    w = p.get_editor_property('FurinaWeaponMenu'); e = {'widget': w.get_name() if w else None}
    if w:
        e['in_viewport'] = w.is_in_viewport()
        btn = [x for x in unreal.WidgetLibrary.get_all_widgets_of_class(w, unreal.Button, False)] if False else None
    try: e['cursor'] = pc.get_editor_property('show_mouse_cursor')
    except Exception as ex: e['cursor'] = str(ex)[:60]
    return e
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'play'; S['t'] = now + 4; return
        if st == 'play':
            if now >= S['t']: LES().editor_request_begin_play(); S['st'] = 'wait'; S['t'] = now + 90
            return
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        if st == 'wait':
            if p is not None and pc is not None: S['st'] = 'settle'; S['t'] = now + 6
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        if st == 'settle' and now >= S['t']:
            R['before'] = state(p, pc); S['st'] = 'step'; S['sub'] = 0; S['t'] = now; return
        if st == 'step' and now >= S['t']:
            name, act = STEPS[S['i']]
            if S['sub'] == 0:
                if act == 'toggle': p.call_method('FurinaWeaponMenuToggle')
                elif act.startswith('nation:'):
                    wm = p.get_editor_property('FurinaWeaponMenu'); wm.set_editor_property('NationIndex', int(act.split(':')[1])); wm.call_method('ApplyNation')
                else: p.get_editor_property('FurinaWeaponMenu').call_method('CloseMenu')
                S['sub'] = 1; S['t'] = now + 1.5; return
            if S['sub'] == 1:
                S['before_shots'] = allshots(); unreal.SystemLibrary.execute_console_command(w, 'shot showui'); S['sub'] = 2; S['t'] = now + 2.0; return
            new = sorted(allshots() - S['before_shots'], key=os.path.getmtime)
            e = state(p, pc); e['step'] = name
            if new: shutil.copy(new[-1], D + '/wmenu_%s_%s.png' % (TAG, name)); e['shot'] = 'wmenu_%s_%s.png' % (TAG, name)
            R['steps'].append(e); save(); S['i'] += 1; S['sub'] = 0; S['t'] = now + 0.5
            if S['i'] >= len(STEPS): S['st'] = 'end'; S['t'] = now + 0.5
            return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); R['done'] = True; save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_WEAPON_MENU_PROBE armed', TAG)
