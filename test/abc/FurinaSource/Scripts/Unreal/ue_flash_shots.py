"""PIE: fires a shot (FurinaRifleShot) and takes a HighResShot in the same tick so the 45 ms muzzle flash is in the frame: first person hip (t 2 s), first person ADS (t 4.5 s), third person (t 7 s).
-> three newest Saved/Screenshots/WindowsEditor/HighresScreenshot*.png"""
import unreal, time
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
S = {'t0': time.time(), 'step': 0}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0); t = time.time() - S['t0']; st = S['step']
    def ads(): return pc.get_components_by_tag(unreal.ActorComponent, 'FurinaADS')[0]
    def shot(): pc.call_method('FurinaRifleShot'); unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2')
    if st == 0 and t > 0.5: pc.get_editor_property('FurinaFPWanted').set_active(True); S['step'] = 1
    elif st == 1 and t > 2.0: shot(); S['step'] = 2
    elif st == 2 and t > 3.0: ads().set_active(True); S['step'] = 3
    elif st == 3 and t > 4.5: shot(); S['step'] = 4
    elif st == 4 and t > 5.5: ads().set_active(False); pc.get_editor_property('FurinaFPWanted').set_active(False); S['step'] = 5
    elif st == 5 and t > 7.0: shot(); S['step'] = 6; unreal.unregister_slate_post_tick_callback(S['h'])
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
