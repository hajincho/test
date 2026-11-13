import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    ia = unreal.load_asset('/Game/Furina/Input/IA_CameraZoom')
    res['class'] = ia.get_class().get_name()
    res['value_type_before'] = str(ia.get_editor_property('value_type'))
    ia.set_editor_property('value_type', unreal.InputActionValueType.AXIS1D)
    unreal.EditorAssetLibrary.save_asset('/Game/Furina/Input/IA_CameraZoom')
    res['value_type_after'] = str(ia.get_editor_property('value_type'))
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    dk = imc.get_editor_property('default_key_mappings')
    res['dk_props'] = [p for p in dir(dk) if not p.startswith('_')][:40]
    try:
        ms = dk.get_editor_property('mappings')
        res['dk_mappings'] = [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None) for m in ms]
    except Exception as e: res['dk_err'] = repr(e)
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(D, 'ue_zoom_check.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('ZOOM_CHECK_DONE')
