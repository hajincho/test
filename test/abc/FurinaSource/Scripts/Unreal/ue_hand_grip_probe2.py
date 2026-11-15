"""PIE: like ue_hand_grip_probe.py but for every socket / bone whose name starts with Left or Right (finger bones included, names printed) -> Data/hand_grip_probe2.json
(position in rifle space, distance to the nearest M4 vertex, nearest vertex). usage: py ue_hand_grip_probe2.py [tag]"""
import unreal, json, os, math, sys
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'x'
    verts = json.load(open(os.path.join(D, 'm4_geometry.json')))['verts']
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    comps = {c.get_name(): c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent)}
    mesh, rifle = comps['FurinaMesh'], comps['FurinaRifle']
    rx = rifle.get_world_transform()
    names = [str(n) for n in mesh.get_all_socket_names()]
    R = {}
    for b in names:
        if not (b.startswith('Left') or b.startswith('Right')): continue
        p = rx.inverse_transform_location(mesh.get_socket_location(b))
        best = min(verts, key=lambda v: (v[0] - p.x) ** 2 + (v[1] - p.y) ** 2 + (v[2] - p.z) ** 2)
        R[b] = dict(p=[round(p.x, 1), round(p.y, 1), round(p.z, 1)], d=round(math.dist((p.x, p.y, p.z), best), 1), nearest=[round(c, 1) for c in best])
    path = os.path.join(D, 'hand_grip_probe2.json')
    allv = json.load(open(path)) if os.path.exists(path) else {}
    allv[tag] = R; json.dump(allv, open(path, 'w'), indent=1); print('HAND_GRIP2', tag, len(R))
    del w, pc, comps, mesh, rifle
main(); del main
