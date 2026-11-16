"""PIE (2026-11-16): game time slowed to 4 % (console 'slomo 0.04') so that one rendered frame is ~0.6 m of bullet flight: first person, looks up PITCH deg, fires ONE shot and logs the BP_FurinaBullet per frame
(game time, position, speed). HighResShots at frames 10, 22 and 40 after the shot show the bullet shape and tracer. Result -> Data/bullet_slowmo.json: speed and drop (perpendicular distance below the launch
direction line) at 100/200/300/400/500 m, time of flight, effective drag k = -ln(v/v0)/x.  usage: py ue_bullet_slowmo.py [pitch_deg] [slomo]"""
import unreal, time, json, math, sys
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
PITCH = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0; SLO = sys.argv[2] if len(sys.argv) > 2 else '0.04'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bullet_slowmo.json'
S = {'t0': time.time(), 'phase': 0, 'rows': [], 'p0': None, 'n': 0}
def tick(dt):
    try: _tick()
    except Exception:
        import traceback; json.dump({'error': traceback.format_exc()}, open(OUT, 'w'), indent=1)
        try: unreal.SystemLibrary.execute_console_command(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'slomo 1')
        except Exception: pass
        unreal.unregister_slate_post_tick_callback(S['h'])
def _tick():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']; pc = unreal.GameplayStatics.get_player_character(w, 0)
    if S['phase'] == 0 and t > 0.5:
        pc.get_editor_property('FurinaFPWanted').set_active(True); ctl = unreal.GameplayStatics.get_player_controller(w, 0); r = ctl.get_control_rotation()
        ctl.set_control_rotation(unreal.Rotator(roll=0.0, pitch=PITCH, yaw=r.yaw)); S['phase'] = 1; S['t1'] = t
    elif S['phase'] == 1 and t > S['t1'] + 1.5:
        unreal.SystemLibrary.execute_console_command(w, 'slomo ' + SLO); S['phase'] = 2; S['t2'] = t
    elif S['phase'] == 2 and t > S['t2'] + 0.5:
        pc.call_method('FurinaRifleShot'); S['phase'] = 3; S['n'] = 0; S['tb'] = time.time()
    elif S['phase'] == 3:
        S['n'] += 1
        if S['n'] in (10, 22, 40): unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2')
        cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C'); acts = unreal.GameplayStatics.get_all_actors_of_class(w, cls)
        if acts:
            b = acts[0]; p = b.get_actor_location(); v = b.get_velocity(); gt = unreal.GameplayStatics.get_time_seconds(w)
            if S['p0'] is None: S['p0'] = p; S['v0'] = v; S['g0'] = gt
            S['rows'].append([gt - S['g0'], p.x - S['p0'].x, p.y - S['p0'].y, p.z - S['p0'].z, v.length()])
            if math.hypot(S['rows'][-1][1], S['rows'][-1][2]) > 62000: S['phase'] = 4
        elif S['rows']: S['phase'] = 4
        if time.time() - S['tb'] > 60: S['phase'] = 4
    elif S['phase'] == 4:
        unreal.SystemLibrary.execute_console_command(w, 'slomo 1')
        rows = S['rows']; res = {'frames': len(rows), 'pitch': PITCH, 'v_first_ms': round(rows[0][4] / 100, 1) if rows else None}
        if rows:
            v0 = S['v0']; d = unreal.Vector(v0.x, v0.y, v0.z); d = d / d.length(); res['dir'] = [round(d.x, 4), round(d.y, 4), round(d.z, 4)]
            for X in (50, 100, 200, 300, 400, 500):
                for i in range(1, len(rows)):
                    along = lambda r: (r[1] * d.x + r[2] * d.y + r[3] * d.z) / 100
                    if along(rows[i]) >= X > along(rows[i - 1]):
                        a, c = rows[i - 1], rows[i]; f = (X - along(a)) / (along(c) - along(a)); sp = (a[4] + f * (c[4] - a[4])) / 100
                        px, py, pz = (a[1] + f * (c[1] - a[1])) / 100, (a[2] + f * (c[2] - a[2])) / 100, (a[3] + f * (c[3] - a[3])) / 100
                        dot = px * d.x + py * d.y + pz * d.z; perp = (px - dot * d.x, py - dot * d.y, pz - dot * d.z)
                        res['at_%dm' % X] = dict(speed_ms=round(sp, 1), k_eff_per_m=round(-math.log(sp / 910.0) / X, 6), off_line_m=[round(x, 3) for x in perp], below_line_m=round(-perp[2] / max(1e-6, math.sqrt(1 - d.z * d.z)) , 3), game_t=round(a[0] + f * (c[0] - a[0]), 3)); break
        json.dump(res, open(OUT, 'w'), indent=1); print('SLOWMO', {k: v for k, v in res.items() if k.startswith('at_')})
        pc.get_editor_property('FurinaFPWanted').set_active(False); unreal.unregister_slate_post_tick_callback(S['h']); S['phase'] = 5
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
