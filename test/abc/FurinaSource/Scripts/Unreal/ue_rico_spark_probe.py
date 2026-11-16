"""PIE: pitch -8, fires N shots (0.45 s apart) at the ground; every tick records the BP_RicoSpark actors (spawned on a ricochet) with the game time first / last seen -> Data/rico_spark_probe.json (lifetime should be ~0.1 s)"""
import unreal, time, json, sys
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
N = int(sys.argv[1]) if len(sys.argv) > 1 else 14
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\rico_spark_probe.json'
S = {'t0': time.time(), 'phase': 0, 'n': 0, 'last': -1, 'sparks': {}}
def tick(dt):
    try: _tick()
    except Exception:
        import traceback; json.dump({'error': traceback.format_exc()}, open(OUT, 'w'), indent=1); unreal.unregister_slate_post_tick_callback(S['h'])
def _tick():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']; pc = unreal.GameplayStatics.get_player_character(w, 0); ctl = unreal.GameplayStatics.get_player_controller(w, 0); gt = unreal.GameplayStatics.get_time_seconds(w)
    cls = unreal.load_class(None, '/Game/Furina/M4/BP_RicoSpark.BP_RicoSpark_C')
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, cls):
        e = S['sparks'].setdefault(a.get_name(), [gt, gt]); e[1] = gt
    if S['phase'] == 0 and t > 0.5: ctl.set_control_rotation(unreal.Rotator(roll=0.0, pitch=-8.0, yaw=ctl.get_control_rotation().yaw)); S['phase'] = 1; S['t1'] = t
    elif S['phase'] == 1 and t > S['t1'] + 1.0:
        if t - S['last'] > 0.45 and S['n'] < N: S['last'] = t; S['n'] += 1; pc.call_method('FurinaRifleShot')
        if S['n'] >= N and t - S['last'] > 1.5:
            res = {'shots': S['n'], 'sparks': {k: dict(first=round(v[0], 3), last_seen=round(v[1], 3), seen_for_s=round(v[1] - v[0], 3)) for k, v in S['sparks'].items()}}
            json.dump(res, open(OUT, 'w'), indent=1); print('RICO_SPARK_PROBE', len(S['sparks'])); unreal.unregister_slate_post_tick_callback(S['h']); S['phase'] = 2
    del w, pc, ctl
S['h'] = unreal.register_slate_post_tick_callback(tick)
