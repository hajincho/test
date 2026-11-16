"""Editor: arm BEFORE pressing Play. When the PIE world appears it samples every frame for <seconds> (default 8) and logs a row whenever Grind UsingRail? / movement mode / FurinaSpecial changes
(time since PIE start, pawn z, mode, UsingRail?, Spline, FurinaSpecial) -> Data/rail_start_probe.json"""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
S = {'t0': None, 'rows': [], 'last': None}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    if pawn is None: return
    if S['t0'] is None: S['t0'] = time.time()
    g = [c for c in pawn.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name().startswith('Grind_Rail')]
    g = g[0] if g else None
    def gv(n):
        try: v = g.get_editor_property(n); return v.get_path_name() if hasattr(v, 'get_path_name') else (None if v is None else bool(v))
        except Exception: return 'ERR'
    row = dict(t=round(time.time() - S['t0'], 2), z=round(pawn.get_actor_location().z), mode=str(pawn.character_movement.movement_mode).split('.')[-1], rail=gv('UsingRail?'), spline=gv('Spline'),
               special=[bool(c.is_active()) for c in pawn.get_components_by_tag(unreal.ActorComponent, 'FurinaSpecial')], tick=(bool(g.is_component_tick_enabled()) if g else None))
    key = (row['rail'], row['mode'], str(row['special']), row['tick'])
    if key != S['last']: S['rows'].append(row)
    S['last'] = key; del w, pawn, g
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h']); json.dump(S['rows'], open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\rail_start_probe.json', 'w'), indent=1); print('RAIL_START', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
