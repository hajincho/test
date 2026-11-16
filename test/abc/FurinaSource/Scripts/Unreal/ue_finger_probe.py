"""PIE (2026-11-16): positions of the left-hand bones (wrist, thumb 0-2, index / middle / ring / little 1-3) in RIFLE-LOCAL cm (the FurinaRifle component space, the same space as Data/colt_geometry.json) and each bone's
local X / Y / Z axes in rifle space, in the first-person hip pose, shoulder pose and ADS. -> Data/finger_probe.json   usage: py ue_finger_probe.py [mesh_component_name]"""
import unreal, time, json, sys
try: unreal.unregister_slate_post_tick_callback(globals()['S']['h'])
except Exception: pass
MESH = sys.argv[1] if len(sys.argv) > 1 else 'FurinaMesh'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\finger_probe.json'
BONES = ['Left-elbow', 'Left-wrist', 'Thumb0_L', 'Thumb1_L', 'Thumb2_L'] + ['%sFinger%d_L' % (n, i) for n in ('Index', 'Middle', 'Ring', 'Little') for i in (1, 2, 3)]
S = {'t0': time.time(), 'phase': 0, 'out': {}}
def tick(dt):
    try: _tick()
    except Exception:
        import traceback; json.dump({'error': traceback.format_exc(), 'partial': S['out']}, open(OUT, 'w'), indent=1); unreal.unregister_slate_post_tick_callback(S['h'])
def snap(pc, tag):
    mesh = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == MESH][0]
    rifle = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaRifle'][0]
    RT = rifle.get_world_transform(); d = {}
    for b in BONES:
        T = mesh.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD)
        p = unreal.MathLibrary.inverse_transform_location(RT, T.translation)
        q = T.rotation
        ax = []
        for v in (unreal.Vector(1, 0, 0), unreal.Vector(0, 1, 0), unreal.Vector(0, 0, 1)):
            wv = q.rotate_vector(v); lv = RT.inverse_transform_direction(wv); ax.append([round(lv.x, 3), round(lv.y, 3), round(lv.z, 3)])
        d[b] = dict(pos=[round(p.x, 2), round(p.y, 2), round(p.z, 2)], axes=ax)
    S['out'][tag] = d
def _tick():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    t = time.time() - S['t0']; pc = unreal.GameplayStatics.get_player_character(w, 0); ph = S['phase']
    def comp(tag): return pc.get_components_by_tag(unreal.ActorComponent, tag)[0]
    if ph == 0 and t > 0.5: pc.get_editor_property('FurinaFPWanted').set_active(True); S['phase'] = 1
    elif ph == 1 and t > 2.5: snap(pc, 'hip'); comp('FurinaShoulder').set_active(True); S['phase'] = 2
    elif ph == 2 and t > 4.5: snap(pc, 'shoulder'); comp('FurinaShoulder').set_active(False); comp('FurinaADS').set_active(True); S['phase'] = 3
    elif ph == 3 and t > 6.5:
        snap(pc, 'ads'); comp('FurinaADS').set_active(False); pc.get_editor_property('FurinaFPWanted').set_active(False)
        json.dump(S['out'], open(OUT, 'w'), indent=1); print('FINGER_PROBE'); unreal.unregister_slate_post_tick_callback(S['h']); S['phase'] = 4
    del w, pc
S['h'] = unreal.register_slate_post_tick_callback(tick)
