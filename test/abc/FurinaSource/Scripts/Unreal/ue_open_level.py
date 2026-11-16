"""Editor: saves the current level, opens the level given in argv[1] (default /Game/UndergroundTunnel/Maps/Demonstration) and probes it (ue_level_probe.py output tag 'opened') -> Data/open_level.json.
usage: py ue_open_level.py [/Game/Path/Map]"""
import unreal, json, sys, traceback
PATH = sys.argv[1] if len(sys.argv) > 1 else '/Game/UndergroundTunnel/Maps/Demonstration'
R = {}
try:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    R['saved_current'] = les.save_current_level()
    R['loaded'] = les.load_level(PATH)
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); R['world'] = w.get_path_name() if w else None
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors(); cnt = {}; notable = []
    for a in acts:
        c = a.get_class().get_name(); cnt[c] = cnt.get(c, 0) + 1
        if c in ('PlayerStart', 'PostProcessVolume', 'DirectionalLight', 'SkyLight', 'ExponentialHeightFog', 'SkyAtmosphere', 'NavMeshBoundsVolume') or 'Character' in c or 'GameMode' in c or 'Pawn' in c:
            l = a.get_actor_location(); notable.append([c, a.get_actor_label(), [round(l.x), round(l.y), round(l.z)], round(a.get_actor_rotation().yaw)])
    R['actor_count'] = len(acts); R['classes'] = dict(sorted(cnt.items(), key=lambda kv: -kv[1])[:30]); R['notable'] = notable[:40]
    try:
        ws = w.get_world_settings(); R['game_mode_override'] = str(ws.get_editor_property('default_game_mode'))
    except Exception as e: R['ws_err'] = str(e)[:150]
    mn = [1e12] * 3; mx = [-1e12] * 3
    for a in acts:
        if isinstance(a, unreal.StaticMeshActor):
            o, e = a.get_actor_bounds(False)
            for i, (p, q) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))): mn[i] = min(mn[i], p - q); mx[i] = max(mx[i], p + q)
    R['static_mesh_bounds'] = [[round(x) for x in mn], [round(x) for x in mx]]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\open_level.json', 'w'), indent=1); print('OPEN_LEVEL', R.get('world'), R.get('error', '')[-200:])
