"""PIE: after <delay> s dumps every zipline/pulley/special related variable of the pawn's bundle components and the flag components -> Data/zip_state_probe.json"""
import unreal, sys, json, time
S = {'t0': time.time()}; DELAY = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
PATHS = {'Grind_Rail_Component_BP': '/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP',
         'Platformer_Component_BP': '/Game/3DPlatformerGameBundle/Blueprints/Components/Platformer_Component_BP'}
V = {}
for k, p in PATHS.items():
    bp = unreal.load_asset(p); V[k] = [str(v) for v in unreal.BlueprintEditorLibrary.list_member_variable_names(bp) if '/Script/' not in str(v)]; del bp
def tick(dt):
    if time.time() - S['t0'] < DELAY: return
    unreal.unregister_slate_post_tick_callback(S['h']); R = {}
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    for c in pawn.get_components_by_class(unreal.ActorComponent):
        cls = c.get_class().get_name().removesuffix('_C')
        if cls in V:
            for n in V[cls]:
                if any(k in n.lower() for k in ('zip', 'pulley', 'using', 'jump', 'grab')):
                    try: R[cls[:8] + '.' + n] = str(c.get_editor_property(n))
                    except Exception as e: R[cls[:8] + '.' + n] = 'ERR'
    for tag in ('FurinaSpecial', 'FurinaZip'): R['flag.' + tag] = [bool(c.is_active()) for c in pawn.get_components_by_tag(unreal.ActorComponent, tag)]
    R['mode'] = str(pawn.character_movement.movement_mode)
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\zip_state_probe.json', 'w'), indent=1); print('ZIP_STATE', R)
    del w, pawn
S['h'] = unreal.register_slate_post_tick_callback(tick)
