"""Lyra PIE(실행 중 무장해도 됨): 3인칭으로 서서 폰을 -90도(왼쪽 옆), +90도(오른쪽 옆), 0도(뒤)로 돌려가며 HighResShot 3 을 저장(소총과 탄창 옆모습/뒷모습 확인용).
(재장전 없이, 총을 든 채 사격 직후 자세) -> Data/lyra_idle_view.json, 스크린샷은 Saved/Screenshots/WindowsEditor/"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_idle_view.json'
R = {'shots': []}; S = {'st': 0, 't': 0, 'i': 0, 'base': None}
YAWS = [-90.0, 90.0, 0.0]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if p is None: return
        now = time.time()
        if S['st'] == 0:
            p.get_editor_property('FurinaFPWanted').set_active(False); S['base'] = p.get_actor_rotation().yaw; S['st'] = 1; S['t'] = now + 3
        elif S['st'] == 1 and now >= S['t']:
            p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=S['base'] + YAWS[S['i']]), False); S['st'] = 2; S['t'] = now + 2.5
        elif S['st'] == 2 and now >= S['t']:
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 3'); R['shots'].append({'yaw': YAWS[S['i']], 'at': now}); save(); S['i'] += 1
            if S['i'] >= len(YAWS): R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h']); return
            S['st'] = 1; S['t'] = now + 1
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_IDLE_VIEW armed')
