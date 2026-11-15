"""PIE zero check: when the first new BP_FurinaBullet appears, stores the camera ray (line of sight); then logs the round's
height above / below that line against distance along it for <seconds> -> Data/fp_zero_probe.json. Start it, then fire one shot."""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_zero_probe.json'
S = {'t0': time.time(), 'rows': [], 'id': None}
def rifle_muzzle(w):
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    rifle = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaRifle'][0]
    m = rifle.get_world_transform().transform_location(unreal.Vector(0, 40.625201, 4.849452)); del pc, rifle
    return [round(m.x, 1), round(m.y, 1), round(m.z, 1)]
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    acts = unreal.GameplayStatics.get_all_actors_of_class(w, cls)
    if S['id'] is None and acts:
        # the shot's recoil already moved the camera this frame -> use the sight line of the previous frame
        b = acts[0]; S['id'] = b.get_name(); S['v0'] = [round(x,1) for x in b.get_velocity().to_tuple()]; S['p0'] = [round(x,1) for x in b.get_actor_location().to_tuple()]
        S['muz'] = rifle_muzzle(w)
        S['cam'], r, S['fov'] = S['prev']
        S['fwd'] = r.get_forward_vector(); S['up'] = r.get_up_vector(); S['right'] = r.get_right_vector()
    if S['id'] is None:
        cm = unreal.GameplayStatics.get_player_camera_manager(w, 0)
        S['prev'] = (cm.get_camera_location(), cm.get_camera_rotation(), cm.get_fov_angle()); del cm
    for a in acts:
        if a.get_name() != S['id']: continue
        d = a.get_actor_location() - S['cam']
        S['rows'].append([round(d.dot(S['fwd']) / 100, 2), round(d.dot(S['up']), 1), round(d.dot(S['right']), 1)])
    del acts, w
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        json.dump(dict(fov=S.get('fov'), v0=S.get('v0'), p0=S.get('p0'), muz=S.get('muz'), cam=[round(x,1) for x in S['cam'].to_tuple()] if 'cam' in S else None, fwd=[round(x,3) for x in S['fwd'].to_tuple()] if 'fwd' in S else None, rows=S['rows']), open(OUT, 'w')); print('ZERO_PROBE', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
