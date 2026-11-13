"""Left Shift = Furina sprint only. The bundle's Sprint_IA (ground: crouch-charge dash, rail: speed boost) moves from
Left Shift to Left Ctrl on keyboard; its gamepad button stays."""
import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    imcp = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC'
    imc = unreal.load_asset(imcp)
    ia = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Actions/Sprint_IA')
    def key(n): k = unreal.Key(); k.set_editor_property('key_name', n); return k
    def listing(): return [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None)
                           for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    if ('LeftShift', 'Sprint_IA') in listing():
        imc.unmap_key(ia, key('LeftShift'))
    if ('LeftControl', 'Sprint_IA') not in listing():
        imc.map_key(ia, key('LeftControl'))
    unreal.EditorAssetLibrary.save_loaded_asset(imc, False)
    res['mappings'] = listing()
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(D, 'ue_shift_remap.json'), 'w'), indent=1)
print('SHIFT_REMAP_DONE')
