"""PIE: spawns /Game/NiagaraExamples/FX_Weapons/MuzzleFlashes/NS_MuzzleFlash at the rifle muzzle with the yaw offsets given in argv (default 90 0 -90) relative to the rifle component rotation,
GlobalScale from argv scale (set through SetVariableFloat), first person, one HighResShot 0.04 s after each spawn. usage: py ue_gunfire_test.py <scale> <yaw> [<yaw> ...]"""
import unreal, time, sys
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
SC = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
YAWS = [float(a) for a in sys.argv[2:]] or [90.0, 0.0, -90.0]
S = {'t0': time.time(), 'i': 0, 'phase': -1, 'tn': 0}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']; pc = unreal.GameplayStatics.get_player_character(w, 0)
    if S['i'] >= len(YAWS): unreal.unregister_slate_post_tick_callback(S['h']); return
    if S['phase'] == -1 and t > 0.5: pc.get_editor_property('FurinaFPWanted').set_active(True); S['phase'] = 0
    elif S['phase'] == 0 and t > 1.5 + S['i'] * 2.0:
        gun = pc.get_editor_property('FurinaRifle'); T = gun.get_world_transform(); loc = T.transform_location(unreal.Vector(0, 41, 3.4))
        rot = unreal.MathLibrary.compose_rotators(unreal.Rotator(0, 0, YAWS[S['i']]), T.rotation.rotator())
        c = unreal.NiagaraFunctionLibrary.spawn_system_at_location(w, unreal.load_asset('/Game/NiagaraExamples/FX_Weapons/MuzzleFlashes/NS_MuzzleFlash'), loc, rot, unreal.Vector(1, 1, 1), True, True)
        try: c.set_variable_float('Global Scale', SC)
        except Exception as e: print('GS', e)
        try: c.set_variable_bool('Use Bullet Shell', False)
        except Exception as e: print('UBS', e)
        S['tn'] = t; S['phase'] = 1
    elif S['phase'] == 1 and t - S['tn'] > 0.04:
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['phase'] = 0; S['i'] += 1
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
