"""PIE helper: teleport the player pawn. usage: py ue_tp_player.py x y z [yaw]   |  py ue_tp_player.py zip <actor name>   (near that actor)
Writes Data/tp_player.json with the pawn location and the special-move flags."""
import unreal, sys, json
def main():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0); R = {}
    if sys.argv[1] == 'zip':
        for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
            if a.get_name().startswith(sys.argv[2]):
                l = a.get_actor_location(); R['actor'] = [a.get_name(), [l.x, l.y, l.z]]
                R['comps'] = {c.get_name(): [round(c.get_world_location().x), round(c.get_world_location().y), round(c.get_world_location().z)] for c in a.get_components_by_class(unreal.SceneComponent)}
                break
    else:
        x, y, z = (float(v) for v in sys.argv[1:4]); pawn.set_actor_location(unreal.Vector(x, y, z), False, False)
        if len(sys.argv) > 4: pawn.set_actor_rotation(unreal.Rotator(0, 0, float(sys.argv[4])), False)
    l = pawn.get_actor_location(); R['pawn'] = [round(l.x), round(l.y), round(l.z)]
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\tp_player.json', 'w'), indent=1); print('TP_PLAYER', R)
    del w, pawn
main(); del main
