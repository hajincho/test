"""PIE test of the BP_FurinaBullet ballistics and of the bullet look (2026-11-16), usage: py ue_bullet_ballistics_test.py
 A) spawns a bullet 1000 m up in the air (nothing to hit), flat along +X, logs (t, x, z, speed) every frame until x > 560 m -> drop at 500 m by interpolation, speed, time of flight; compares with the
    vacuum drop for the same muzzle speed (drag-caused extra drop, target 1.0 m at 500 m)  -> Data/bullet_ballistics_test.json
 B) spawns a frozen bullet (speed 0, no gravity, tracer hidden) 60 cm in front of the first-person camera and takes a HighResShot, so the bullet shape / size / material can be seen."""
import unreal, time, json, math
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bullet_ballistics_test.json'
S = {'t0': time.time(), 'phase': 0, 'rows': [], 'bullet': None, 'tp': 0}
def spawn(w, cls, loc, rot):
    xf = unreal.Transform(loc, rot, unreal.Vector(1, 1, 1)); GS = unreal.GameplayStatics
    names = [n for n in dir(GS) if 'spawn' in n.lower() and 'actor' in n.lower()]
    S['api'] = names
    begin = getattr(GS, 'begin_deferred_actor_spawn_from_class', None) or getattr(GS, 'begin_spawning_actor_from_class', None)
    a = begin(w, cls, xf)
    return GS.finish_spawning_actor(a, xf)
def tick(dt):
    try: _tick()
    except Exception:
        import traceback; json.dump({'error': traceback.format_exc(), 'api': S.get('api')}, open(OUT, 'w'), indent=1); unreal.unregister_slate_post_tick_callback(S['h'])
def _tick():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']; cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    if S['phase'] == 0 and t > 1.0:
        S['bullet'] = spawn(w, cls, unreal.Vector(0, 0, 100000), unreal.Rotator(0, 0, 0))
        S['tb'] = time.time(); S['phase'] = 1
    elif S['phase'] == 1:
        b = S['bullet']
        if b is None or not unreal.SystemLibrary.is_valid(b): S['phase'] = 2
        else:
            p = b.get_actor_location(); v = b.get_velocity(); S['rows'].append([round(time.time() - S['tb'], 4), p.x, p.z, v.length()])
            if p.x > 56000: S['phase'] = 2; b.destroy_actor()
    elif S['phase'] == 2:
        rows = S['rows']; res = {'frames': len(rows), 'first': rows[:3], 'last': rows[-2:]}
        for i in range(1, len(rows)):
            if rows[i][1] >= 50000 > rows[i - 1][1]:
                a, c = rows[i - 1], rows[i]; f = (50000 - a[1]) / (c[1] - a[1]); res['at_500m'] = dict(drop_m=round((a[2] + f * (c[2] - a[2]) - 100000) / 100, 3), speed_ms=round((a[3] + f * (c[3] - a[3])) / 100, 1), t_wall=round(a[0] + f * (c[0] - a[0]), 3)); break
        res['note'] = 'time and positions are per rendered frame; wall time includes frame time scaling of the sim (the projectile ticks with game delta time)'
        json.dump(res, open(OUT, 'w'), indent=1); print('BALLISTICS_TEST', res.get('at_500m')); S['phase'] = 3; S['t3'] = t
    elif S['phase'] == 3 and t > S['t3'] + 0.5:
        pc = unreal.GameplayStatics.get_player_character(w, 0); pc.get_editor_property('FurinaFPWanted').set_active(True); S['phase'] = 4; S['t4'] = t
    elif S['phase'] == 4 and t > S['t4'] + 1.0:
        pc = unreal.GameplayStatics.get_player_character(w, 0); cam = [c for c in pc.get_components_by_class(unreal.CameraComponent) if c.is_active()][0]
        loc = cam.get_world_location() + cam.get_forward_vector() * 70 + cam.get_right_vector() * 6 - cam.get_up_vector() * 3
        rot = cam.get_world_rotation(); rot.yaw += 60
        b = spawn(w, cls, loc, rot); pm = b.get_component_by_class(unreal.ProjectileMovementComponent); pm.set_editor_property('projectile_gravity_scale', 0.0); pm.set_velocity(unreal.Vector(0, 0, 0))
        for c in b.get_components_by_class(unreal.StaticMeshComponent):
            if c.static_mesh and c.static_mesh.get_name() == 'Cylinder': c.set_visibility(False)
        S['frozen'] = b; S['phase'] = 5; S['t5'] = t
    elif S['phase'] == 5 and t > S['t5'] + 0.4:
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2'); S['phase'] = 6; S['t6'] = t
    elif S['phase'] == 6 and t > S['t6'] + 0.6:
        S['frozen'].destroy_actor(); pc = unreal.GameplayStatics.get_player_character(w, 0); pc.get_editor_property('FurinaFPWanted').set_active(False); unreal.unregister_slate_post_tick_callback(S['h'])
    del w
S['h'] = unreal.register_slate_post_tick_callback(tick)
