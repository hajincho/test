"""PIE 자동 검증: 권총 교체(SwapMid 호출) -> 사격(FurinaRifleShot) -> 총알/탄피 클래스, 속도, 슬라이드, 탄약, 복귀.  결과 -> Saved/Scratch/p200_pie_test.json
열린 에디터에서 실행하면 L_FiringRange_WP 를 열고 PIE 를 시작한다. 진행은 슬레이트 틱 콜백으로 비동기."""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p200_pie_test.json'
R = {'steps': []}; S = {'stage': 0, 't0': 0.0, 'known': set()}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def pawn_state(p):
    d = {}
    for k in ('FurinaAmmo', 'FurinaReserve', 'FurinaAmmoStash', 'FurinaReserveStash', 'FurinaSlideCur', 'FurinaSwapCur', 'FurinaReloading'):
        try: d[k] = round(float(p.get_editor_property(k)), 3) if k.endswith('Cur') else p.get_editor_property(k)
        except Exception as e: d[k] = 'ERR'
    for k in ('FurinaPistolOn', 'FurinaSwapping'):
        try: d[k] = p.get_editor_property(k).is_active()
        except Exception: d[k] = 'ERR'
    for k in ('FurinaRifle', 'FurinaPistolFrame', 'FurinaPistolSlide', 'FurinaMag'):
        try: d['vis_' + k] = p.get_editor_property(k).is_visible()
        except Exception: d['vis_' + k] = 'ERR'
    try:
        sl = p.get_editor_property('FurinaPistolSlide'); d['slide_rel_x'] = round(sl.relative_location.x, 3)
        fr = p.get_editor_property('FurinaPistolFrame'); d['frame_world'] = [round(v, 1) for v in (fr.get_world_location().x, fr.get_world_location().y, fr.get_world_location().z)]
    except Exception: pass
    return d
def actor_names(w): return {a.get_name(): a.get_class().get_name() for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)}
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; S['t0'] = now; S['stage'] = 1; R['steps'].append(['start', pawn_state(p)]); S['known'] = set(actor_names(w)); return
        p = S['p']
        if S['stage'] == 1 and now - S['t0'] > 1.0:
            p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and now - S['t0'] > 0.6:
            R['steps'].append(['after swap to pistol', pawn_state(p)]); S['known'] = set(actor_names(w)); p.call_method('FurinaRifleShot'); S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3:
            cur = actor_names(w); S.setdefault('seen', {}); S.setdefault('bul', None)
            for k, v in cur.items():
                if k not in S['known']: S['seen'][k] = v
            for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
                if a.get_name() in S['seen'] and 'Bullet' in a.get_class().get_name() and S['bul'] is None:
                    pm = a.get_component_by_class(unreal.ProjectileMovementComponent); v = pm.get_editor_property('velocity') if pm else None
                    S['bul'] = {'class': a.get_class().get_name(), 'speed_cm_s': round(v.length(), 1) if v else None, 'gravity_scale': pm.get_editor_property('projectile_gravity_scale') if pm else None, 'loc': str(a.get_actor_location())}
            if now - S['t0'] > 0.4:
                R['steps'].append(['pistol shot (union over 0.4s)', {'new_actors': dict(S['seen']), 'bullet': S['bul'], 'state': pawn_state(p)}]); S['seen'] = {}; S['bul'] = None; S['t0'] = now; S['stage'] = 4
        elif S['stage'] == 4 and now - S['t0'] > 1.0:
            R['steps'].append(['1s later (slide back to 0, case on ground)', pawn_state(p)]); p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 5
        elif S['stage'] == 5 and now - S['t0'] > 0.6:
            R['steps'].append(['after swap back to rifle', pawn_state(p)]); S['known'] = set(actor_names(w)); p.call_method('FurinaRifleShot'); S['t0'] = now; S['stage'] = 6
        elif S['stage'] == 6:
            S.setdefault('seen6', {})
            for k, v in actor_names(w).items():
                if k not in S['known']: S['seen6'][k] = v
            if now - S['t0'] > 0.4:
                R['steps'].append(['rifle shot after returning (union 0.4s)', {'new_actors': dict(S['seen6']), 'state': pawn_state(p)}]); S['stage'] = 9; save()
                unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h']); print('P200_PIE_TEST done')
        elif S['stage'] == 99:
            pass
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h']); print('P200_PIE_TEST done')
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if 'FiringRange' not in str(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name()): R['load'] = les.load_level('/ShooterMaps/Maps/L_FiringRange_WP')
S['h'] = unreal.register_slate_post_tick_callback(tick)
les.editor_request_begin_play(); save(); print('P200_PIE_TEST armed')
