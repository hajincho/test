"""PIE probe (~16 s): speed, curves (idle/walk/hair/blink/slope debug), feet spread, ankle heights, hair offsets in Head space."""
import unreal, json, os, time
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
HAIR = ['F_17_1_L', 'F_17_1_R', 'F_8_1_L', 'CF_2_L', 'CF_2_R', 'DM_5_1', 'DM_3_1']
CURVES = ['AimPitch', 'RifleKick', 'RifleReload', 'FurinaIdle', 'FurinaWalk', 'HairDyn', 'IdleBlink', 'DbgL', 'DbgR', 'DbgW', 'DbgC']
state = {'t0': time.time(), 'rows': [], 'n': 0}
def r2(v): return [round(x, 1) for x in v.to_tuple()]
def tick(dt):
    state['n'] += 1
    if state['n'] % 3 == 0:
        try:
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
            comp = [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
            ai = comp.get_anim_instance()
            xf = comp.get_world_transform()
            hx = comp.get_socket_transform('Head', unreal.RelativeTransformSpace.RTS_WORLD)
            row = {'t': round(time.time() - state['t0'], 2), 'v': round(pawn.get_velocity().length(), 1),
                   'mws': round(pawn.character_movement.get_editor_property('max_walk_speed'), 1)}
            for cv in CURVES: row[cv] = round(ai.get_curve_value(cv), 3)
            for b in ('Left-ankle', 'Right-ankle', 'Left-toe', 'Right-toe', 'Left-knee', 'Right-knee', 'Hips', 'Right-wrist', 'Left-wrist', 'Neck', 'Head', 'Right-elbow', 'Left-elbow'):
                row[b] = r2(xf.inverse_transform_location(comp.get_socket_location(b)))
            for b in HAIR: row['h_' + b] = r2(hx.inverse_transform_location(comp.get_socket_location(b)))
            state['rows'].append(row)
        except Exception as e:
            state['rows'].append({'err': repr(e)[:200]})
    if time.time() - state['t0'] > 16:
        unreal.unregister_slate_post_tick_callback(state['h'])
        json.dump(state['rows'], open(os.path.join(D, 'ue_playtest.json'), 'w'), indent=0)
        print('PLAYTEST_DONE')
state['h'] = unreal.register_slate_post_tick_callback(tick)
