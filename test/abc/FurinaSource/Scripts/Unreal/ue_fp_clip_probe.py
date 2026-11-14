"""PIE probe: how close does the rifle get to the first-person camera (near-plane clipping) over time?
Samples points along the rifle (local Y -26..48, Z -8..6) in camera space; reports the smallest forward depth among
points that are inside the view cone, plus Head / Neck positions and the movement mode. usage: py ue_fp_clip_probe.py <seconds>"""
import unreal, json, time, sys, math
S = {'t0': time.time(), 'rows': [], 'dur': float(sys.argv[1]) if len(sys.argv) > 1 else 8}
PTS = [unreal.Vector(x, y, z) for y in range(-26, 50, 4) for z in (-8, -3, 2, 6) for x in (-2, 2)]
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        comps = {c.get_name(): c for c in pawn.get_components_by_class(unreal.SceneComponent)}
        cam, rifle, mesh = comps['FPCamera'], comps['FurinaRifle'], comps['FurinaMesh']
        cx = cam.get_world_transform(); rx = rifle.get_world_transform(); mx = mesh.get_world_transform()
        best = (999, None)
        for p in PTS:
            c = cx.inverse_transform_location(rx.transform_location(p))      # camera space: X forward, Y right, Z up
            if c.x > -5 and abs(math.atan2(c.y, max(c.x, 0.01))) < math.radians(50) and abs(math.atan2(c.z, max(c.x, 0.01))) < math.radians(35):
                if c.x < best[0]: best = (round(c.x, 1), [round(p.y), round(p.z)])
        S['rows'].append({'t': round(time.time() - S['t0'], 2), 'fp': cam.is_active(),
                          'mode': str(pawn.character_movement.movement_mode).split('.')[-1][:12],
                          'min_depth': best[0], 'at': best[1],
                          'cam': [round(v, 1) for v in mx.inverse_transform_location(cx.translation).to_tuple()],
                          'head': [round(v, 1) for v in mx.inverse_transform_location(mesh.get_socket_location('Head')).to_tuple()],
                          'neck': [round(v, 1) for v in mx.inverse_transform_location(mesh.get_socket_location('Neck')).to_tuple()],
                          'rifle': [round(v, 1) for v in mx.inverse_transform_location(rx.translation).to_tuple()]})
    except Exception as e:
        S['rows'].append({'err': repr(e)[:200]})
    if time.time() - S['t0'] > S['dur']:
        unreal.unregister_slate_post_tick_callback(S['h'])
        json.dump(S['rows'], open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_clip.json', 'w'), indent=0)
S['h'] = unreal.register_slate_post_tick_callback(tick)
