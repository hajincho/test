"""PIE: requests a reload (FurinaRequestReload) and takes a HighResShot 1.0 s later (reload runs 3 s) so the HUD reload animation can be seen. -> Saved/Screenshots/WindowsEditor/HighresScreenshot*.png"""
import unreal, time
S = {'t0': time.time(), 'req': False, 'shot': False}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']
    if not S['req']:
        S['req'] = True; unreal.GameplayStatics.get_player_character(w, 0).call_method('FurinaRequestReload')
    if t > 1.0 and not S['shot']:
        S['shot'] = True; unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2')
    if t > 1.5:
        unreal.unregister_slate_post_tick_callback(S['h'])
    del w
S['h'] = unreal.register_slate_post_tick_callback(tick)
