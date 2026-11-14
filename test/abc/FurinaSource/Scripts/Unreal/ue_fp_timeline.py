"""PIE probe (~6 s): rifle curves, montage state, left hand position in the rifle frame, rifle animation time."""
import unreal, json, os, time
import sys
state = {'t0': time.time(), 'rows': [], 'dur': sys.argv[1] if len(sys.argv) > 1 else 6}
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        comps = {c.get_name(): c for c in pawn.get_components_by_class(unreal.SceneComponent)}
        mesh, rifle = comps['FurinaMesh'], comps['FurinaRifle']
        ai = mesh.get_anim_instance()
        rx = rifle.get_world_transform()
        row = {'t': round(time.time() - state['t0'], 2),
               'kick': round(ai.get_curve_value('RifleKick'), 3), 'reload': round(ai.get_curve_value('RifleReload'), 3),
               'aim': round(ai.get_curve_value('AimPitch'), 1),
               'montage': str(ai.get_current_active_montage().get_name()) if ai.get_current_active_montage() else None,
               'lw_in_rifle': [round(v, 1) for v in rx.inverse_transform_location(mesh.get_socket_location('Left-wrist')).to_tuple()],
               'rw_in_rifle': [round(v, 1) for v in rx.inverse_transform_location(mesh.get_socket_location('Right-wrist')).to_tuple()],
               'fp': comps['FPCamera'].is_active(), 'want': comps['FurinaFPWanted'].is_active() if 'FurinaFPWanted' in comps else None,
               'mode': str(pawn.character_movement.movement_mode).split('.')[-1][:14], 'v': round(pawn.get_velocity().length()),
               'run': round(ai.get_curve_value('DbgC'), 2)}
        if ai.get_current_active_montage() and not state.get('names'):
            try: state['names'] = [str(n) for n in ai.get_all_curve_names()]
            except Exception as e: state['names'] = repr(e)[:150]
            try: state['mweight'] = ai.montage_get_weight(ai.get_current_active_montage()) if hasattr(ai, 'montage_get_weight') else 'n/a'
            except Exception as e: state['mweight'] = repr(e)[:100]
        state['rows'].append(row)
    except Exception as e:
        state['rows'].append({'err': repr(e)[:200]})
    if time.time() - state['t0'] > float(state.get('dur', 6)):
        unreal.unregister_slate_post_tick_callback(state['h'])
        state['rows'].append({'names': state.get('names'), 'mweight': state.get('mweight')})
        json.dump(state['rows'], open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_timeline.json', 'w'), indent=0)
state['h'] = unreal.register_slate_post_tick_callback(tick)
