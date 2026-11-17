"""Lyra PIE(Play 전에 무장): 봇 비용 측정. 워밍업 25초 -> CSV 12초(봇 있음) -> 봇 폰/컨트롤러 삭제 -> 5초 -> CSV 12초(봇 없음).
봇 수/클래스/AI 컨트롤러, 삭제 개수를 기록 -> Data/lyra_bot_cost.json  (CSV 는 Saved/Profiling/CSV 의 최근 두 개)"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_bot_cost.json'
R = {}; S = {'st': 'wait', 't': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def cmd(w, c): unreal.SystemLibrary.execute_console_command(w, c)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time()
        if S['st'] == 'wait':
            if unreal.GameplayStatics.get_player_pawn(w, 0) is None: return
            S['st'] = 'warm1'; S['t'] = now + 25
        elif S['st'] == 'warm1' and now >= S['t']:
            bots = [p for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character) if 'Mannequin' in p.get_class().get_name()]
            R['bots_before'] = [[b.get_name(), b.get_controller().get_class().get_name() if b.get_controller() else None, round(b.get_velocity().length())] for b in bots]
            cmd(w, 'csvprofile start'); S['st'] = 'rec1'; S['t'] = now + 12; R['rec1_at'] = now
        elif S['st'] == 'rec1' and now >= S['t']:
            cmd(w, 'csvprofile stop')
            bots = [p for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character) if 'Mannequin' in p.get_class().get_name()]; n = 0
            for b in bots:
                c = b.get_controller()
                if c: c.destroy_actor()
                b.destroy_actor(); n += 1
            R['destroyed'] = n; S['st'] = 'warm2'; S['t'] = now + 6; save()
        elif S['st'] == 'warm2' and now >= S['t']:
            R['bots_after'] = len([p for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character) if 'Mannequin' in p.get_class().get_name()])
            cmd(w, 'csvprofile start'); S['st'] = 'rec2'; S['t'] = now + 12
        elif S['st'] == 'rec2' and now >= S['t']:
            cmd(w, 'csvprofile stop'); R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_BOT_COST armed')
