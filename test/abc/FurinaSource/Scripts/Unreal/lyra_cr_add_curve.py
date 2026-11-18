"""Lyra 에디터(`py <파일> <곡선이름...>`): CR_FurinaSecondary 의 릭 계층에 곡선 요소를 추가한다(컨트롤 릭의 GetCurveValue 는 릭에 등록된 곡선만 읽는다). 이미 있으면 건너뜀. 저장까지.
 (lyra_fp_handle_fade.py 가 읽는 HandleFp 가 등록 안 돼 있어 1인칭 보정이 꺼지지 않았다.)   -> Data/lyra_cr_add_curve.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_add_curve.json'
NAMES = [a for a in sys.argv[1:] if not a.endswith('.py')] or ['HandleFp']
R = {}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); h = cr.get_hierarchy()
    have = [str(k.name) for k in h.get_all_keys(True) if k.type == unreal.RigElementType.CURVE]; R['before'] = len(have)
    R['added'] = {}
    for n in NAMES:
        if n in have: R['added'][n] = 'exists'
        else: R['added'][n] = str(cr.get_hierarchy_controller().add_curve(n, 0.0, False))
    del h
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
    h2 = cr.get_hierarchy(); R['after'] = len([k for k in h2.get_all_keys(True) if k.type == unreal.RigElementType.CURVE]); R['has'] = [n for n in NAMES if n in [str(k.name) for k in h2.get_all_keys(True) if k.type == unreal.RigElementType.CURVE]]
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CR_ADD_CURVE', R.get('has'), R.get('error', '')[-200:])
import gc; gc.collect()
