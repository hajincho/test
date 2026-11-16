"""PIE: spawns existing Niagara systems (project Sparks_FXS, engine DirectionalBurst, SimpleExplosion) in front of the player at the rifle muzzle (scale given by argv[1], default 0.15) one after another
and takes a HighResShot 0.35 s after each spawn, to judge whether they can serve as muzzle effects. usage: py ue_niagara_spawn_test.py [scale]"""
import unreal, time, sys
SC = float(sys.argv[1]) if len(sys.argv) > 1 else 0.15
SYS = ['/Game/3DPlatformerGameBundle/NiagaraSystems/Sparks_FXS', '/Niagara/DefaultAssets/Templates/Systems/DirectionalBurst', '/Niagara/DefaultAssets/Templates/Systems/SimpleExplosion']
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])     # drop a previous (failed) run's callback
except Exception: pass
S = {'t0': time.time(), 'i': 0, 'phase': 0, 'tn': 0}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']; pc = unreal.GameplayStatics.get_player_character(w, 0)
    if S['i'] >= len(SYS):
        unreal.unregister_slate_post_tick_callback(S['h']); return
    if S['phase'] == 0 and t > 1.0 + S['i'] * 2.0:
        gun = pc.get_editor_property('FurinaRifle'); T = gun.get_world_transform(); loc = T.transform_location(unreal.Vector(0, 41, 3.4)); rot = T.rotation.rotator()
        unreal.NiagaraFunctionLibrary.spawn_system_at_location(w, unreal.load_asset(SYS[S['i']]), loc, rot, unreal.Vector(SC, SC, SC), True, True); S['tn'] = t; S['phase'] = 1
    elif S['phase'] == 1 and t - S['tn'] > 0.35:
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['phase'] = 0; S['i'] += 1
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
