"""PIE probe: binds OnComponentHit on every new BP_FurinaBullet and logs what it hits (actor, component, location, time,
instigator) for <seconds> -> Data/fp_bullet_hitprobe.json. Start it, then fire."""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_bullet_hitprobe.json'
H = {'t0': time.time(), 'seen': set(), 'hits': [], 'spawns': []}
def on_hit(hit_comp, other_actor, other_comp, normal_impulse, hit):
    H['hits'].append(dict(t=round(time.time() - H['t0'], 3), bullet=hit_comp.get_owner().get_name(),
                          other=other_actor.get_name() if other_actor else None, comp=other_comp.get_name() if other_comp else None,
                          at=str(hit.to_tuple()[4]) if hasattr(hit, 'to_tuple') else None))
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, cls):
        n = a.get_name()
        if n in H['seen']: continue
        H['seen'].add(n)
        sph = a.get_components_by_class(unreal.SphereComponent)[0]
        loc = a.get_actor_location(); v = a.get_velocity()
        end = loc + v * 0.02
        hit = unreal.SystemLibrary.sphere_trace_single(w, loc, end, 1.5, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [a], unreal.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        H['hits'].append(dict(n=n, blocking=t[0] if t else None, initial_overlap=t[1] if t else None, dist=t[3] if t else None,
                              actor=t[9].get_name() if t and t[9] else None, comp=t[10].get_name() if t and t[10] else None))
        ins = a.get_instigator(); own = a.get_owner()
        H['spawns'].append(dict(n=n, instigator=ins.get_name() if ins else None, owner=own.get_name() if own else None,
                                profile=str(sph.get_collision_profile_name()), loc=str(a.get_actor_location())))
    if time.time() - H['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(H['h'])
        json.dump(dict(spawns=H['spawns'], hits=H['hits']), open(OUT, 'w'), indent=1, default=str); print('HITPROBE done', len(H['spawns']), len(H['hits']))
H['h'] = unreal.register_slate_post_tick_callback(tick)
