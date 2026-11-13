"""Per-frame: cloth tips in Hips space, hair tips in Head space (pure secondary motion), + speed/idle."""
import unreal, json, os, time
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
SETS = {'Hips': ['HB1_7_4', 'HB1_7_0', 'HB2_18_1', 'HB3_17_1', 'HB4_16_1'], 'Head': ['F_17_1_L', 'F_17_1_R', 'CF_2_L', 'DM_5_1']}
state = {'t0': time.time(), 'rows': []}
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        comp = [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
        row = {'t': round(time.time() - state['t0'], 3), 'v': round(pawn.get_velocity().length(), 1),
               'idle': round(comp.get_anim_instance().get_curve_value('FurinaIdle'), 3), 'dt': dt}
        for base, tips in SETS.items():
            bx = comp.get_socket_transform(base, unreal.RelativeTransformSpace.RTS_WORLD)
            for b in tips:
                p = bx.inverse_transform_location(comp.get_socket_location(b))
                s = bx.scale3d.x
                row[b] = [round(p.x * s, 2), round(p.y * s, 2), round(p.z * s, 2)]
        state['rows'].append(row)
    except Exception as e:
        state['rows'].append({'err': repr(e)})
    if time.time() - state['t0'] > 7:
        unreal.unregister_slate_post_tick_callback(state['h'])
        json.dump(state['rows'], open(os.path.join(S, 'ue_sample2.json'), 'w'), indent=0)
state['h'] = unreal.register_slate_post_tick_callback(tick)
