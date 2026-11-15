"""PIE: for <seconds> records every new BP_FurinaBullet and compares its launch direction with the ideal direction
muzzle -> (rear sight + sight line * 50 m) at the same frame (sight line = rear/front sight points of the M4 in rifle space, same values as
ue_fp_sight_aim.py). Data/ads_sight_probe.json: per shot yaw/pitch error in degrees + ADS flag + the sight-line pitch of that frame
(shows how much the recoil moves the sight while the bullet must follow it). usage: py ue_ads_sight_probe.py [seconds]"""
import unreal, sys, json, time, math
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\ads_sight_probe.json'
REAR = unreal.Vector(0.139, -11.757165, 9.957); FRONT = unreal.Vector(0.080865, 30.682121, 9.815); MUZ = unreal.Vector(0, 40.625201, 4.849452)
S = {'t0': time.time(), 'seen': set(), 'rows': [], 'n': 0}
def yp(d): return math.degrees(math.atan2(d.y, d.x)), math.degrees(math.asin(d.z / d.length()))
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    rifle = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaRifle'][0]
    T = rifle.get_world_transform()
    rear = T.transform_location(REAR); front = T.transform_location(FRONT); muz = T.transform_location(MUZ)
    d = front - rear; d = d / d.length()
    ads = bool(pc.get_components_by_tag(unreal.ActorComponent, 'FurinaADS')[0].is_active())
    cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    for b in unreal.GameplayStatics.get_all_actors_of_class(w, cls):
        n = b.get_name()
        if n in S['seen']: continue
        S['seen'].add(n)
        v = b.get_velocity()
        ideal = (rear + d * 5000) - muz
        iy, ip = yp(ideal); vy, vp = yp(v); sy, sp = yp(d)
        S['rows'].append(dict(ads=ads, yaw_err=round((vy - iy + 180) % 360 - 180, 3), pitch_err=round(vp - ip, 3), sight_pitch=round(sp, 2), sight_yaw=round(sy, 2), speed=round(v.length()), v=[round(v.x/v.length(),4),round(v.y/v.length(),4),round(v.z/v.length(),4)], ideal=[round(ideal.x/ideal.length(),4),round(ideal.y/ideal.length(),4),round(ideal.z/ideal.length(),4)], sight=[round(d.x,4),round(d.y,4),round(d.z,4)], p0_rel_muz=[round(x,1) for x in ((b.get_actor_location()-muz).to_tuple())]))
    del pc, rifle, w
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        json.dump(S['rows'], open(OUT, 'w'), indent=1); print('ADS_SIGHT_PROBE', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
