"""Lyra PIE(Play 전에 무장): 푸리나 입력 확인. 30초 동안 0.5초마다 플레이어 폰 위치/속도/잔탄(FurinaAmmo)/컨트롤러/활성 입력 매핑을 기록.
사람이 그 사이 W를 누르고 좌클릭(사격)하면, 위치 변화·잔탄 감소로 입력 경로(IMC)가 살아있는지 알 수 있다. -> Data/lyra_input_probe.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_input_probe.json'
R = {'samples': []}; S = {'last': -9, 'n': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = unreal.GameplayStatics.get_time_seconds(w)
        if now - S['last'] < 0.5: return
        S['last'] = now; S['n'] += 1
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        row = {'t': round(now, 1)}
        if p is None: row['pawn'] = None
        else:
            l = p.get_actor_location(); v = p.get_velocity()
            row.update({'pawn': p.get_name(), 'loc': [round(l.x), round(l.y), round(l.z)], 'speed': round(v.length()), 'rot': round(p.get_control_rotation().yaw)})
            for k in ('FurinaAmmo', 'FurinaReserve', 'FurinaReloading'):
                try: row[k] = p.get_editor_property(k)
                except Exception as e: row[k] = 'err'
            try: row['crouched'] = bool(p.get_editor_property('is_crouched')); cm = p.get_editor_property('character_movement'); row['maxwalk'] = cm.get_editor_property('max_walk_speed'); row['maxcrouch'] = cm.get_editor_property('max_walk_speed_crouched'); row['gspeed'] = round(p.get_velocity().size_2d())
            except Exception as e: row['cr_err'] = str(e)[:60]
            pc = p.get_controller(); row['pc'] = pc.get_class().get_name() if pc else None
            try:
                k = unreal.Key(); k.set_editor_property('key_name', 'LeftMouseButton'); row['lmb_down'] = bool(pc.is_input_key_down(k))
                k2 = unreal.Key(); k2.set_editor_property('key_name', 'W'); row['w_down'] = bool(pc.is_input_key_down(k2))
                k3 = unreal.Key(); k3.set_editor_property('key_name', 'LeftShift'); row['shift_down'] = bool(pc.is_input_key_down(k3))
            except Exception as e: row['key_err'] = str(e)[:80]
        R['samples'].append(row); save()
        if S['n'] > 70: unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_INPUT_PROBE armed')
