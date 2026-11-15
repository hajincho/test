"""PIE: starts a zipline ride by script: teleports the pawn to the pulley of <actor> (default Zipline_BP_2), sets Platformer component's Zipline Actor and calls its UseZipline event.
-> Data/zip_use.json"""
import unreal, sys, json
def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'Zipline_BP_2'
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0); R = {}
    z = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if a.get_name().startswith(name)][0]
    pc = [c for c in pawn.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name().startswith('Platformer_Component')][0]
    R['comp'] = pc.get_name(); R['props'] = [p for p in dir(pc) if not p.startswith('_') and ('zip' in p.lower() or 'pulley' in p.lower() or 'overlap' in p.lower())]
    sphere = [c for c in z.get_components_by_class(unreal.SceneComponent) if c.get_name() == 'Sphere'][0]; l = sphere.get_world_location()
    pawn.set_actor_location(unreal.Vector(l.x, l.y, l.z), False, False)
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\zip_use.json', 'w'), indent=1)
    pc.set_editor_property('Zipline Actor', z)
    try: R['call'] = str(pc.call_method('UseZipline'))
    except Exception as e: R['call'] = 'ERR ' + str(e)[:200]
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\zip_use.json', 'w'), indent=1); print('ZIP_USE', R)
    del w, pawn, z, pc, sphere
main(); del main
