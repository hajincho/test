"""Lists zipline / rappel related actors of the current level (editor or PIE world) with locations -> Data/find_zip.json"""
import unreal, json
R = []
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    n = a.get_name() + ' ' + a.get_class().get_name()
    if any(k in n.lower() for k in ('pulley',)):
        l = a.get_actor_location(); R.append([a.get_name(), a.get_class().get_name(), [round(l.x), round(l.y), round(l.z)], [c.get_name() for c in a.get_components_by_class(unreal.SceneComponent)][:8]])
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\find_pulley.json', 'w'), indent=1); print('FIND_ZIP', len(R))
