"""PIE: after <delay> s samples the Furina mesh-space positions of both wrists, elbows, head, hips and the rifle muzzle once -> Data/zip_hand_probe.json"""
import unreal, sys, json, time
S = {'t0': time.time()}
DELAY = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
def tick(dt):
    if time.time() - S['t0'] < DELAY: return
    unreal.unregister_slate_post_tick_callback(S['h'])
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    ms = {c.get_name(): c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent)}
    m = [c for n, c in ms.items() if n.startswith('FurinaMesh')][0]; T = m.get_world_transform()
    def L(b): return [round(v, 1) for v in unreal.MathLibrary.inverse_transform_location(T, m.get_socket_location(b)).to_tuple()]
    R = {b: L(b) for b in ('Head', 'Hips', 'Left-arm', 'Left-elbow', 'Left-wrist', 'Right-arm', 'Right-elbow', 'Right-wrist')}
    R['rifle_muzzle'] = [round(v, 1) for v in unreal.MathLibrary.inverse_transform_location(T, ms['FurinaRifle'].get_world_transform().transform_location(unreal.Vector(0, 40.625, 4.849))).to_tuple()]
    z = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if a.get_name().startswith('Zipline_BP_2')][0]
    R['pulley'] = [round(v, 1) for v in unreal.MathLibrary.inverse_transform_location(T, [c for c in z.get_components_by_class(unreal.SceneComponent) if c.get_name() == 'SM_Pulley'][0].get_world_location()).to_tuple()]
    R['scale'] = [round(v, 3) for v in T.scale3d.to_tuple()]
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\zip_hand_probe.json', 'w'), indent=1); print('ZIP_HAND', R)
    del w, pc, ms, m
S['h'] = unreal.register_slate_post_tick_callback(tick)
