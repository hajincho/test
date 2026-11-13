"""Per frame (~14 s): blink curve + morph weight, hair tips in Head space, distance of braid joints to chest/hips."""
import unreal, json, os, time
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
HAIR = ['F_6_1_L', 'F_12_1_L', 'F_17_1_L', 'F_17_1_R', 'CF_2_L', 'DM_5_1']
state = {'t0': time.time(), 'rows': []}
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        comp = [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
        ai = comp.get_anim_instance()
        row = {'t': round(time.time() - state['t0'], 3), 'v': round(pawn.get_velocity().length(), 1),
               'idle': round(ai.get_curve_value('FurinaIdle'), 3), 'blink': round(ai.get_curve_value('IdleBlink'), 3)}
        try: row['morph'] = round(comp.get_morph_target('IdleBlink'), 3)
        except Exception as e: row['morph'] = repr(e)[:60]
        hx = comp.get_socket_transform('Head', unreal.RelativeTransformSpace.RTS_WORLD)
        for b in HAIR:
            p = hx.inverse_transform_location(comp.get_socket_location(b)); row[b] = [round(p.x, 2), round(p.y, 2), round(p.z, 2)]
        # closest braid joint to the torso centre line (chest..hips)
        a = comp.get_socket_location('Hips'); c = comp.get_socket_location('Chest')
        best = 1e9
        for side in ('L', 'R'):
            for k in range(3, 18):
                q = comp.get_socket_location('F_%d_1_%s' % (k, side))
                ab = c - a; t = max(0, min(1, (q - a).dot(ab) / max(ab.dot(ab), 1e-6)))
                best = min(best, (q - (a + ab * t)).length())
        row['braid_torso'] = round(best, 1)
        state['rows'].append(row)
    except Exception as e:
        state['rows'].append({'err': repr(e)})
    if time.time() - state['t0'] > 14:
        unreal.unregister_slate_post_tick_callback(state['h'])
        json.dump(state['rows'], open(os.path.join(D, 'ue_sample3.json'), 'w'), indent=0)
state['h'] = unreal.register_slate_post_tick_callback(tick)
