"""Lyra 에디터(`py <파일> [부분문자열]`): CR_FurinaSecondary 의 리그 계층에서 이름에 부분문자열(기본 Thumb)이 들어간 뼈를 나열.  -> Data/lyra_cr_has_bone.json"""
import unreal, json, sys, traceback
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; KEY = ARGS[0] if ARGS else 'Thumb'
R = {'key': KEY}
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary')
    h = None
    for nm in ('get_hierarchy', 'hierarchy'):
        try:
            h = getattr(cr, nm); h = h() if callable(h) else h; break
        except Exception as e: R.setdefault('err', []).append(nm + ':' + str(e)[:80])
    R['hier'] = str(type(h))
    keys = h.get_all_keys() if h is not None else []
    R['n_keys'] = len(keys)
    R['match'] = [str(k.name) for k in keys if KEY.lower() in str(k.name).lower()]
except Exception: R['error'] = traceback.format_exc()[-700:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_has_bone.json', 'w', encoding='utf-8'), indent=1, default=str); print('LYRA_CR_HAS_BONE', R.get('n_keys'), R.get('error', ''))
