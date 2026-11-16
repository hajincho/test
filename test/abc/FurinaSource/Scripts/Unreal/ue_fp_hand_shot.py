"""PIE: first person (FurinaFPWanted), waits 1.5 s, takes HighResShots of the hip pose (1) and after raising to the shoulder pose (FurinaShoulder, 1.5 s later) (2) -> newest HighresScreenshot*.png. usage: py ue_fp_hand_shot.py"""
import unreal, time
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
S = {'t0': time.time(), 'phase': 0}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']; pc = unreal.GameplayStatics.get_player_character(w, 0); ph = S['phase']
    if ph == 0 and t > 0.5: pc.get_editor_property('FurinaFPWanted').set_active(True); S['phase'] = 1
    elif ph == 1 and t > 2.5: unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['phase'] = 2
    elif ph == 2 and t > 3.5: [c.set_active(True) for c in pc.get_components_by_tag(unreal.ActorComponent, 'FurinaShoulder')]; S['phase'] = 3
    elif ph == 3 and t > 5.0: unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['phase'] = 4
    elif ph == 4 and t > 6.0:
        [c.set_active(False) for c in pc.get_components_by_tag(unreal.ActorComponent, 'FurinaShoulder')]; pc.get_editor_property('FurinaFPWanted').set_active(False); unreal.unregister_slate_post_tick_callback(S['h']); S['phase'] = 5
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
