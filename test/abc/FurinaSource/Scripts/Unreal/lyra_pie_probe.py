"""LYRA 에디터: Play 전에 실행해 무장 -> PIE 에서 푸리나 폰/컨트롤러/탄약 확인 + 체력 컴포넌트 달린 표적에 5발 사격(FurinaDamage 를 임시로 10으로) 후 체력 변화 기록
-> FurinaSource/Data/lyra_pie_probe.json   (끝나면 FurinaDamage CDO 를 0으로 되돌린다)"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_pie_probe.json'
R = {'log': []}; S = {'t0': time.time(), 'stage': 0, 'fired': 0, 'last': -1, 'tw': None}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def bullet_cdo():
    return unreal.get_default_object(unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C'))
def targets(w):
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        try: h = a.get_component_by_class(unreal.LyraHealthComponent)
        except Exception: h = None
        if h: out.append((a, h))
    return out
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        t = time.time() - S['t0']; pc = unreal.GameplayStatics.get_player_controller(w, 0); pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['tw'] is None: S['tw'] = t
        if S['stage'] == 0:
            if pawn is None or pc is None:
                if t - S['tw'] > 40: R['log'].append('no pawn after 40s'); R['pc'] = str(pc); save(); S['stage'] = 9; unreal.unregister_slate_post_tick_callback(S['h'])
                return
            R['pc'] = pc.get_class().get_name(); R['pawn'] = pawn.get_class().get_name(); l = pawn.get_actor_location(); R['loc'] = [l.x, l.y, l.z]
            for p in ('FurinaAmmo', 'FurinaReserve'):
                try: R[p] = pawn.get_editor_property(p)
                except Exception as e: R[p] = 'ERR ' + str(e)[:60]
            try: R['view_target'] = pc.get_view_target().get_name()
            except Exception: pass
            S['ts'] = t; S['stage'] = 1; save()
        elif S['stage'] == 1 and t - S['ts'] > 4:
            tg = targets(w); R['targets'] = [[a.get_name(), a.get_class().get_name(), round(h.get_health(), 1), round(h.get_max_health(), 1)] for a, h in tg][:12]
            pl = pawn.get_actor_location(); near = [(((a.get_actor_location() - pl).length(), a, h)) for a, h in tg if a != pawn]; near.sort(key=lambda x: x[0])
            if not near: R['log'].append('no health targets'); save(); S['stage'] = 9; unreal.unregister_slate_post_tick_callback(S['h']); return
            S['dist'], S['tgt'], S['hc'] = near[0]; R['target'] = [S['tgt'].get_name(), round(S['dist']), round(S['hc'].get_health(), 1)]
            bullet_cdo().set_editor_property('FurinaDamage', 10.0)
            cam = pc.player_camera_manager.get_camera_location(); tl = S['tgt'].get_actor_location() + unreal.Vector(0, 0, 60)
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(cam, tl)); S['ts'] = t; S['stage'] = 2; S['h0'] = S['hc'].get_health()
        elif S['stage'] == 2 and t - S['ts'] > 0.6:
            if S['fired'] < 5 and t - S['last'] > 0.3: S['last'] = t; S['fired'] += 1; pawn.call_method('FurinaRifleShot')
            if S['fired'] >= 5 and t - S['last'] > 2.5:
                R['health_before'] = S['h0']; R['health_after'] = S['hc'].get_health(); R['ammo_after'] = pawn.get_editor_property('FurinaAmmo')
                bullet_cdo().set_editor_property('FurinaDamage', 0.0); S['stage'] = 9; save(); print('LYRA_PIE_PROBE', R); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: bullet_cdo().set_editor_property('FurinaDamage', 0.0)
        except Exception: pass
        unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_PIE_PROBE armed')
