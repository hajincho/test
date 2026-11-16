"""PIE: for each view (third person, first person hip, ADS) fires one shot and takes HighResShots at the shot tick and 0.06 s / 0.15 s after it, to look for effects that appear a little after the flash.
-> 9 newest Saved/Screenshots/WindowsEditor/HighresScreenshot*.png in order TP(3) FP(3) ADS(3)"""
import unreal, time
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
S = {'t0': time.time(), 'step': 0, 'tn': 0, 'k': 0}
OFFS = [0.0, 0.06, 0.15]
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0); t = time.time() - S['t0']; st = S['step']
    def ads(): return pc.get_components_by_tag(unreal.ActorComponent, 'FurinaADS')[0]
    def shot_start(): S['tn'] = t; S['k'] = 0; pc.call_method('FurinaRifleShot'); unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['k'] = 1
    def shot_follow():
        if S['k'] < 3 and t - S['tn'] >= OFFS[S['k']]: unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['k'] += 1
        return S['k'] >= 3
    # step plan: 0 TP shot, 1 follow, 2 FP on, 3 FP shot, 4 follow, 5 ADS on, 6 ADS shot, 7 follow, 8 restore
    if st == 0 and t > 1.0: shot_start(); S['step'] = 1
    elif st == 1 and shot_follow(): S['step'] = 2; S['t2'] = t
    elif st == 2 and t - S['t2'] > 0.8: pc.get_editor_property('FurinaFPWanted').set_active(True); S['step'] = 3; S['t2'] = t
    elif st == 3 and t - S['t2'] > 1.5: shot_start(); S['step'] = 4
    elif st == 4 and shot_follow(): S['step'] = 5; S['t2'] = t
    elif st == 5 and t - S['t2'] > 0.8: ads().set_active(True); S['step'] = 6; S['t2'] = t
    elif st == 6 and t - S['t2'] > 1.5: shot_start(); S['step'] = 7
    elif st == 7 and shot_follow(): ads().set_active(False); pc.get_editor_property('FurinaFPWanted').set_active(False); S['step'] = 8; unreal.unregister_slate_post_tick_callback(S['h'])
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
