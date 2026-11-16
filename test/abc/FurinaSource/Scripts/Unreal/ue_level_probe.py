"""Editor: describes the CURRENT level: path, world-settings game mode / default pawn / HUD override, counts of actor classes, PlayerStart / pawn actors (location), lights, post process volumes, bounds of all
static meshes -> Data/level_probe.json. usage: py ue_level_probe.py [tag]   (tag is part of the output file name)"""
import unreal, json, sys
tag = sys.argv[1] if len(sys.argv) > 1 else 'cur'
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); R = {'world': w.get_path_name()}
try:
    ws = w.get_world_settings(); R['world_settings'] = {k: str(ws.get_editor_property(k)) for k in ('default_game_mode',) if ws.has_editor_property(k)} if hasattr(ws, 'has_editor_property') else {}
    gm = ws.get_editor_property('default_game_mode'); R['game_mode_override'] = str(gm)
except Exception as e: R['ws_err'] = str(e)[:150]
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors(); cnt = {}; keep = []
mn = [1e12] * 3; mx = [-1e12] * 3
for a in acts:
    c = a.get_class().get_name(); cnt[c] = cnt.get(c, 0) + 1
    if c in ('PlayerStart', 'ThirdPersonCharacter_BP_C', 'PostProcessVolume', 'DirectionalLight', 'SkyLight', 'ExponentialHeightFog', 'SkyAtmosphere', 'NavMeshBoundsVolume', 'LightmassImportanceVolume') or 'Character' in c or 'GameMode' in c:
        l = a.get_actor_location(); keep.append([c, a.get_actor_label(), [round(l.x), round(l.y), round(l.z)], a.get_actor_rotation().yaw])
    if isinstance(a, unreal.StaticMeshActor):
        o, e = a.get_actor_bounds(False)
        for i, (p, q) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))): mn[i] = min(mn[i], p - q); mx[i] = max(mx[i], p + q)
R['actor_count'] = len(acts); R['classes'] = dict(sorted(cnt.items(), key=lambda kv: -kv[1])[:30]); R['notable'] = keep[:40]; R['static_mesh_bounds'] = [[round(x) for x in mn], [round(x) for x in mx]]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\level_probe_%s.json' % tag, 'w'), indent=1); print('LEVEL_PROBE', tag, R['world'], len(acts))
