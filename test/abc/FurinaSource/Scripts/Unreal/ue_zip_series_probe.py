"""PIE: for <seconds> samples every frame: Grind UsingZipline?/JumpToZipline?/UsingRail?, Platformer UseZipline?/OverlapWithPulley?, flag components FurinaSpecial/FurinaZip,
movement mode, pawn z, Furina wrist positions (mesh space) -> Data/zip_series_probe.json (only rows where something changes)"""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
S = {'t0': time.time(), 'rows': [], 'last': None}
def comps(pawn):
    g = [c for c in pawn.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name().startswith('Grind_Rail')][0]
    p = [c for c in pawn.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name().startswith('Platformer_Component')][0]
    return g, p
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    g, p = comps(pawn)
    def gv(c, n):
        try: return bool(c.get_editor_property(n))
        except Exception: return None
    m = [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name().startswith('FurinaMesh')][0]; T = m.get_world_transform()
    def L(b): return [round(v) for v in unreal.MathLibrary.inverse_transform_location(T, m.get_socket_location(b)).to_tuple()]
    row = dict(t=round(time.time() - S['t0'], 2), grind_zip=gv(g, 'UsingZipline?'), grind_jz=gv(g, 'JumpToZipline?'), grind_rail=gv(g, 'UsingRail?'), plat_use=gv(p, 'UseZipline?'),
               plat_ov=gv(p, 'OverlapWithPulley?'), special=[bool(c.is_active()) for c in pawn.get_components_by_tag(unreal.ActorComponent, 'FurinaSpecial')],
               zipflag=[bool(c.is_active()) for c in pawn.get_components_by_tag(unreal.ActorComponent, 'FurinaZip')], mode=str(pawn.character_movement.movement_mode).split('.')[-1],
               z=round(pawn.get_actor_location().z), lw=L('Left-wrist'), rw=L('Right-wrist'))
    key = (row['grind_zip'], row['grind_jz'], row['grind_rail'], row['plat_use'], row['plat_ov'], str(row['special']), str(row['zipflag']), row['mode'])
    if key != S['last'] or len(S['rows']) % 15 == 0: S['rows'].append(row)
    S['last'] = key; del w, pawn, g, p, m
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h']); json.dump(S['rows'], open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\zip_series_probe.json', 'w')); print('ZIP_SERIES', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
