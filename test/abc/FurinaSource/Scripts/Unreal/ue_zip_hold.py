"""PIE: holds the pawn on the Sphere (pulley trigger) of a Zipline_BP for <seconds> (zero velocity every frame) so the overlap stays true while the Jump key is pressed.
usage: py ue_zip_hold.py [seconds] [actor name prefix]"""
import unreal, sys, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0; NAME = sys.argv[2] if len(sys.argv) > 2 else 'Zipline_BP_2'
S = {'t0': time.time()}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    z = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if a.get_name().startswith(NAME)][0]
    sphere = [c for c in z.get_components_by_class(unreal.SceneComponent) if c.get_name() == 'Sphere'][0]
    if time.time() - S['t0'] < DUR:
        pawn.set_actor_location(sphere.get_world_location(), False, False); pawn.character_movement.velocity = unreal.Vector(0, 0, 0)
    else: unreal.unregister_slate_post_tick_callback(S['h']); print('ZIP_HOLD done')
    del w, pawn, z, sphere
S['h'] = unreal.register_slate_post_tick_callback(tick)
