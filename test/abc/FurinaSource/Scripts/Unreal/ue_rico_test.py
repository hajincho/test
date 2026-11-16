"""PIE (2026-11-16): ricochet statistics of BP_FurinaBullet. Looks at the ground at pitch -8 deg (grazing angle about 8 deg < 20 deg) and fires 40 shots (two magazines, reload in between), then at pitch -35 deg
(grazing 35 deg) and fires 20 shots. A bullet counts as a ricochet when its variable FurinaRico reads 1 (set by the BP only on a ricochet). Result -> Data/rico_test.json
(expected: about 40 % of the shallow shots, 0 % of the steep shots).   usage: py ue_rico_test.py"""
import unreal, time, json
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\rico_test.json'
S = {'t0': time.time(), 'phase': 0, 'seen': {}, 'fired': 0, 'last': -1, 'groups': {'shallow': {'shots': 0, 'rico': set()}, 'steep': {'shots': 0, 'rico': set()}}, 'cur': 'shallow', 'mag': 0}
def tick(dt):
    try: _tick()
    except Exception:
        import traceback; json.dump({'error': traceback.format_exc()}, open(OUT, 'w'), indent=1); unreal.unregister_slate_post_tick_callback(S['h'])
def _tick():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']; pc = unreal.GameplayStatics.get_player_character(w, 0); ctl = unreal.GameplayStatics.get_player_controller(w, 0)
    cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    for b in unreal.GameplayStatics.get_all_actors_of_class(w, cls):
        try: flag = b.get_editor_property('FurinaRico')
        except Exception: flag = None
        if flag == 1 and b.get_name() not in S['seen']:
            S['seen'][b.get_name()] = [S['cur'], [round(x, 1) for x in b.get_velocity().to_tuple()]]; S['groups'][S['cur']]['rico'].add(b.get_name())
    ph = S['phase']
    if ph == 0 and t > 0.5:
        r = ctl.get_control_rotation(); S['yaw'] = r.yaw; ctl.set_control_rotation(unreal.Rotator(roll=0.0, pitch=-8.0, yaw=r.yaw)); S['phase'] = 1; S['t1'] = t
    elif ph in (1, 3, 5) and t > S['t1'] + 1.0:
        if t - S['last'] > 0.15 and S['fired'] < 20:
            S['last'] = t; S['fired'] += 1; S['groups'][S['cur']]['shots'] += 1; pc.call_method('FurinaRifleShot')
        if S['fired'] >= 20 and t - S['last'] > 1.0:
            if ph == 5: S['phase'] = 7; S['t7'] = t
            else: pc.call_method('FurinaRequestReload'); S['phase'] = ph + 1; S['t1'] = t
    elif ph in (2, 4) and t > S['t1'] + 4.5:
        S['fired'] = 0; S['t1'] = t - 0.5
        if ph == 4: S['cur'] = 'steep'; ctl.set_control_rotation(unreal.Rotator(roll=0.0, pitch=-35.0, yaw=S['yaw']))
        S['phase'] = ph + 1
    elif ph == 7 and t > S['t7'] + 1.5:
        res = {k: dict(shots=v['shots'], ricochets=len(v['rico']), rate=round(len(v['rico']) / max(1, v['shots']), 3)) for k, v in S['groups'].items()}
        res['ricochet_first_velocity_cms'] = S['seen']; json.dump(res, open(OUT, 'w'), indent=1); print('RICO_TEST', {k: res[k] for k in ('shallow', 'steep')}); unreal.unregister_slate_post_tick_callback(S['h']); S['phase'] = 8
    del w, pc, ctl
S['h'] = unreal.register_slate_post_tick_callback(tick)
