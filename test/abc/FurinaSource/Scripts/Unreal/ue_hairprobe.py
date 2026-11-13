"""PIE probe: records hair chain joints in Head space for ~4 s (compare with the reference pose offline)."""
import unreal, json, os, time
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
BONES = ['Head'] + ['F_%d_1_L' % i for i in (0, 4, 8, 12, 17)] + ['F_%d_1_R' % i for i in (0, 4, 8, 12, 17)] + \
        ['CF_1_L', 'CF_2_L', 'CF_1_R', 'CF_2_R'] + ['DM_%d_1' % i for i in range(6)]
state = {'t0': time.time(), 'rows': [], 'n': 0}
def tick(dt):
    state['n'] += 1
    if state['n'] % 6 == 0:
        try:
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
            comp = [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
            hx = comp.get_socket_transform('Head', unreal.RelativeTransformSpace.RTS_WORLD)
            row = {'t': round(time.time() - state['t0'], 3), 'vel': [round(v, 1) for v in pawn.get_velocity().to_tuple()]}
            for b in BONES:
                p = comp.get_socket_location(b)
                row[b] = [round(v, 2) for v in hx.inverse_transform_location(p).to_tuple()]
            state['rows'].append(row)
        except Exception as e:
            state['rows'].append({'err': repr(e)})
    if time.time() - state['t0'] > 4:
        unreal.unregister_slate_post_tick_callback(state['h'])
        json.dump(state['rows'], open(os.path.join(D, 'ue_hairprobe.json'), 'w'), indent=0)
        print('HAIRPROBE_DONE')
state['h'] = unreal.register_slate_post_tick_callback(tick)
