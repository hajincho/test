"""Editor (tunnel level open): in the tunnel PIE the Grind_Rail_Component starts with UsingRail? = True (class default; nothing tagged 'Rail' in this level ever resets it), which switches on FurinaSpecial and blocks firing.
Sets UsingRail? / WasUsingRail? = False on the level instance of Furina_Player (a per-instance override that is saved with the level) and saves the level -> Data/level_norail.json"""
import unreal, json, traceback
R = {}
try:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    pawn = [a for a in eas.get_all_level_actors() if a.get_actor_label() == 'Furina_Player'][0]
    g = [c for c in pawn.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name().startswith('Grind_Rail')][0]
    for p in ('UsingRail?', 'WasUsingRail?'):
        R[p + '_before'] = bool(g.get_editor_property(p)); g.set_editor_property(p, False); R[p + '_after'] = bool(g.get_editor_property(p))
    pawn.modify(); g.modify()
    R['saved'] = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\level_norail.json', 'w'), indent=1); print('NORAIL', R)
