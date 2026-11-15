"""PIE: for <seconds> tracks every BP_M4MagDrop: MagBody world z, simulating?, linear velocity, collision profile -> Data/drop_probe.json. usage: py ue_drop_probe.py [seconds]"""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
S = {'t0': time.time(), 'rows': []}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    cls = unreal.load_class(None, '/Game/Furina/M4/BP_M4MagDrop.BP_M4MagDrop_C')
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, cls):
        b = [c for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == 'MagBody'][0]
        l = b.get_world_location(); v = b.get_physics_linear_velocity()
        S['rows'].append([round(time.time() - S['t0'], 2), a.get_name()[-4:], round(l.x), round(l.y), round(l.z, 1), round(v.z), bool(b.is_simulating_physics()), str(b.get_collision_profile_name())])
    del w
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h']); json.dump(S['rows'], open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\drop_probe.json', 'w')); print('DROP_PROBE', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
