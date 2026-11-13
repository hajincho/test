import unreal, json, os
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
arm = pawn.get_components_by_class(unreal.SpringArmComponent)[0]
out = os.path.join(D, 'ue_armlen.json')
hist = json.load(open(out)) if os.path.exists(out) else []
hist.append(arm.get_editor_property('target_arm_length'))
json.dump(hist, open(out, 'w'))
print('ARMLEN', hist[-1])
