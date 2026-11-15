"""PIE: for every SkeletalMeshComponent of the player character prints name, skinned asset, relative scale, visibility and anim class -> Data/mesh_state.json"""
import unreal, json
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pc = unreal.GameplayStatics.get_player_character(w, 0); R = []
for c in pc.get_components_by_class(unreal.SkeletalMeshComponent):
    a = c.get_editor_property('skinned_asset'); R.append(dict(name=c.get_name(), asset=a.get_path_name() if a else None, scale=str(c.get_editor_property('relative_scale3d')), visible=c.is_visible(), anim=str(c.get_editor_property('anim_class').get_name()) if c.get_editor_property('anim_class') else None))
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\mesh_state.json', 'w'), indent=1); print('MESH_STATE', R)
del w, pc
