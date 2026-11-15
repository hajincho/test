"""PIE: describe an actor by name (location, bounds, primitive components' collision) + the player position -> Data/probe_actor.json"""
import unreal, sys, json
def main():
    name = sys.argv[1]
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    R = {}
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0); R['player'] = str(pawn.get_actor_location())
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if a.get_name() != name: continue
        o, e = a.get_actor_bounds(False)
        R['actor'] = dict(cls=a.get_class().get_name(), loc=str(a.get_actor_location()), origin=str(o), extent=str(e), label=a.get_actor_label() if hasattr(a, 'get_actor_label') else None)
        R['comps'] = []
        for c in a.get_components_by_class(unreal.PrimitiveComponent)[:12]:
            R['comps'].append(dict(n=c.get_name(), cls=c.get_class().get_name(), profile=str(c.get_collision_profile_name()),
                                   enabled=str(c.get_collision_enabled()), obj=str(c.get_collision_object_type()),
                                   mesh=str(c.get_editor_property('static_mesh').get_name()) if hasattr(c, 'static_mesh') or isinstance(c, unreal.StaticMeshComponent) else None,
                                   visible=c.is_visible()))
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\probe_actor.json', 'w'), indent=1, default=str)
    print('PROBE_ACTOR', R.get('actor'))
main(); del main
