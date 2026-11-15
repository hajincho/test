"""PIE: mesh-space (X left, Y forward, Z up, cm) positions of Hips / Spine / Chest / Neck / Head / shoulders / thighs and the forward lean (deg, atan2(dy, dz)) of Hips->Spine,
Spine->Chest, Chest->Neck, Neck->Head and Hips->Head, plus the curves RestW-related (ViewTP, FireHold) -> Data/spine_probe.json (key = tag). usage: py ue_spine_probe.py [tag]"""
import unreal, json, os, sys, math
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\spine_probe.json'
def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'x'
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pc = unreal.GameplayStatics.get_player_character(w, 0)
    m = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]; T = m.get_world_transform()
    def M(b): return unreal.MathLibrary.inverse_transform_location(T, m.get_socket_location(b)).to_tuple()
    names = ('Hips', 'Spine', 'Chest', 'Neck', 'Head', 'Left-arm', 'Right-arm', 'Left-leg', 'Right-leg')
    P = {n: M(n) for n in names}
    R = {n: [round(x, 1) for x in p] for n, p in P.items()}
    def lean(a, b): return round(math.degrees(math.atan2(P[b][1] - P[a][1], P[b][2] - P[a][2])), 1)
    R['lean'] = {a + '>' + b: lean(a, b) for a, b in (('Hips', 'Spine'), ('Spine', 'Chest'), ('Chest', 'Neck'), ('Neck', 'Head'), ('Hips', 'Head'))}
    ai = m.get_anim_instance(); R['curves'] = {k: round(ai.get_curve_value(k), 3) for k in ('ViewTP', 'FireHold', 'AimADS', 'AimShoulder')}
    d = json.load(open(OUT)) if os.path.exists(OUT) else {}; d[tag] = R; json.dump(d, open(OUT, 'w'), indent=1); print('SPINE_PROBE', tag, R['lean'])
    del w, pc, m, ai
main(); del main
