"""PIE probe (~10 s): movement mode, velocity and the bundle traversal components' bool/enum variables over time."""
import unreal, json, time
PATHS = {'Grind_Rail_Component_BP': '/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP',
         'Homing_Attack_Component_BP': '/Game/3DPlatformerGameBundle/Blueprints/Components/Homing_Attack_Component_BP',
         'Platformer_Component_BP': '/Game/3DPlatformerGameBundle/Blueprints/Components/Platformer_Component_BP'}
S = {'t0': time.time(), 'rows': [], 'vars': {}}
for k, p in PATHS.items():
    bp = unreal.load_asset(p)
    S['vars'][k] = [str(v) for v in unreal.BlueprintEditorLibrary.list_member_variable_names(bp) if '/Script/' not in str(v)] if bp else []
    del bp
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        cm = pawn.character_movement
        row = {'t': round(time.time() - S['t0'], 2), 'mode': str(cm.movement_mode), 'custom': int(cm.custom_movement_mode),
               'v': round(pawn.get_velocity().length()), 'vz': round(pawn.get_velocity().z)}
        for c in pawn.get_components_by_class(unreal.ActorComponent):
            cls = c.get_class().get_name().replace('_C', '')
            if cls in S['vars']:
                for n in S['vars'][cls]:
                    try:
                        val = c.get_editor_property(n)
                        if isinstance(val, (bool, int, float)) or 'Enum' in type(val).__name__ or type(val).__name__ in ('str', 'Name'):
                            row[cls[:6] + '.' + n] = val if isinstance(val, (bool, int)) else str(val)
                    except Exception: pass
        S['rows'].append(row)
    except Exception as e:
        S['rows'].append({'err': repr(e)[:200]})
    if time.time() - S['t0'] > 10:
        unreal.unregister_slate_post_tick_callback(S['h'])
        json.dump({'vars': S['vars'], 'rows': S['rows']}, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\traversal_live.json', 'w'), indent=0, default=str)
S['h'] = unreal.register_slate_post_tick_callback(tick)
