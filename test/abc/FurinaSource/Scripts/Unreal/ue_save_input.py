import unreal, json, os
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
for p in ['/Game/Furina/Input/IA_CameraZoom', '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC',
          '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP']:
    a = unreal.load_asset(p)
    res[p] = [str(a), unreal.EditorAssetLibrary.save_loaded_asset(a, False)]
res['pkg_ok'] = unreal.EditorLoadingAndSavingUtils.save_packages([unreal.load_asset('/Game/Furina/Input/IA_CameraZoom').get_outermost(),
    unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC').get_outermost()], False)
json.dump(res, open(os.path.join(D, 'ue_save_input.json'), 'w'), default=str, indent=1)
print('SAVE_INPUT_DONE')
