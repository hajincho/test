"""PIE probe: for <seconds> logs every BP_FurinaBullet (id, position, speed, tracer hidden) each frame -> Data/fp_bullet_probe.json.
Start it, then fire. usage: py ue_fp_bullet_probe.py [seconds]"""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_bullet_probe.json'
state = {'t0': time.time(), 'tracks': {}, 'frames': 0, 'max_alive': 0}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    acts = unreal.GameplayStatics.get_all_actors_of_class(w, cls)
    if state['frames'] == 0:
        pc = unreal.GameplayStatics.get_player_character(w, 0); state['player'] = [round(pc.get_actor_location().x), round(pc.get_actor_location().y), round(pc.get_actor_location().z), round(pc.get_control_rotation().yaw)]; del pc
    state['frames'] += 1; state['max_alive'] = max(state['max_alive'], len(acts))
    now = round(time.time() - state['t0'], 3)
    for a in acts:
        tr = state['tracks'].setdefault(a.get_name(), [])
        p = a.get_actor_location(); v = a.get_velocity()
        tracer = a.get_components_by_class(unreal.StaticMeshComponent)
        hid = [round(x, 3) for x in tracer[0].get_editor_property('relative_scale3d').to_tuple()] + [round(tracer[0].get_editor_property('relative_location').x), tracer[0].is_visible(), tracer[0].get_editor_property('hidden_in_game'), str(tracer[0].get_material(0).get_name()) if tracer[0].get_material(0) else None] if tracer else None
        tr.append([now, round(p.x), round(p.y), round(p.z), round(v.length()), hid, round(v.x), round(v.y), round(v.z)])
    del acts, w
    if time.time() - state['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(state['h'])
        tracks = state['tracks']
        summ = {}
        for k, tr in tracks.items():
            if len(tr) < 2: summ[k] = dict(n=len(tr)); continue
            a, b = tr[0], tr[-1]
            dist = ((b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2) ** 0.5
            summ[k] = dict(n=len(tr), t=round(b[0] - a[0], 3), horiz_m=round(dist / 100, 1), dz_cm=b[3] - a[3], v0=a[4], v1=b[4], hidden_first=a[5], hidden_last=b[5])
        json.dump(dict(player=state.get('player'), frames=state['frames'], max_alive=state['max_alive'], bullets=len(tracks), summary=summ, tracks=tracks), open(OUT, 'w'), indent=1)
        print('FP_BULLET_PROBE', state['frames'], len(tracks), state['max_alive'])
state['h'] = unreal.register_slate_post_tick_callback(tick)
