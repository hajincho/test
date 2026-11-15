"""PIE: camera-space depth of the M4 vertices (Data/m4_geometry.json) in view: min depth, count below 2 / 4 / 6 cm, camera FOV, near plane
console value -> Data/ads_clip_probe.json (appended list). Run during ADS / hip / reload."""
import unreal, json, os, math
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    verts = json.load(open(os.path.join(D, 'm4_geometry.json')))['verts']
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_character(w, 0); cm = unreal.GameplayStatics.get_player_camera_manager(w, 0)
    rifle = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaRifle'][0]
    rx = rifle.get_world_transform(); cam = cm.get_camera_location(); r = cm.get_camera_rotation(); f = r.get_forward_vector(); up = r.get_up_vector(); rt = r.get_right_vector()
    th = math.tan(math.radians(cm.get_fov_angle() / 2)); asp = 16 / 9
    depths = []
    for v in verts[::2]:
        p = rx.transform_location(unreal.Vector(*v)) - cam
        d = p.dot(f)
        if d <= 0.1: continue
        sx, sy = p.dot(rt) / (d * th), p.dot(up) / (d * th / asp)
        if abs(sx) <= 1.05 and abs(sy) <= 1.05: depths.append(d)
    out = dict(fov=round(cm.get_fov_angle(), 1), n=len(depths), min=round(min(depths), 2) if depths else None, below2=sum(1 for x in depths if x < 2), below4=sum(1 for x in depths if x < 4), below6=sum(1 for x in depths if x < 6),
               ads=bool(pc.get_components_by_tag(unreal.ActorComponent, 'FurinaADS')[0].is_active()))
    path = os.path.join(D, 'ads_clip_probe.json'); L = json.load(open(path)) if os.path.exists(path) else []; L.append(out); json.dump(L, open(path, 'w'), indent=1); print('ADS_CLIP', out)
    del w, pc, cm, rifle
main(); del main
