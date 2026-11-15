"""PIE: rifle origin / axes (mesh space), shoulders, elbows, wrists, head -> Data/rifle_frame_probe.json; plus left wrist expressed in rifle space and the distance left shoulder -> point on the rifle
at rifle-local y = 0, 10, 20, 30 (the handguard) so the reach (arm = 21.14 + 18.02 = 39.2 cm) can be judged. usage: py ue_rifle_frame_probe.py <tag>"""
import unreal, sys, json, os
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\rifle_frame_probe.json'
def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'x'
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pc = unreal.GameplayStatics.get_player_character(w, 0)
    ms = {c.get_name(): c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent)}; m = ms['FurinaMesh']; r = ms['FurinaRifle']; T = m.get_world_transform(); RT = r.get_world_transform()
    def M(v): return unreal.MathLibrary.inverse_transform_location(T, v)
    def rd(v): return [round(x, 1) for x in v.to_tuple()]
    R = {'rifle_origin': rd(M(RT.transform_location(unreal.Vector(0, 0, 0))))}
    for n, v in (('y', unreal.Vector(0, 1, 0)), ('z', unreal.Vector(0, 0, 1)), ('x', unreal.Vector(1, 0, 0))): R['rifle_axis_' + n] = [round(x, 3) for x in (M(RT.transform_location(v)) - M(RT.transform_location(unreal.Vector(0, 0, 0)))).to_tuple()]
    for b in ('Head', 'Hips', 'Left-arm', 'Left-elbow', 'Left-wrist', 'Right-arm', 'Right-elbow', 'Right-wrist'): R[b] = rd(M(m.get_socket_location(b)))
    sh = M(m.get_socket_location('Left-arm')); R['reach_left_to_rifle_y'] = {str(y): round((M(RT.transform_location(unreal.Vector(0, y, 0))) - sh).length(), 1) for y in (-10, 0, 10, 20, 30, 40)}
    lw = RT.inverse_transform_location(m.get_socket_location('Left-wrist')); R['left_wrist_in_rifle'] = rd(lw)
    d = json.load(open(OUT)) if os.path.exists(OUT) else {}; d[tag] = R; json.dump(d, open(OUT, 'w'), indent=1); print('RIFLE_FRAME', tag)
    del w, pc, ms, m, r
main(); del main
