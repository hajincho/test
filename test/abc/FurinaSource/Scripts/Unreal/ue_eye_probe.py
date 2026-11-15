"""PIE: FPCamera (eye point), Head, shoulders, wrists, rifle origin in mesh space (cm), standing wherever the pawn is -> Data/eye_probe.json (key = tag). usage: py ue_eye_probe.py [tag]"""
import unreal, json, os, sys
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\eye_probe.json'
def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'x'
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pc = unreal.GameplayStatics.get_player_character(w, 0)
    comps = {c.get_name(): c for c in pc.get_components_by_class(unreal.SceneComponent)}
    m, r, cam = comps['FurinaMesh'], comps['FurinaRifle'], comps['FPCamera']; T = m.get_world_transform(); RT = r.get_world_transform()
    def M(v): return [round(x, 1) for x in unreal.MathLibrary.inverse_transform_location(T, v).to_tuple()]
    R = {'eye': M(cam.get_world_location()), 'rifle': M(RT.transform_location(unreal.Vector(0, 0, 0)))}
    for n, v in (('y', unreal.Vector(0, 1, 0)), ('z', unreal.Vector(0, 0, 1))):
        a = unreal.MathLibrary.inverse_transform_location(T, RT.transform_location(v)); b = unreal.MathLibrary.inverse_transform_location(T, RT.transform_location(unreal.Vector(0, 0, 0)))
        R['rifle_' + n] = [round(x, 3) for x in (a - b).to_tuple()]
    for b in ('Head', 'Hips', 'Left-arm', 'Right-arm', 'Left-wrist', 'Right-wrist', 'Left-elbow', 'Right-elbow'): R[b] = M(m.get_socket_location(b))
    d = json.load(open(OUT)) if os.path.exists(OUT) else {}; d[tag] = R; json.dump(d, open(OUT, 'w'), indent=1); print('EYE_PROBE', tag, R['eye'])
    del w, pc, comps, m, r, cam
main(); del main
