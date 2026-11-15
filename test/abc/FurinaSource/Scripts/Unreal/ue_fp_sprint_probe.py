"""PIE: per frame for <seconds>: speed, rifle grip and muzzle in camera space (fwd, right, up cm) -> Data/fp_sprint_probe.json"""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_sprint_probe.json'
S = {'t0': time.time(), 'rows': []}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    cm = unreal.GameplayStatics.get_player_camera_manager(w, 0)
    cl = cm.get_camera_location(); r = cm.get_camera_rotation()
    f, rt, up = r.get_forward_vector(), r.get_right_vector(), r.get_up_vector()
    rifle = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaRifle'][0]
    xf = rifle.get_world_transform()
    def cs(p): d = p - cl; return [round(d.dot(f), 1), round(d.dot(rt), 1), round(d.dot(up), 1)]
    S['rows'].append([round(time.time() - S['t0'], 3), round(pc.get_velocity().length()), cs(xf.translation), cs(xf.transform_location(unreal.Vector(0, 48.5, 3.1)))])
    del pc, cm, rifle, w
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        json.dump(S['rows'], open(OUT, 'w')); print('SPRINT_PROBE', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
