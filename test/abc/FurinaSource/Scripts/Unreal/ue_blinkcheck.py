"""Samples ~10 s of idle: IdleBlink curve value and whether the engine treats it as an active morph-target curve."""
import unreal, json, os, time
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
state = {'t0': time.time(), 'rows': []}
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        comp = [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
        ai = comp.get_anim_instance()
        v = ai.get_curve_value('IdleBlink')
        if v > 0.05:
            morph = [str(n) for n in ai.get_active_curve_names(unreal.AnimCurveType.MORPH_TARGET_CURVE)]
            state['rows'].append({'t': round(time.time() - state['t0'], 3), 'blink': round(v, 3), 'morph_active': 'IdleBlink' in morph, 'n_morph': len(morph)})
    except Exception as e:
        state['rows'].append({'err': repr(e)})
    if time.time() - state['t0'] > 10:
        unreal.unregister_slate_post_tick_callback(state['h'])
        json.dump(state['rows'], open(os.path.join(D, 'ue_blinkcheck.json'), 'w'), indent=0)
state['h'] = unreal.register_slate_post_tick_callback(tick)
