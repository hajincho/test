"""Lyra PIE(Play 전에 무장): 1인칭에서 컨트롤 피치를 0 / -20 / -45 / -70 / +30 으로 바꿔 가며 각 5발씩 쏜다.
각 총알의 첫 샘플(생성 위치, 속도 방향)에서 총알 경로를 구 추적(반지름 1.5, 모든 물체 유형, 폰 무시)으로 3000cm 까지 쏴서 '첫 막힘'(액터/컴포넌트/거리)을 기록.
총구/카메라 위치와 조준 방향(컨트롤 회전)도 기록. 막힘 거리가 100cm 미만이면 박힘 후보.  -> Data/lyra_fp_bullet_probe2.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_bullet_probe2.json'
R = {'shots': []}; S = {'stage': 0, 'ts': 0, 'fired': 0, 'last': -9, 'pi': 0, 'hb': 0, 'hbt': 0, 'seen': set()}
PITCHES = [0.0, -20.0, -45.0, -70.0, 30.0]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def comp(pawn, name, cls=unreal.SceneComponent):
    for c in pawn.get_components_by_class(cls):
        if c.get_name() == name: return c
    return None
def v(x): return [round(x.x, 1), round(x.y, 1), round(x.z, 1)]
OBJ = [getattr(unreal.ObjectTypeQuery, 'OBJECT_TYPE_QUERY%d' % i) for i in range(1, 7)]
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = unreal.GameplayStatics.get_time_seconds(w); pawn = unreal.GameplayStatics.get_player_pawn(w, 0); S['hb'] += 1
        if time.time() - S['hbt'] > 2: S['hbt'] = time.time(); R['heartbeat'] = [S['hb'], S['stage'], S['pi'], round(now, 1)]; save()
        if pawn is None: return
        pc = unreal.GameplayStatics.get_player_controller(w, 0); bc = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
        # 새로 생긴 총알: 경로 추적
        for b in unreal.GameplayStatics.get_all_actors_of_class(w, bc):
            n = b.get_name()
            if n in S['seen']: continue
            S['seen'].add(n); l = b.get_actor_location(); pm = b.get_component_by_class(unreal.ProjectileMovementComponent); vel = pm.get_editor_property('velocity') if pm else None
            row = {'bullet': n, 'pitch_set': PITCHES[min(S['pi'], len(PITCHES) - 1)], 'spawn': v(l), 'ctrl_rot': str(pc.get_control_rotation())}
            if vel and vel.length() > 1:
                d = vel / vel.length(); row['dir'] = [round(d.x, 3), round(d.y, 3), round(d.z, 3)]; row['cam_loc'] = v(pc.player_camera_manager.get_camera_location())
                hit = unreal.SystemLibrary.sphere_trace_single_for_objects(w, l, l + d * 3000.0, 1.5, OBJ, False, [pawn], unreal.DrawDebugTrace.NONE, True)
                ok = hit[0] if isinstance(hit, tuple) else hit
                if ok:
                    h = hit[1] if isinstance(hit, tuple) else None
                    if h is not None:
                        row['first_block'] = {'dist': round((h.impact_point - l).length(), 1), 'actor': h.get_actor().get_name() if h.get_actor() else None, 'comp': h.get_component().get_name() if h.get_component() else None,
                                              'comp_class': h.get_component().get_class().get_name() if h.get_component() else None, 'start_penetrating': bool(h.start_penetrating)}
                else: row['first_block'] = None
            R['shots'].append(row)
        if S['stage'] == 0:
            pawn.get_editor_property('FurinaFPWanted').set_active(True); S['stage'] = 1; S['ts'] = now
        elif S['stage'] == 1 and now - S['ts'] > 4:
            R['muzzle_world'] = v(comp(pawn, 'FurinaRifle').get_world_transform().transform_location(unreal.Vector(0, 48.5, 3.1))); S['stage'] = 2; S['ts'] = now; S['pi'] = 0
            r = pc.get_control_rotation(); r.pitch = PITCHES[0]; pc.set_control_rotation(r)
        elif S['stage'] == 2:
            if now - S['ts'] < 0.6: return
            if S['fired'] < 5 and now - S['last'] > 0.25: S['last'] = now; S['fired'] += 1; pawn.call_method('FurinaRifleShot')
            if S['fired'] >= 5 and now - S['last'] > 0.9:
                S['pi'] += 1; S['fired'] = 0
                if S['pi'] >= len(PITCHES): S['stage'] = 3
                else: r = pc.get_control_rotation(); r.pitch = PITCHES[S['pi']]; pc.set_control_rotation(r); S['ts'] = now
        elif S['stage'] == 3:
            S['stage'] = 9; save(); print('LYRA_FP_BULLET_PROBE2', len(R['shots'])); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_FP_BULLET_PROBE2 armed')
