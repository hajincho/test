"""Lyra PIE(Play 전에 무장): 시점 모드별(TP / 견착 FurinaShoulder / FP / FP+정조준 FurinaADS) 4발씩 쏘고, 발사 직후(같은 프레임) 새 총알의 생성 위치와 전방 벡터,
카메라 시선 레이(Visibility)의 첫 막힘, 총알 경로 구 추적(반지름 1.5, 폰 무시)의 첫 막힘(액터/컴포넌트/거리/시작 관통)을 기록.  -> Data/lyra_shoulder_probe.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_shoulder_probe.json'
R = {'shots': []}; S = {'stage': 0, 'ts': 0, 'mi': 0, 'fired': 0, 'last': -9, 'hb': 0, 'hbt': 0, 'known': set()}
MODES = [('TP', False, False, False), ('SHOULDER', False, True, False), ('FP', True, False, False), ('FP_ADS', True, False, True)]
OBJ = [getattr(unreal.ObjectTypeQuery, 'OBJECT_TYPE_QUERY%d' % i) for i in range(1, 7)]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def v(x): return [round(x.x, 1), round(x.y, 1), round(x.z, 1)]
def hit_info(res, origin):
    ok = res[0] if isinstance(res, tuple) else None
    h = res[1] if isinstance(res, tuple) and len(res) > 1 else res
    try: bl = bool(h.blocking_hit)
    except Exception: bl = bool(ok)
    if not bl: return None
    a = h.get_actor(); c = h.get_component()
    return {'dist': round((h.impact_point - origin).length(), 1), 'actor': a.get_name() if a else None, 'comp': c.get_name() if c else None, 'comp_class': c.get_class().get_name() if c else None, 'start_pen': bool(h.start_penetrating)}
def set_mode(pawn, tpl):
    pawn.get_editor_property('FurinaFPWanted').set_active(tpl[1]); pawn.get_editor_property('FurinaShoulder').set_active(tpl[2]); pawn.get_editor_property('FurinaADS').set_active(tpl[3])
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = unreal.GameplayStatics.get_time_seconds(w); pawn = unreal.GameplayStatics.get_player_pawn(w, 0); S['hb'] += 1
        if time.time() - S['hbt'] > 2: S['hbt'] = time.time(); R['heartbeat'] = [S['hb'], S['stage'], S['mi'], round(now, 1)]; save()
        if pawn is None: return
        pc = unreal.GameplayStatics.get_player_controller(w, 0); bc = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
        if S['stage'] == 0:
            S['stage'] = 1; S['ts'] = now; set_mode(pawn, MODES[0])
        elif S['stage'] == 1 and now - S['ts'] > 3.5:
            S['stage'] = 2; S['fired'] = 0; S['last'] = -9
        elif S['stage'] == 2:
            if S['fired'] < 4 and now - S['last'] > 0.3:
                S['last'] = now; S['fired'] += 1; before = {b.get_name() for b in unreal.GameplayStatics.get_all_actors_of_class(w, bc)}
                pawn.call_method('FurinaRifleShot')
                for b in unreal.GameplayStatics.get_all_actors_of_class(w, bc):
                    if b.get_name() in before: continue
                    l = b.get_actor_location(); f = b.get_actor_forward_vector(); cam = pc.player_camera_manager; cl = cam.get_camera_location(); cf = cam.get_actor_forward_vector()
                    row = {'mode': MODES[S['mi']][0], 'bullet': b.get_name(), 'spawn': v(l), 'fwd': [round(f.x, 3), round(f.y, 3), round(f.z, 3)], 'cam': v(cl), 'cam_fwd': [round(cf.x, 3), round(cf.y, 3), round(cf.z, 3)], 'pawn': v(pawn.get_actor_location()), 'ctrl_yaw': round(pc.get_control_rotation().yaw, 1), 'pawn_yaw': round(pawn.get_actor_rotation().yaw, 1), 'spawn_to_cam': round((l - cl).length(), 1)}
                    row['cam_ray'] = hit_info(unreal.SystemLibrary.line_trace_single(w, cl, cl + cf * 20000.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True), cl)
                    row['bullet_path'] = hit_info(unreal.SystemLibrary.sphere_trace_single_for_objects(w, l, l + f * 3000.0, 1.5, OBJ, False, [pawn, b], unreal.DrawDebugTrace.NONE, True), l)
                    R['shots'].append(row)
            if S['fired'] >= 4 and now - S['last'] > 1.0:
                S['mi'] += 1
                if S['mi'] >= len(MODES): S['stage'] = 3
                else: set_mode(pawn, MODES[S['mi']]); S['stage'] = 1; S['ts'] = now
        elif S['stage'] == 3:
            S['stage'] = 9; set_mode(pawn, MODES[0]); save(); print('LYRA_SHOULDER_PROBE', len(R['shots'])); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_SHOULDER_PROBE armed')
