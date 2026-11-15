"""PIE probe for <seconds> (default 8): per frame the ADS / FP-wanted flags, FPCamera active, anim curves (AimADS, ViewTP), FollowCamera FOV, boom arm length and
the rear / front sight points in the active camera's space (x forward, y right, z up) -> Data/ads_time_probe.json. Start it, then right-click (tap) in the viewport.
usage: py ue_ads_time_probe.py [seconds]"""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\ads_time_probe.json'
S = {'t0': time.time(), 'rows': []}
REAR = unreal.Vector(0.14139, -11.757165, 9.98355); FRONT = unreal.Vector(0.0809, 30.61, 9.8146)
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    def flag(t):
        c = pc.get_components_by_tag(unreal.ActorComponent, t); return int(bool(c and c[0].is_active()))
    fpc = pc.get_editor_property('FPCamera'); gun = pc.get_editor_property('FurinaRifle')
    mesh = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
    ai = mesh.get_anim_instance()
    boom = pc.get_components_by_class(unreal.SpringArmComponent)[0]
    fol = [c for c in pc.get_components_by_class(unreal.CameraComponent) if c.get_name() == 'FollowCamera'][0]
    ct = fpc.get_world_transform(); gt = gun.get_world_transform()
    r = ct.inverse_transform_location(gt.transform_location(REAR)); f = ct.inverse_transform_location(gt.transform_location(FRONT))
    S['rows'].append([round(time.time() - S['t0'], 3), flag('FurinaADS'), flag('FurinaShoulder'), int(pc.get_editor_property('FurinaFPWanted').is_active()), int(fpc.is_active()),
                      round(ai.get_curve_value('AimADS'), 3), round(ai.get_curve_value('ViewTP'), 3), round(fol.field_of_view, 1), round(boom.get_editor_property('target_arm_length'), 1),
                      [round(r.x, 1), round(r.y, 1), round(r.z, 1)], [round(f.x, 1), round(f.y, 1), round(f.z, 1)]])
    del pc, fpc, gun, mesh, ai, boom, fol, w
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        json.dump(dict(cols=['t', 'ads', 'sh', 'fpwant', 'fpcam', 'AimADS', 'ViewTP', 'fov', 'arm', 'rear', 'front'], rows=S['rows']), open(OUT, 'w'))
        print('ADS_TIME_PROBE', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
