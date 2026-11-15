"""PIE: rifle origin relative to the FP eye point (FPCamera socket) in mesh component axes, FP camera active? -> appends to Data/fp_grip_probe.json"""
import unreal, json, os
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_grip_probe.json'
def main():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    comps = {c.get_name(): c for c in pc.get_components_by_class(unreal.SceneComponent)}
    mesh, rifle, cam = comps['FurinaMesh'], comps['FurinaRifle'], comps['FPCamera']
    mx = mesh.get_world_transform()
    r = mx.inverse_transform_location(rifle.get_world_location()); e = mx.inverse_transform_location(cam.get_world_location())
    row = dict(fp=cam.is_active(), rel=[round(a - b, 1) for a, b in zip(r.to_tuple(), e.to_tuple())], dist=round((r - e).length(), 1),
               rifle_scale=round(rifle.get_world_scale().x, 3))
    rows = json.load(open(OUT)) if os.path.exists(OUT) else []
    rows.append(row); json.dump(rows, open(OUT, 'w'), indent=1); print('GRIP', row)
    del w, pc, comps, mesh, rifle, cam
main(); del main
