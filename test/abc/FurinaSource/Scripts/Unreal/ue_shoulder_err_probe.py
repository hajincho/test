"""PIE: fires <n> shots (FurinaRifleShot every 0.12 s) in the stance given by <mode> (shoulder | hip | ads: sets / clears the FurinaShoulder and FurinaADS flag components) and for each
bullet reports the angle between its launch direction and the camera forward read just before the shot (crosshair direction; 0.04 deg muzzle parallax at 100 m is ignored; the
100 m zero lift is 0.0746 deg up). -> Data/shoulder_err_probe_<mode>.json: per shot (dyaw, dpitch, radius deg, tan(radius) %), summary mean / max.
Look at open ground (pitch 0) first. usage: py ue_shoulder_err_probe.py <mode> [n]"""
import unreal, sys, json, time, math
MODE = sys.argv[1] if len(sys.argv) > 1 else 'shoulder'
N = int(sys.argv[2]) if len(sys.argv) > 2 else 25
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\shoulder_err_probe_%s.json' % MODE
S = {'t0': time.time(), 'seen': set(), 'rows': [], 'fired': 0, 'last': -1, 'fwd': None, 'setup': False}
def yp(d): return math.degrees(math.atan2(d.y, d.x)), math.degrees(math.asin(max(-1, min(1, d.z / d.length()))))
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0); t = time.time() - S['t0']
    if not S['setup']:
        S['setup'] = True
        for tag, on in (('FurinaShoulder', MODE == 'shoulder'), ('FurinaADS', MODE == 'ads')):
            for c in pc.get_components_by_tag(unreal.ActorComponent, tag): c.set_active(on, False)
        try: pc.set_editor_property('FurinaAmmo', 30)
        except Exception: pass
    cam = [c for c in pc.get_components_by_class(unreal.CameraComponent) if c.is_active()][0]
    # new bullets first (they belong to the previous shot)
    cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    for b in unreal.GameplayStatics.get_all_actors_of_class(w, cls):
        n = b.get_name()
        if n in S['seen'] or S['fwd'] is None: continue
        S['seen'].add(n); v = b.get_velocity(); fy, fp = yp(S['fwd']); vy, vp = yp(v)
        dy = (vy - fy + 180) % 360 - 180; dp = vp - fp; cp = math.cos(math.radians(fp))
        r = math.degrees(math.acos(max(-1, min(1, v.normal().dot(S['fwd'].normal())))))
        S['rows'].append(dict(dyaw=round(dy * cp, 3), dpitch=round(dp, 3), radius_deg=round(r, 3), tan_pct=round(100 * math.tan(math.radians(r)), 2)))
    if t - S['last'] > 0.12 and S['fired'] < N:
        S['last'] = t; S['fired'] += 1; S['fwd'] = cam.get_forward_vector(); pc.call_method('FurinaRifleShot')
    del pc, cam, w
    if S['fired'] >= N and t - S['last'] > 0.6:
        unreal.unregister_slate_post_tick_callback(S['h'])
        rs = [r['radius_deg'] for r in S['rows']]; tp = [r['tan_pct'] for r in S['rows']]
        summ = dict(mode=MODE, shots=S['fired'], bullets=len(rs), mean_deg=round(sum(rs) / max(1, len(rs)), 3), max_deg=max(rs or [0]), mean_tan_pct=round(sum(tp) / max(1, len(tp)), 2), max_tan_pct=max(tp or [0]))
        json.dump(dict(summary=summ, rows=S['rows']), open(OUT, 'w'), indent=1); print('SHOULDER_ERR', summ)
S['h'] = unreal.register_slate_post_tick_callback(tick)
