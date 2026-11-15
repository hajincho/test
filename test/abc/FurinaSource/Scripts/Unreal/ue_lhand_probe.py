"""PIE: first-person left-hand stability. For <seconds> logs every frame the left wrist / left elbow in FPCamera space and the left wrist in rifle space, the rifle origin in camera space,
speed and the FP flag; mode idle | walk (add_movement_input forward) | fire (FurinaRifleShot every 0.075 s) | run. -> Data/lhand_probe_<mode>.json with per-axis std dev (cm) and max frame-to-frame step.
usage: py ue_lhand_probe.py <mode> [seconds]"""
import unreal, sys, json, time, math
MODE = sys.argv[1] if len(sys.argv) > 1 else 'idle'
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lhand_probe_%s.json' % MODE
S = {'t0': time.time(), 'rows': [], 'lastshot': 0}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0); t = time.time() - S['t0']
    if MODE in ('walk', 'run'):
        pc.add_movement_input(pc.get_actor_forward_vector(), 1.0)
    if MODE == 'fire' and t - S['lastshot'] > 0.075: S['lastshot'] = t; pc.call_method('FurinaRifleShot')
    comps = {c.get_name(): c for c in pc.get_components_by_class(unreal.SceneComponent)}
    m, r, cam = comps['FurinaMesh'], comps['FurinaRifle'], comps['FPCamera']; CT = cam.get_world_transform(); RT = r.get_world_transform()
    def C(v): return [round(x, 2) for x in unreal.MathLibrary.inverse_transform_location(CT, v).to_tuple()]
    S['rows'].append([round(t, 3), int(cam.is_active()), round(pc.get_velocity().length()), C(m.get_socket_location('Left-wrist')), C(m.get_socket_location('Left-elbow')),
                      C(RT.transform_location(unreal.Vector(0, 0, 0))), [round(x, 2) for x in RT.inverse_transform_location(m.get_socket_location('Left-wrist')).to_tuple()]])
    del pc, comps, m, r, cam, w
    if t > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        rows = S['rows']
        def stats(idx):
            out = {}
            for ax in range(3):
                v = [x[idx][ax] for x in rows]; mean = sum(v) / len(v)
                out['xyz'[ax]] = dict(mean=round(mean, 2), std=round(math.sqrt(sum((a - mean) ** 2 for a in v) / len(v)), 3), maxstep=round(max(abs(v[i] - v[i - 1]) for i in range(1, len(v))), 2))
            return out
        res = dict(mode=MODE, n=len(rows), fp=rows[0][1], speed_max=max(x[2] for x in rows), wrist_in_cam=stats(3), elbow_in_cam=stats(4), rifle_in_cam=stats(5), wrist_in_rifle=stats(6))
        json.dump(dict(summary=res, rows=rows), open(OUT, 'w')); print('LHAND', MODE, res['fp'], res['wrist_in_cam'])
S['h'] = unreal.register_slate_post_tick_callback(tick)
