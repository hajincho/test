"""PIE debug: pitch -8, slomo 0.05, fire 6 shots, every tick list all BP_FurinaBullet: name, FurinaRico read result or exception, velocity, location -> Data/rico_debug.json"""
import unreal, time, json, sys
SLO = sys.argv[1] if len(sys.argv) > 1 else '0.05'; NSHOT = int(sys.argv[2]) if len(sys.argv) > 2 else 6
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\rico_debug.json'
S = {'t0': time.time(), 'phase': 0, 'rows': [], 'n': 0, 'last': -1, 'ammo': []}
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
        try: flag = str(b.get_editor_property('FurinaRico'))
        except Exception as e: flag = 'ERR ' + str(e)[:80]
        p = b.get_actor_location(); v = b.get_velocity(); pm = b.get_component_by_class(unreal.ProjectileMovementComponent)
        S['rows'].append([round(t, 3), b.get_name(), flag, [round(x) for x in p.to_tuple()], [round(x) for x in v.to_tuple()], str(pm.get_editor_property('should_bounce')), str(pm.is_active())])
    if S['phase'] == 0 and t > 0.5: ctl.set_control_rotation(unreal.Rotator(roll=0.0, pitch=-8.0, yaw=ctl.get_control_rotation().yaw)); S['phase'] = 1; S['t1'] = t; unreal.SystemLibrary.execute_console_command(w, 'slomo ' + SLO)
    elif S['phase'] == 1 and t > S['t1'] + 1.0:
        if t - S['last'] > 0.15 / float(SLO) + 0.3 and S['n'] < NSHOT: S['last'] = t; S['n'] += 1; S['ammo'].append(pc.get_editor_property('FurinaAmmo')); pc.call_method('FurinaRifleShot')
        if S['n'] >= NSHOT and t - S['last'] > 0.2 / float(SLO) + 1.0:
            unreal.SystemLibrary.execute_console_command(w, 'slomo 1'); S['ammo'].append(pc.get_editor_property('FurinaAmmo')); json.dump({'ammo_before_each_shot_and_final': S['ammo'], 'rows': S['rows'][:400]}, open(OUT, 'w'), indent=1); print('RICO_DEBUG', len(S['rows'])); unreal.unregister_slate_post_tick_callback(S['h']); S['phase'] = 2
    del w, pc, ctl
S['h'] = unreal.register_slate_post_tick_callback(tick)
