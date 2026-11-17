"""Lyra 에디터: 모든 InputMappingContext 중 LeftMouseButton 매핑이 있는 것과 그 액션/consume -> Data/lyra_lmb_scan.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_lmb_scan.json'
R = {'imcs': []}
try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/EnhancedInput', 'InputMappingContext'), True):
        imc = a.get_asset(); hits = []
        try:
            for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings'):
                if str(m.get_editor_property('key').get_editor_property('key_name')) in ('LeftMouseButton',):
                    ia = m.get_editor_property('action'); hits.append([ia.get_name() if ia else None, bool(ia.get_editor_property('consume_input')) if ia else None])
        except Exception as e: hits.append('err ' + str(e)[:60])
        if hits: R['imcs'].append({'imc': str(a.get_editor_property('package_name')), 'lmb': hits})
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_LMB_SCAN', len(R['imcs']), R.get('error', '')[-200:])
