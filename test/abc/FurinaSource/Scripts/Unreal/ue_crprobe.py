import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    res['cr_classes'] = [n for n in dir(unreal) if n.startswith('RigUnit_') and any(k in n for k in ('Harmonic', 'Spring', 'Delta', 'Verlet', 'Accumulate', 'World', 'Time', 'Offset', 'SetTransform', 'GetTransform', 'Point', 'Sin', 'Rotat', 'Quaternion', 'FromAxis', 'Clamp', 'Remap', 'Length', 'Interp'))]
    res['factory'] = [n for n in dir(unreal) if 'ControlRig' in n and ('Factory' in n or 'Library' in n or 'Blueprint' in n)]
    for n in ['RigUnit_ChainHarmonicsPerItem', 'RigUnit_ChainHarmonics']:
        if hasattr(unreal, n):
            res[n] = getattr(unreal, n)().export_text()
    for n in ['RigVMController', 'ControlRigBlueprint', 'ControlRigBlueprintFactory']:
        if hasattr(unreal, n):
            res[n + '_methods'] = [m for m in dir(getattr(unreal, n)) if not m.startswith('_')]
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_crprobe.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('CRPROBE_DONE')
