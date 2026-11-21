"""Lyra 에디터(`py <파일>`): CR_FurinaSecondary 를 정식 컴파일(BlueprintEditorLibrary.compile_blueprint) 후 저장 (계층에 뼈 추가한 뒤 클래스 반영용).  -> Data/lyra_cr_compile.json"""
import unreal, json, traceback
R = {}
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary')
    try: unreal.BlueprintEditorLibrary.compile_blueprint(cr); R['compiled'] = True
    except Exception as e: R['compile_err'] = str(e)[:200]
    try: cr.recompile_vm(); R['vm'] = True
    except Exception as e: R['vm_err'] = str(e)[:200]
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
    gc = cr.generated_class() if hasattr(cr, 'generated_class') else None
    R['class'] = str(gc)
    try:
        cdo = unreal.get_default_object(gc); h = cdo.get_hierarchy() if hasattr(cdo, 'get_hierarchy') else None
        R['cdo_thumb3'] = [str(k.name) for k in h.get_all_keys() if 'Thumb3' in str(k.name)] if h else None
    except Exception as e: R['cdo_err'] = str(e)[:200]
except Exception: R['error'] = traceback.format_exc()[-700:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_compile.json', 'w', encoding='utf-8'), indent=1, default=str); print('LYRA_CR_COMPILE', R)
