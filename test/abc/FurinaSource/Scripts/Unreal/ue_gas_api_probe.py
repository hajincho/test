"""Editor: GAS Python/BP API 존재 확인 + BlueprintEditorLibrary/BlueprintGraphEditor 타입 헬퍼 -> Data/gas_api_probe.json"""
import unreal, json, traceback
R = {}
try:
    R['gas_loaded'] = hasattr(unreal, 'AbilitySystemBlueprintLibrary')
    for cls in ('AbilitySystemBlueprintLibrary', 'AbilitySystemComponent', 'GameplayEffect', 'GameplayAbilityTargetDataHandle'):
        c = getattr(unreal, cls, None)
        if c: R[cls] = [m for m in dir(c) if not m.startswith('_') and any(k in m.lower() for k in ('spec', 'effect', 'tag', 'event', 'asc', 'ability_system', 'target', 'magnitude', 'context', 'hit'))][:60]
    R['BlueprintEditorLibrary'] = [m for m in dir(unreal.BlueprintEditorLibrary) if not m.startswith('_')]
    ed = unreal.BlueprintGraphEditor
    R['GraphEditor'] = [m for m in dir(ed) if not m.startswith('_')]
    R['SoftClass'] = hasattr(unreal, 'SoftClassPath')
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\gas_api_probe.json', 'w'), indent=1)
print('GAS_API', R.get('gas_loaded'), R.get('error', '')[-200:])
