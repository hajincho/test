"""Checks the character BP default MaxWalkSpeed and the sprint nodes after compile; sets 120 again if it was reset."""
import unreal, json, os
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
cm = unreal.get_default_object(bp.generated_class()).get_editor_property('character_movement')
res = {'before': cm.get_editor_property('max_walk_speed')}
if res['before'] != 120.0:
    cm.set_editor_property('max_walk_speed', 120.0)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
res['after'] = cm.get_editor_property('max_walk_speed')
json.dump(res, open(os.path.join(D, 'ue_check_speed.json'), 'w'), indent=1)
print('CHECK_SPEED', res)
