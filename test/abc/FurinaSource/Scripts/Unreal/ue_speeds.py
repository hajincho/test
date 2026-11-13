import unreal, json, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
cdo = unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(bp))
cm = cdo.get_editor_property('character_movement')
r = {k: cm.get_editor_property(k) for k in ('max_walk_speed', 'max_acceleration', 'braking_deceleration_walking', 'jump_z_velocity')}
sk = unreal.load_asset('/Game/Furina/SK_Furina'); pose = sk.get_editor_property('skeleton').get_reference_pose()
r['pos'] = {}
for n in unreal.AnimPoseExtensions.get_bone_names(pose):
    n = str(n)
    if n.endswith(('_1_0', '_1_1', '_1_2', '_1_3', '_1_4', '_1_5', '_1_6', '_1_7', '_1_8')) or n in ('Hips', 'HB2_0_1', 'HB3_0_1', 'HB4_0_1', 'F_0_1_L', 'F_0_1_R', 'F_17_1_L', 'CF_1_L', 'CF_1_R', 'DM_0_1', 'DM_5_1', 'HB2_18_1', 'HB3_17_1', 'HB4_16_1', 'HB1_7_0', 'HB1_7_4'):
        t = unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD).translation
        r['pos'][n] = [round(t.x, 1), round(t.y, 1), round(t.z, 1)]
json.dump(r, open(os.path.join(S, 'ue_speeds.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('SPEEDS_DONE')
