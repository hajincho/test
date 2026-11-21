"""헤드리스: CR_FurinaSecondary 의 PgK_<뼈>.Value 를 consts json 값으로 설정.  인자: <consts_json> <R|L|RL>
 consts_json: {'consts': {뼈: [x,y,z,w]}} 또는 lyra_pistol_twitch_probe_<태그>.json (consts 키)"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; CJ = ARGS[0]; HANDS = ARGS[1] if len(ARGS) > 1 else 'RL'
R = {'args': ARGS, 'set': []}
try:
    C = json.load(open(CJ, encoding='utf-8')); C = C.get('consts', C)
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller()
    for bn, q in C.items():
        if bn[-1] not in HANDS: continue
        c.set_pin_default_value('PgK_%s.Value' % bn, '(X=%.7f,Y=%.7f,Z=%.7f,W=%.7f)' % tuple(q), True, False); R['set'].append(bn)
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(D + r'\lyra_cr_pistol_consts_set.json', 'w'), indent=1); print('LYRA_CR_CONSTS_SET', R.get('saved'), R.get('error', ''))
