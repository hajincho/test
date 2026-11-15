"""PIE: for <seconds> logs per frame the character speed, Furina's ankle forward offsets (relative to the hips, character forward axis) and the
hidden Manny mesh ankles ('foot_l','foot_r' - its animation drives the original footstep sounds) -> Data/step_probe.json, plus a summary of the
step rate (foot forward-offset zero crossings per second) for both. usage: py ue_step_probe.py [seconds]"""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\step_probe.json'
S = {'t0': time.time(), 'rows': []}
def cross(rows, i, t0=1.0):
    """rate of rising zero crossings of (left - right) column i -> full cycles per second (one cycle = 2 steps)"""
    prev = None; n = 0; first = last = None
    for r in rows:
        if r[0] < t0 or r[1] < 300: continue
        v = r[i]
        if prev is not None and prev < 0 <= v:
            n += 1; first = r[0] if first is None else first; last = r[0]
        prev = v
    return (n - 1) / (last - first) if n > 2 and last > first else None
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    meshes = {c.get_name(): c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent)}
    fm = [c for n, c in meshes.items() if n.startswith('FurinaMesh')][0]
    mm = meshes.get('CharacterMesh0')
    fwd = pc.get_actor_forward_vector()
    def d(m, a, b): return round((m.get_socket_location(a) - m.get_socket_location(b)).dot(fwd), 1)
    row = [round(time.time() - S['t0'], 3), round(pc.get_velocity().length()), d(fm, 'Left-ankle', 'Right-ankle')]
    row.append(d(mm, 'foot_l', 'foot_r') if mm else None)
    S['rows'].append(row)
    del pc, fm, mm, meshes, w
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        out = dict(furina_cycles_per_s=cross(S['rows'], 2), manny_cycles_per_s=cross([r for r in S['rows'] if r[3] is not None], 3), rows=S['rows'])
        json.dump(out, open(OUT, 'w')); print('STEP_PROBE', out['furina_cycles_per_s'], out['manny_cycles_per_s'])
S['h'] = unreal.register_slate_post_tick_callback(tick)
