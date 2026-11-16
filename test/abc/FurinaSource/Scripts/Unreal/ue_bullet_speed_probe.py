"""PIE (2026-11-16): looks 2.5 deg up (so the bullet stays in the air), switches to first person, fires ONE shot (FurinaRifleShot) and logs the BP_FurinaBullet every frame (time, distance travelled from the first
sample, speed, height). Takes a HighResShot on the shot frame and on the next two frames (the bullet shape and its tracer are visible for a moment).
Result -> Data/bullet_speed_probe.json: speed at 100/200/300/400/500 m (interpolated), effective drag k = -ln(v/v0)/x (set value 1.38e-3 per m) -- spread randomises the direction but not the speed.
usage: py ue_bullet_speed_probe.py"""
import unreal, time, json, math
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bullet_speed_probe.json'
S = {'t0': time.time(), 'phase': 0, 'rows': [], 'p0': None, 'shots': 0, 'nframe': 0}
def tick(dt):
    try: _tick()
    except Exception:
        import traceback; json.dump({'error': traceback.format_exc()}, open(OUT, 'w'), indent=1); unreal.unregister_slate_post_tick_callback(S['h'])
def _tick():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']; pc = unreal.GameplayStatics.get_player_character(w, 0)
    if S['phase'] == 0 and t > 0.5:
        pc.get_editor_property('FurinaFPWanted').set_active(True); ctl = pc.get_controller(); r = ctl.get_control_rotation(); r.pitch = 2.5; ctl.set_control_rotation(r); S['phase'] = 1; S['t1'] = t
    elif S['phase'] == 1 and t > S['t1'] + 1.5:
        pc.call_method('FurinaRifleShot'); unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['phase'] = 2; S['tb'] = time.time(); S['nframe'] = 0
    elif S['phase'] == 2:
        S['nframe'] += 1
        if S['nframe'] in (2, 3): unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2')
        cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C'); acts = unreal.GameplayStatics.get_all_actors_of_class(w, cls)
        if acts:
            b = acts[0]; p = b.get_actor_location(); v = b.get_velocity()
            if S['p0'] is None: S['p0'] = p
            S['rows'].append([round(time.time() - S['tb'], 4), math.dist((p.x, p.y, p.z), (S['p0'].x, S['p0'].y, S['p0'].z)) / 100, v.length() / 100, p.z / 100])
        elif S['rows']: S['phase'] = 3
        if time.time() - S['tb'] > 3.5: S['phase'] = 3
    elif S['phase'] == 3:
        rows = S['rows']; res = {'frames': len(rows), 'first': rows[:2], 'last': rows[-2:]}
        if rows:
            v0 = rows[0][2] if rows[0][1] < 1 else 910.0; res['v0_first_sample'] = rows[0][2]
            for X in (100, 200, 300, 400, 500):
                for i in range(1, len(rows)):
                    if rows[i][1] >= X > rows[i - 1][1]:
                        a, c = rows[i - 1], rows[i]; f = (X - a[1]) / (c[1] - a[1]); sp = a[2] + f * (c[2] - a[2]); res['at_%dm' % X] = dict(speed_ms=round(sp, 1), k_eff_per_m=round(-math.log(sp / 910.0) / (X + 0.0), 6)); break
        json.dump(res, open(OUT, 'w'), indent=1); print('SPEED_PROBE', {k: v for k, v in res.items() if k.startswith('at_')}); S['phase'] = 4
        pc.get_editor_property('FurinaFPWanted').set_active(False); unreal.unregister_slate_post_tick_callback(S['h'])
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
