"""PIE: Grind_Rail_Component state (which actor/component it thinks is a rail) + pawn location -> Data/pie_state_probe.json"""
import unreal, json, traceback
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    l = pawn.get_actor_location(); R['loc'] = [l.x, l.y, l.z]
    g = [c for c in pawn.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name().startswith('Grind_Rail')][0]
    for p in ('UsingRail?', 'UseRail?', 'WasUsingRail?', 'HitActor', 'HitComponent', 'Spline', 'PreviousSpline', 'HitObject?', 'HitSurface?', 'RailOverlap?', 'SplineMeshComponent', 'RailJumpActive?', 'UsingZipline?'):
        try:
            v = g.get_editor_property(p); R[p] = v.get_path_name() if hasattr(v, 'get_path_name') else str(v)
        except Exception as e: R[p] = 'ERR ' + str(e)[:60]
    for p in ('FurinaAmmo', 'FurinaReserve', 'FurinaReloading'): R[p] = pawn.get_editor_property(p)
    R['hitactor_class'] = None
    try:
        ha = g.get_editor_property('HitActor'); R['hitactor_class'] = ha.get_class().get_name() + ' / ' + ha.get_actor_label()
    except Exception: pass
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\pie_state_probe.json', 'w'), indent=1, default=str); print('PIE_STATE', R.get('error', '')[-200:])
