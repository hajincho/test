"""Lyra PIE(Play 전에 무장): 푸리나=Lyra 영웅 통합 확인.
 t0: 플레이어 폰 클래스/컨트롤러/팀/체력, 모든 폰(봇 마네킹?)의 클래스/컨트롤러/팀/체력, 월드의 무기 관련 액터 수
 +8s: 플레이어 체력 컴포넌트 DamageSelfDestruct 호출 -> +1.5s 체력/사망 상태, +10s 새 플레이어 폰(리스폰) 클래스
-> Data/lyra_hero_probe.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_hero_probe.json'
R = {'phases': {}}; S = {'stage': 0, 'ts': 0, 'hb': 0, 'hbt': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def pinfo(p):
    row = {'name': p.get_name(), 'class': p.get_class().get_name(), 'parent': p.get_class().get_super_struct().get_name() if hasattr(p.get_class(), 'get_super_struct') else None}
    c = p.get_controller(); row['controller'] = c.get_class().get_name() if c else None; row['player_controlled'] = bool(p.is_player_controlled())
    try:
        h = p.get_component_by_class(unreal.LyraHealthComponent); row['health'] = [round(h.get_health(), 1), round(h.get_max_health(), 1)] if h else None
        row['death_state'] = str(h.get_death_state()) if h else None
    except Exception as e: row['health_err'] = str(e)[:80]
    try: row['team'] = str(p.get_generic_team_id())
    except Exception as e: row['team_err'] = str(e)[:80]
    try:
        asc = p.get_ability_system_component(); row['asc'] = asc.get_class().get_name() if asc else None
    except Exception as e: row['asc_err'] = str(e)[:80]
    row['has_pawn_ext'] = bool(p.get_component_by_class(unreal.LyraPawnExtensionComponent)) if hasattr(unreal, 'LyraPawnExtensionComponent') else None
    return row
def snapshot(w):
    pawns = [pinfo(p) for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn)]
    names = [a.get_class().get_name() for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)]
    return {'pawns': pawns, 'weapon_actors': [n for n in names if any(k in n for k in ('WeaponSpawner', 'Pickup', 'Grenade', 'Rifle', 'Pistol', 'Shotgun'))][:20], 'player_pawn': str(unreal.GameplayStatics.get_player_pawn(w, 0))}
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = unreal.GameplayStatics.get_time_seconds(w); S['hb'] += 1
        if time.time() - S['hbt'] > 2: S['hbt'] = time.time(); R['heartbeat'] = [S['hb'], S['stage'], round(now, 1)]; save()
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if pawn is None: return
            S['stage'] = 1; S['ts'] = now
        elif S['stage'] == 1 and now - S['ts'] > 8:
            R['phases']['t0'] = snapshot(w); S['stage'] = 2; S['ts'] = now
            try: unreal.SystemLibrary.execute_console_command(w, 'DamageSelfDestruct'); R['self_destruct_called'] = True
            except Exception as e: R['self_destruct_err'] = str(e)[:150]
        elif S['stage'] == 2 and now - S['ts'] > 1.5: R['phases']['after_1_5s'] = snapshot(w); S['stage'] = 3
        elif S['stage'] == 3 and now - S['ts'] > 12:
            R['phases']['after_12s'] = snapshot(w); S['stage'] = 9; save(); print('LYRA_HERO_PROBE done'); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_HERO_PROBE armed')
