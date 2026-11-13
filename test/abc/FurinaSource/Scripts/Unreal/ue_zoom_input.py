"""Creates IA_CameraZoom (mouse wheel, Axis1D), maps it in Default_IMC, opens the character BP."""
import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
eal = unreal.EditorAssetLibrary
try:
    p = '/Game/Furina/Input/IA_CameraZoom'
    if eal.does_asset_exist(p):
        ia = unreal.load_asset(p)
    else:
        ia = unreal.AssetToolsHelpers.get_asset_tools().create_asset('IA_CameraZoom', '/Game/Furina/Input', unreal.InputAction, unreal.InputAction_Factory() if hasattr(unreal, 'InputAction_Factory') else None)
    ia.set_editor_property('value_type', unreal.InputActionValueType.AXIS1D)
    eal.save_asset(p)
    imcp = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC'
    imc = unreal.load_asset(imcp)
    key = unreal.Key(); key.set_editor_property('key_name', 'MouseWheelAxis')
    existing = [m for m in imc.get_editor_property('mappings') if m.action == ia]
    if not existing:
        imc.map_key(ia, key)
    eal.save_asset(imcp)
    res['mappings'] = [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None) for m in imc.get_editor_property('mappings')]
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([bp])
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(D, 'ue_zoom_input.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('ZOOM_INPUT_DONE')
