import unreal, json, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
eal = unreal.EditorAssetLibrary
r = {'furina': eal.save_directory('/Game/Furina', only_if_is_dirty=True, recursive=True)}
for p in ['/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP',
          '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/GrindRailCharacterBP/Ver_2_ThirdPersonCharacter_BP',
          '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/HomingAttackCharacterBP/ThirdPersonCharacter_BP',
          '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/JumpPadCharacterBP/ThirdPersonCharacter_BP']:
    r[p] = eal.save_asset(p, only_if_is_dirty=True)
dirty = [str(p.get_name()) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()] + [str(p.get_name()) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
r['still_dirty'] = dirty
json.dump(r, open(os.path.join(S, 'ue_saveall.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('SAVE_DONE')
