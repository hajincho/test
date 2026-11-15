"""PIE: for <seconds> per frame: MagState curve, FurinaMag visibility / attach parent / distance to Left-wrist and to the seated pose (rifle origin),
BP_M4MagDrop count and the lowest dropped magazine z -> Data/mag_probe.json (summary of every state change)."""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\mag_probe.json'
S = {'t0': time.time(), 'rows': [], 'last': None}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    comps = {c.get_name(): c for c in pc.get_components_by_class(unreal.SceneComponent)}
    mesh, rifle, mag = comps['FurinaMesh'], comps['FurinaRifle'], comps['FurinaMag']
    anim = mesh.get_anim_instance(); cur = anim.get_curve_value('MagState') if anim else -1
    lw = mesh.get_socket_location('Left-wrist'); mp = mag.get_world_location(); rp = rifle.get_world_location()
    seated = rifle.get_world_transform().transform_location(unreal.Vector(0, 0, 0))
    cls = unreal.load_class(None, '/Game/Furina/M4/BP_M4MagDrop.BP_M4MagDrop_C')
    drops = unreal.GameplayStatics.get_all_actors_of_class(w, cls)
    par = mag.get_attach_parent()
    row = [round(time.time() - S['t0'], 2), round(cur, 2), bool(mag.is_visible()), par.get_name() if par else None, round((mp - lw).length(), 1), round((mp - seated).length(), 1), len(drops),
           round(min([a.get_actor_location().z for a in drops]), 1) if drops else None]
    key = (row[2], row[3], row[6])
    if key != S['last']: S['rows'].append(row); S['last'] = key
    del pc, comps, mesh, rifle, mag, w, drops
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h']); json.dump(S['rows'], open(OUT, 'w'), indent=1); print('MAG_PROBE', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
