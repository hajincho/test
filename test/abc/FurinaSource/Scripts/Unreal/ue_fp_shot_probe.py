"""PIE: at the first new BP_FurinaBullet, records bullet position/velocity/rotation, the camera of the previous frame (location, rotation, fov),
the rifle muzzle (rifle component * (0, 40.625, 4.849)) and the actor/control rotations -> Data/fp_shot_probe.json. Start it, then fire one shot."""
import unreal, sys, json, time
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_shot_probe.json'
S = {'t0': time.time(), 'prev': None, 'done': False}
def v3(v): return [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
def tick(dt):
    if S['done']: return
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    cm = unreal.GameplayStatics.get_player_camera_manager(w, 0)
    rifle = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaRifle'][0]
    cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    acts = unreal.GameplayStatics.get_all_actors_of_class(w, cls)
    cur = dict(cam=v3(cm.get_camera_location()), camrot=[round(cm.get_camera_rotation().pitch, 3), round(cm.get_camera_rotation().yaw, 3)], fov=cm.get_fov_angle(),
               muzzle=v3(rifle.get_world_transform().transform_location(unreal.Vector(0, 40.625201, 4.849452))),
               rifle=v3(rifle.get_world_location()), ctrl=[round(pc.get_control_rotation().pitch, 3), round(pc.get_control_rotation().yaw, 3)],
               ads=bool(pc.get_components_by_tag(unreal.ActorComponent, 'FurinaADS')[0].is_active()), sh=bool(pc.get_components_by_tag(unreal.ActorComponent, 'FurinaShoulder')[0].is_active()))
    if acts:
        b = acts[0]; v = b.get_velocity()
        S['res'] = dict(prev=S['prev'], now=cur, bullet=v3(b.get_actor_location()), vel=v3(v), speed=round(v.length()), n=len(acts),
                        names=[a.get_name() for a in acts][:4])
        json.dump(S['res'], open(OUT, 'w'), indent=1); S['done'] = True; print('SHOT_PROBE', S['res'])
        unreal.unregister_slate_post_tick_callback(S['h'])
    else: S['prev'] = cur
    del pc, cm, rifle, acts, w
S['h'] = unreal.register_slate_post_tick_callback(tick)
