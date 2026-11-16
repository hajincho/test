"""Editor: why does the Grind_Rail_Component think the pawn rides a rail in the tunnel? prints the component defaults (Rail Component Tag, Spline Mesh Object Type, trace settings) and lists the level's components that carry
that tag (and all SplineMeshComponents) -> Data/rail_tag_probe.json"""
import unreal, json, traceback
R = {}
try:
    g = unreal.load_asset('/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP'); cdo = unreal.get_default_object(g.generated_class())
    for p in ('RailComponentTag', 'ZiplineActorTag', 'TraceIgnoredComponentTag', 'SplineMeshObjectType', 'TraceObjectType', 'SplineLineTraceHeight', 'SplineMeshHeight', 'RailJumpBlockedObjTypes'):
        try: R[p] = str(cdo.get_editor_property(p))
        except Exception as e: R[p] = 'ERR ' + str(e)[:60]
    tag = str(cdo.get_editor_property('RailComponentTag')); R['tag'] = tag
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); hits = []; spl = []
    for a in eas.get_all_level_actors():
        for c in a.get_components_by_class(unreal.SceneComponent):
            tags = [str(t) for t in c.component_tags]
            if tag in tags or isinstance(c, unreal.SplineMeshComponent):
                o = c.get_world_location(); (hits if tag in tags else spl).append([a.get_actor_label(), c.get_name(), c.get_class().get_name(), tags, round(o.x), round(o.y), round(o.z)])
    R['tagged'] = hits[:40]; R['n_tagged'] = len(hits); R['spline_meshes'] = spl[:40]; R['n_spline'] = len(spl)
    ts = [a.get_actor_label() for a in eas.get_all_level_actors() if tag in [str(t) for t in a.tags]]; R['actors_with_tag'] = ts[:40]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\rail_tag_probe.json', 'w'), indent=1); print('RAIL_TAG', R.get('error', '')[-200:])
