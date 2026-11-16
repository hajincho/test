"""PIE: checks magazine 20 / reserve 600: reads (ammo, reserve) at start, fires 6 shots (FurinaRifleShot every 0.15 s), reads, requests a reload, takes a HighResShot 1.5 s into it (HUD pips filling),
reads again 3.6 s after the request (expected 20 / 594) -> Data/ammo_2060_probe.json"""
import unreal, time, json
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\ammo_2060_probe.json'
S = {'t0': time.time(), 'fired': 0, 'last': -1, 'log': {}, 'stage': 0, 'tr': 0}
def rd(pc): return [pc.get_editor_property('FurinaAmmo'), pc.get_editor_property('FurinaReserve'), bool(pc.get_editor_property('FurinaReloading'))]
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0); t = time.time() - S['t0']
    if S['stage'] == 0:
        if 'start' not in S['log']: S['log']['start'] = rd(pc)
        if t - S['last'] > 0.15 and S['fired'] < 6: S['last'] = t; S['fired'] += 1; pc.call_method('FurinaRifleShot')
        if S['fired'] >= 6 and t - S['last'] > 0.5: S['log']['after_6_shots'] = rd(pc); pc.call_method('FurinaRequestReload'); S['tr'] = t; S['stage'] = 1
    elif S['stage'] == 1 and t - S['tr'] > 1.5: unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['log']['mid_reload'] = rd(pc); S['stage'] = 2
    elif S['stage'] == 2 and t - S['tr'] > 3.8:
        S['log']['after_reload'] = rd(pc); json.dump(S['log'], open(OUT, 'w'), indent=1); print('AMMO_PROBE', S['log']); unreal.unregister_slate_post_tick_callback(S['h'])
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
