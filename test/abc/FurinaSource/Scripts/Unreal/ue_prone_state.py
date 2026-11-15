"""PIE: prints / writes the stance state (IsCrouching, FurinaProne flag, FurinaProneWant, capsule half height, max speeds) -> Data/prone_state.json"""
import unreal, json
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pc = unreal.GameplayStatics.get_player_character(w, 0)
cmc = pc.character_movement; cap = pc.capsule_component
R = dict(crouching=bool(cmc.is_crouching()), prone_flag=bool(pc.get_components_by_tag(unreal.ActorComponent, 'FurinaProne')[0].is_active()), want=bool(pc.get_editor_property('FurinaProneWant')),
         half_height=round(cap.get_scaled_capsule_half_height(), 1), max_walk=cmc.get_editor_property('max_walk_speed'), max_crouched=cmc.get_editor_property('max_walk_speed_crouched'), speed=round(pc.get_velocity().length(), 1))
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\prone_state.json', 'w'), indent=1); print('PRONE_STATE', R)
del w, pc, cmc, cap
