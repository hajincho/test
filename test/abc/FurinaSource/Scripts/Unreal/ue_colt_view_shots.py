"""PIE: takes HighResShot screenshots of the Colt rifle in third person (t=0.5 s), first person (t=2.5 s) and ADS (t=4.5 s) by toggling the view components
(FurinaFPWanted, tag FurinaADS), then restores them. -> Saved/Screenshots/WindowsEditor/HighresScreenshot*.png (the three newest files, in this order)"""
import unreal, time
S = {'t0': time.time(), 'step': 0}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0); t = time.time() - S['t0']; st = S['step']
    def ads(): return pc.get_components_by_tag(unreal.ActorComponent, 'FurinaADS')[0]
    if st == 0 and t > 0.5: unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['step'] = 1
    elif st == 1 and t > 1.2: pc.get_editor_property('FurinaFPWanted').set_active(True); S['step'] = 2
    elif st == 2 and t > 2.8: unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['step'] = 3
    elif st == 3 and t > 3.4: ads().set_active(True); S['step'] = 4
    elif st == 4 and t > 5.0: unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['step'] = 5
    elif st == 5 and t > 5.6: ads().set_active(False); pc.get_editor_property('FurinaFPWanted').set_active(False); S['step'] = 6; unreal.unregister_slate_post_tick_callback(S['h'])
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
