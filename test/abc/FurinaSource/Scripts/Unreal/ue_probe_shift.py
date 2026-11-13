"""Probe: what is bound to Left Shift (IMC mappings) and which BP graphs use those actions."""
import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    for prop in ('mappings', 'default_key_mappings'):
        try:
            v = imc.get_editor_property(prop)
            res[prop] = str(v)[:3000]
        except Exception as e: res[prop] = repr(e)
    try:
        dkm = imc.get_editor_property('default_key_mappings')
        res['dkm_list'] = [(str(m.key.get_editor_property('key_name')), m.action.get_path_name() if m.action else None) for m in dkm.get_editor_property('mappings')]
    except Exception as e: res['dkm_err'] = repr(e)
    # which assets reference Sprint_IA
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in unreal.EditorAssetLibrary.list_assets('/Game', True, False):
        n = a.split('.')[-1]
        if 'Sprint' in n or 'Dash' in n and n.endswith('IA'):
            p = a.split('.')[0]
            res.setdefault('ia', []).append(p)
            opts = unreal.AssetRegistryDependencyOptions(True, True, True, True, True)
            res['refs ' + p] = [str(x) for x in ar.get_referencers(p, opts)]
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(D, 'ue_probe_shift.json'), 'w', encoding='utf-8'), indent=1, default=str)
print('PROBE_SHIFT_DONE')
