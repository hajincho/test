"""PIE (2026-11-16): measures the random dispersion of a still, standing ADS shot. In ADS (tag FurinaADS), first person, standing still, it fires N shots 1.6 s apart (recoil settled). Right before each shot the ideal
launch direction is computed from the live rifle transform exactly like the BP does (muzzle -> rear aperture + sight line x 50 m, Colt calibration points) and right after FurinaRifleShot the new bullet's launch velocity
(spawn frame, before any drag) is compared with it. Result -> Data/spread_probe.json: per-shot yaw / pitch error (deg), mean (systematic: 50 m drop compensation), radius of the scatter about the mean, equivalent radius at 500 m.
usage: py ue_spread_probe.py [N] [mode]   mode: ads (default) | hip"""
import unreal, time, json, math, sys
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20; MODE = sys.argv[2] if len(sys.argv) > 2 else 'ads'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\spread_probe.json'
G = json.load(open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\colt_geometry.json'))
REAR = unreal.Vector(*G['rear_aperture']); FRONT = unreal.Vector(*G['front_post']); MUZ = unreal.Vector(*G['muzzle'])
S = {'t0': time.time(), 'phase': 0, 'rows': [], 'n': 0, 'last': -10}
def yp(d): return math.degrees(math.atan2(d.y, d.x)), math.degrees(math.asin(d.z / d.length()))
def tick(dt):
    try: _tick()
    except Exception:
        import traceback; json.dump({'error': traceback.format_exc()}, open(OUT, 'w'), indent=1); unreal.unregister_slate_post_tick_callback(S['h'])
def _tick():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']; pc = unreal.GameplayStatics.get_player_character(w, 0)
    def comp(tag): return pc.get_components_by_tag(unreal.ActorComponent, tag)[0]
    if S['phase'] == 0 and t > 0.5:
        pc.get_editor_property('FurinaFPWanted').set_active(True)
        if MODE == 'ads': comp('FurinaADS').set_active(True)
        S['phase'] = 1; S['t1'] = t
    elif S['phase'] == 1 and t > S['t1'] + 2.0 and t - S['last'] > 1.6:
        rifle = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaRifle'][0]
        T = rifle.get_world_transform(); rear = T.transform_location(REAR); front = T.transform_location(FRONT); muz = T.transform_location(MUZ)
        d = front - rear; d = d / d.length(); ideal = (rear + d * 5000) - muz
        cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C'); before = set(a.get_name() for a in unreal.GameplayStatics.get_all_actors_of_class(w, cls))
        pc.call_method('FurinaRifleShot'); S['last'] = t; S['n'] += 1
        for b in unreal.GameplayStatics.get_all_actors_of_class(w, cls):
            if b.get_name() in before: continue
            v = b.get_velocity(); iy, ip = yp(ideal); vy, vp = yp(v); S['rows'].append(dict(yaw_err=round((vy - iy + 180) % 360 - 180, 4) * math.cos(math.radians(ip)), pitch_err=round(vp - ip, 4), speed=round(v.length() / 100, 1)))
        del rifle
        if S['n'] >= N: S['phase'] = 2; S['t2'] = t
    elif S['phase'] == 2 and t > S['t2'] + 1.0:
        rows = S['rows']; n = len(rows); res = {'mode': MODE, 'shots': S['n'], 'bullets': n}
        if n:
            my = sum(r['yaw_err'] for r in rows) / n; mp = sum(r['pitch_err'] for r in rows) / n; rad = [math.hypot(r['yaw_err'] - my, r['pitch_err'] - mp) for r in rows]
            res.update(mean_offset_deg=[round(my, 4), round(mp, 4)], scatter_mean_radius_deg=round(sum(rad) / n, 4), scatter_max_radius_deg=round(max(rad), 4),
                       max_radius_at_500m_m=round(math.tan(math.radians(max(rad))) * 500, 3), mean_radius_at_500m_m=round(math.tan(math.radians(sum(rad) / n)) * 500, 3), speeds=[r['speed'] for r in rows][:5])
        res['rows'] = rows; json.dump(res, open(OUT, 'w'), indent=1); print('SPREAD_PROBE', {k: v for k, v in res.items() if k != 'rows'})
        if MODE == 'ads': comp('FurinaADS').set_active(False)
        pc.get_editor_property('FurinaFPWanted').set_active(False); unreal.unregister_slate_post_tick_callback(S['h']); S['phase'] = 3
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
