"""Lists the Niagara Python API (unreal.Niagara*), whether the Niagara plugin / engine template emitters are available -> Data/niagara_probe.json"""
import unreal, json
R = {'classes': sorted(n for n in dir(unreal) if 'niagara' in n.lower())}
for cn in ('NiagaraSystem', 'NiagaraEmitter', 'NiagaraFunctionLibrary', 'NiagaraEditorLibrary', 'NiagaraSystemFactoryNew', 'NiagaraComponent', 'NiagaraEditorUtilities'):
    c = getattr(unreal, cn, None)
    if c: R[cn] = [a for a in dir(c) if not a.startswith('_')]
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for root in ('/Niagara', '/Game'):
    try:
        f = unreal.ARFilter(class_names=['NiagaraSystem', 'NiagaraEmitter'] if hasattr(unreal, 'ARFilter') else [], package_paths=[root], recursive_paths=True)
        R['assets_' + root] = [str(a.package_name) + ' ' + str(a.asset_class_path.asset_name) for a in ar.get_assets(f)][:80]
    except Exception as e: R['assets_' + root] = 'err ' + str(e)
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\niagara_probe.json', 'w'), indent=1); print('NIAGARA_PROBE', len(R['classes']))
