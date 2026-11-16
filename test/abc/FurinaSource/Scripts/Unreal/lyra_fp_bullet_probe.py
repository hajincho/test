"""Lyra PIE(Play 전에 무장): 1인칭(FurinaFPWanted)으로 바꾼 뒤 FurinaRifleShot 으로 12발(0.15초 간격) 쏘며 총알 BP 액터별 추적.
기록: 생성 위치/시각, 마지막 위치, 이동 거리, 속도, 살아있던 시간. 0.5초 넘게 살아있는데 50cm 넘게 못 간 총알은 '박힘'으로 보고 주변 컴포넌트(구 반지름 8)를 조회.
추가: 총구 월드 위치, 카메라 위치/방향, 컨트롤 회전.  -> FurinaSource/Data/lyra_fp_bullet_probe.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_bullet_probe.json'
R = {'bullets': {}, 'stuck': []}; S = {'stage': 0, 'ts': 0, 'fired': 0, 'last': -9, 'hb': 0, 'hbt': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def comp(pawn, name, cls=unreal.SceneComponent):
    for c in pawn.get_components_by_class(cls):
        if c.get_name() == name: return c
    return None
def v(x): return [round(x.x, 1), round(x.y, 1), round(x.z, 1)]
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = unreal.GameplayStatics.get_time_seconds(w); pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        S['hb'] += 1
        if time.time() - S['hbt'] > 2: S['hbt'] = time.time(); R['heartbeat'] = [S['hb'], S['stage'], round(now, 1)]; save()
        if pawn is None: return
        bc = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
        if S['stage'] == 0:
            pawn.get_editor_property('FurinaFPWanted').set_active(True); S['stage'] = 1; S['ts'] = now
        elif S['stage'] == 1 and now - S['ts'] > 4:
            rifle = comp(pawn, 'FurinaRifle'); pc = unreal.GameplayStatics.get_player_controller(w, 0)
            R['muzzle_world'] = v(rifle.get_world_transform().transform_location(unreal.Vector(0, 48.5, 3.1)))
            cam = pc.player_camera_manager; R['cam_loc'] = v(cam.get_camera_location()); R['cam_rot'] = str(cam.get_camera_rotation()); R['ctrl_rot'] = str(pc.get_control_rotation())
            R['rifle_parent'] = rifle.get_attach_parent().get_name() if rifle.get_attach_parent() else None; R['rifle_socket'] = str(rifle.get_attach_socket_name())
            S['stage'] = 2; S['ts'] = now
        elif S['stage'] == 2:
            if S['fired'] < 12 and now - S['last'] > 0.15: S['last'] = now; S['fired'] += 1; pawn.call_method('FurinaRifleShot')
            if S['fired'] >= 12 and now - S['last'] > 2.5: S['stage'] = 3
        elif S['stage'] == 3:
            R['summary'] = {'fired': S['fired'], 'tracked': len(R['bullets']), 'stuck': len(R['stuck'])}
            for k, b in R['bullets'].items(): b['moved'] = round(sum((b['last'][i] - b['first'][i]) ** 2 for i in range(3)) ** 0.5, 1)
            S['stage'] = 9; save(); print('LYRA_FP_BULLET_PROBE', R['summary']); unreal.unregister_slate_post_tick_callback(S['h'])
        if S['stage'] in (2, 3):
            seen = set()
            for b in unreal.GameplayStatics.get_all_actors_of_class(w, bc):
                n = b.get_name(); seen.add(n); l = b.get_actor_location(); d = R['bullets'].get(n)
                pm = b.get_component_by_class(unreal.ProjectileMovementComponent); vel = pm.get_editor_property('velocity') if pm else None
                if d is None: R['bullets'][n] = d = {'t0': round(now, 2), 'first': v(l), 'last': v(l), 'speed0': round(vel.length(), 0) if vel else None, 'alive': 0}
                d['last'] = v(l); d['alive'] = round(now - d['t0'], 2); d['speed'] = round(vel.length(), 0) if vel else None
                mv = sum((d['last'][i] - d['first'][i]) ** 2 for i in range(3)) ** 0.5
                if d['alive'] > 0.5 and mv < 50 and n not in [s['name'] for s in R['stuck']]:
                    objs = [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY3, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY4,
                            unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY5, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY6]
                    comps = unreal.SystemLibrary.sphere_overlap_components(w, l, 8.0, objs, unreal.PrimitiveComponent, [b])
                    R['stuck'].append({'name': n, 'loc': v(l), 'moved': round(mv, 1), 'alive': d['alive'], 'speed': d['speed'], 'overlaps': [c.get_owner().get_name() + '/' + c.get_name() + ' (' + c.get_class().get_name() + ')' for c in (comps if isinstance(comps, (list, tuple)) else comps[1] if comps else [])][:12]})
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_FP_BULLET_PROBE armed')
