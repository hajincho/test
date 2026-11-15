"""PIE: distance of every Left-* / Right-* hand bone to the nearest M4 vertex (rifle component space, Data/m4_geometry.json verts) plus the nearest
vertex position; run once in the hip pose, once with the arms in the shoulder pose -> Data/hand_grip_probe.json (appended per call)."""
import unreal, json, os, math
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    G = json.load(open(os.path.join(D, 'm4_geometry.json')))
    verts = G['verts']
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    comps = {c.get_name(): c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent)}
    mesh, rifle = comps['FurinaMesh'], comps['FurinaRifle']
    rx = rifle.get_world_transform()
    names = [str(n) for n in mesh.get_all_socket_names()] if hasattr(mesh, 'get_all_socket_names') else []
    bones = [n for n in names if n.startswith(('Left', 'Right')) and any(k in n for k in ('wrist', 'hand', 'finger', 'thumb', 'index', 'middle', 'ring', 'pinky', 'little', 'fore'))]
    R = {'n_sockets': len(names), 'bones': {}}
    for b in bones:
        p = rx.inverse_transform_location(mesh.get_socket_location(b))
        best = min(verts, key=lambda v: (v[0] - p.x) ** 2 + (v[1] - p.y) ** 2 + (v[2] - p.z) ** 2)
        R['bones'][b] = dict(p=[round(p.x, 1), round(p.y, 1), round(p.z, 1)], d=round(math.dist((p.x, p.y, p.z), best), 1), nearest=[round(c, 1) for c in best])
    path = os.path.join(D, 'hand_grip_probe.json'); json.dump(R, open(path, 'w'), indent=1); print('HAND_GRIP', len(R['bones']))
    del w, pc, comps, mesh, rifle
main(); del main
