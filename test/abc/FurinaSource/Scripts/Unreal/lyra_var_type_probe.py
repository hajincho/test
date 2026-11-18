"""Lyra 에디터(`py <파일>`): BlueprintEditorLibrary 의 변수 타입 관련 메서드와 get_basic_type_by_name 결과 확인 -> Data/lyra_var_type_probe.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_var_type_probe.json'
R = {'methods': [m for m in dir(unreal.BlueprintEditorLibrary) if 'variable' in m.lower() or 'type' in m.lower()]}
try:
    for n in ('float', 'real', 'double', 'int', 'bool', 'boolean', 'Float', 'Real'):
        try: t = unreal.BlueprintEditorLibrary.get_basic_type_by_name(n); R[n] = str(t)[:200]
        except Exception as e: R[n] = 'err ' + str(e)[:60]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('VAR_TYPE_PROBE')
