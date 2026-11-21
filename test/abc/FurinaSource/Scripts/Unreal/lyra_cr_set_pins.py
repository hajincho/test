"""헤드리스: CR_FurinaSecondary 핀 기본값 설정.  인자: <json 경로>   json = {"PistQw.B": "(X=..,Y=..,Z=..,W=..)", "PistRV.B": "(X=..,Y=..,Z=..)", ...}  -> 컴파일/저장"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; R = {'args': ARGS, 'set': {}}
try:
    P = json.load(open(ARGS[0], encoding='utf-8'))
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller()
    for pin, val in P.items(): R['set'][pin] = bool(c.set_pin_default_value(pin, val, True, False))
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(D + r'\lyra_cr_set_pins.json', 'w'), indent=1); print('LYRA_CR_SET_PINS', R.get('saved'), R.get('error', ''))
