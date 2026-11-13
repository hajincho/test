import unreal, json, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
ar = unreal.AssetRegistryHelpers.get_asset_registry()
opt = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
res = {}
for p in ['/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/Manny_AnimBlueprint',
          '/Game/3DPlatformerGameBundle/Animations/AnimationBlueprints/Platformer_AnimBlueprint',
          '/Game/3DPlatformerGameBundle/Animations/AnimationBlueprints/Grind_Rail_AnimBlueprint',
          '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP',
          '/Game/3DPlatformerGameBundle/Blueprints/Components/Platformer_Component_BP']:
    res[p] = [str(d) for d in ar.get_dependencies(p, opt) or []]
idle = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/Idle_Anim'
res['idle_referencers'] = [str(d) for d in ar.get_referencers(idle, opt) or []]
seq = unreal.load_asset(idle)
res['idle_len'] = seq.get_play_length()
res['idle_curves'] = [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(seq, unreal.RawCurveTrackTypes.RCT_FLOAT)]
json.dump(res, open(os.path.join(S, 'ue_deps.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('DEPS_DONE')
