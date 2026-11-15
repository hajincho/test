"""PIE: for <seconds> logs lateral foot positions (character right axis, cm) relative to the pelvis centre, hip width and the foot gap,
plus speed -> Data/leg_probe.json. usage: py ue_leg_probe.py [seconds]"""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\leg_probe.json'
S = {'t0': time.time(), 'rows': []}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    m = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name().startswith('FurinaMesh')][0]
    right = pc.get_actor_right_vector(); fwd = pc.get_actor_forward_vector()
    def p(b): return m.get_socket_location(b)
    hips = p('Hips'); la, ra = p('Left-ankle'), p('Right-ankle'); ll, rl = p('Left-leg'), p('Right-leg')
    def lat(v, o): d = v - o; return round(d.dot(right), 1)
    S['rows'].append([round(time.time() - S['t0'], 3), round(pc.get_velocity().length()), lat(la, hips), lat(ra, hips), lat(ll, hips), lat(rl, hips),
                      round((la - ra).dot(fwd), 1), round((la - ra).dot(right), 1)])
    del pc, m, w
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        json.dump(S['rows'], open(OUT, 'w')); print('LEG_PROBE', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
