"""Editor: debug of line traces: raw return of line_trace_single / multi at a few points + the static mesh actors (name, component collision profile, bounds) whose bounds contain the XY of the post-process centre -> Data/trace_debug.json"""
import unreal, json, traceback
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cx, cy = -3041.0, -87.0
    for name, ch in (('vis', unreal.TraceTypeQuery.TRACE_TYPE_QUERY1), ('cam', unreal.TraceTypeQuery.TRACE_TYPE_QUERY2)):
        r = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(cx, cy, 4000), unreal.Vector(cx, cy, -2000), ch, True, [], unreal.DrawDebugTrace.NONE, True)
        R['single_' + name] = str(type(r)) + ' ' + str(r)[:300]
        r = unreal.SystemLibrary.line_trace_multi(w, unreal.Vector(cx, cy, 4000), unreal.Vector(cx, cy, -2000), ch, True, [], unreal.DrawDebugTrace.NONE, True)
        R['multi_' + name] = str(type(r)) + ' ' + str(r)[:300]
    cand = []
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.StaticMeshActor):
            o, e = a.get_actor_bounds(False)
            if abs(o.x - cx) < e.x + 200 and abs(o.y - cy) < e.y + 200:
                smc = a.static_mesh_component
                cand.append([a.get_actor_label(), round(o.x), round(o.y), round(o.z), round(e.x), round(e.y), round(e.z), str(smc.get_collision_profile_name()), str(smc.static_mesh.get_name()) if smc.static_mesh else None])
    cand.sort(key=lambda r: r[3]); R['actors_over_xy'] = cand[:60]; R['n_over_xy'] = len(cand)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\trace_debug.json', 'w'), indent=1); print('TRACE_DEBUG', R.get('error', '')[-200:])
