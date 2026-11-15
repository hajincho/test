"""PIE: for <seconds> records every new BP_FurinaBullet: first position / velocity, the camera of the previous frame (location, rotation, fov),
the rifle muzzle now, ADS / shoulder flags. Then Data/fp_shots_probe.json gets the direction error of every shot vs the ideal
(muzzle -> camera-ray point at <zero m>, default 50) in degrees. usage: py ue_fp_shots_probe.py [seconds] [zero_m]"""
import unreal, sys, json, time, math
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
ZERO = float(sys.argv[2]) if len(sys.argv) > 2 else 50.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_shots_probe.json'
S = {'t0': time.time(), 'prev': None, 'seen': set(), 'rows': []}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    cm = unreal.GameplayStatics.get_player_camera_manager(w, 0)
    rifle = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaRifle'][0]
    cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    cur = dict(cam=cm.get_camera_location(), rot=cm.get_camera_rotation(), fov=cm.get_fov_angle(),
               muz=rifle.get_world_transform().transform_location(unreal.Vector(0, 40.625201, 4.849452)),
               ads=bool(pc.get_components_by_tag(unreal.ActorComponent, 'FurinaADS')[0].is_active()), sh=bool(pc.get_components_by_tag(unreal.ActorComponent, 'FurinaShoulder')[0].is_active()))
    for b in unreal.GameplayStatics.get_all_actors_of_class(w, cls):
        n = b.get_name()
        if n in S['seen']: continue
        S['seen'].add(n)
        if S['prev'] is None: continue
        pr = S['prev']; v = b.get_velocity(); p = b.get_actor_location()
        S['rows'].append(dict(p0=p, v0=v, prev=pr, muz=cur['muz'], ads=cur['ads'], sh=cur['sh']))
    S['prev'] = cur
    del pc, cm, rifle, w
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        out = []
        for r in S['rows']:
            pr = r['prev']; f = pr['rot'].get_forward_vector(); aim = pr['cam'] + f * (ZERO * 100)
            ideal = (aim - r['muz']); ideal = ideal / ideal.length(); v = r['v0']; vd = v / v.length()
            def yp(d): return math.degrees(math.atan2(d.y, d.x)), math.degrees(math.asin(d.z))
            iy, ip = yp(ideal); vy, vp = yp(vd)
            dy = (vy - iy + 180) % 360 - 180
            out.append(dict(speed=round(v.length()), yaw_err=round(dy, 3), pitch_err=round(vp - ip, 3), ads=r['ads'], sh=r['sh'], fov=round(pr['fov'], 1),
                            muz_back_m=round((r['muz'] - pr['cam']).dot(f) / 100, 2), muz_right_cm=round((r['muz'] - pr['cam']).dot(pr['rot'].get_right_vector()), 1),
                            muz_up_cm=round((r['muz'] - pr['cam']).dot(pr['rot'].get_up_vector()), 1)))
        json.dump(out, open(OUT, 'w'), indent=1); print('SHOTS_PROBE', len(out))
S['h'] = unreal.register_slate_post_tick_callback(tick)
