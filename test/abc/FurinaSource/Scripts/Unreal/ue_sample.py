"""Samples Furina every frame for ~9 s in PIE: speed, idle curve, cloth/hair tip offsets (component space)."""
import unreal, json, os, time
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
BONES = ['Hips', 'Left-leg', 'Left-knee', 'Right-leg', 'Right-knee', 'Right-ankle', 'Left-toe', 'HB1_7_4', 'HB1_7_0', 'HB2_18_1', 'HB3_17_1', 'HB4_16_1', 'F_17_1_L', 'F_17_1_R', 'CF_2_L', 'DM_5_1', 'Left-ankle', 'Head']
state = {'t0': time.time(), 'rows': []}
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if not w: return
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        comp = [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
        xf = comp.get_world_transform()
        row = {'t': round(time.time() - state['t0'], 3), 'v': round(pawn.get_velocity().length(), 1),
               'idle': round(comp.get_anim_instance().get_curve_value('FurinaIdle'), 3)}
        for b in BONES:
            p = xf.inverse_transform_location(comp.get_socket_location(b))
            row[b] = [round(p.x, 2), round(p.y, 2), round(p.z, 2)]
        state['rows'].append(row)
    except Exception as e:
        state['rows'].append({'err': repr(e)})
    if time.time() - state['t0'] > 7:
        unreal.unregister_slate_post_tick_callback(state['h'])
        json.dump(state['rows'], open(os.path.join(S, 'ue_sample.json'), 'w'), indent=0)
        print('SAMPLE_DONE', len(state['rows']))
state['h'] = unreal.register_slate_post_tick_callback(tick)

