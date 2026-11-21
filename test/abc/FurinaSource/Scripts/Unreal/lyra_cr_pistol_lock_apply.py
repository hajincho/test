"""헤드리스 가능: UnrealEditor-Cmd.exe <uproject> -run=pythonscript -script="<이 파일> <consts_json> <firm_json> <out_consts_json>"
 consts_json : lyra_pistol_twitch_probe_<태그>.json (consts: 뼈 -> 부모 기준 로컬 쿼터니언 [x,y,z,w]) 또는 이전 단계의 out_consts_json({'consts':...})
 firm_json   : Data/pistol_grip_firm_<태그>.json (fingers[*].dq: 뼈 -> 로컬 델타 쿼터니언)
 새 상수 = 이전 상수 x dq (로컬 곱), 정규화.  CR_FurinaSecondary 의 기존 PgK_<뼈>.Value 핀 값만 갱신(노드 생성 없음) -> 컴파일/저장.   out_consts_json 에 새 상수 기록."""
import unreal, json, sys, math, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]
CJ, FJ, OJ = ARGS[0], ARGS[1], ARGS[2]
R = {'args': ARGS, 'changed': []}
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return [aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz]
try:
    C = json.load(open(CJ, encoding='utf-8')); C = C.get('consts', C); F = json.load(open(FJ, encoding='utf-8'))
    new = dict(C)
    for key, v in F['fingers'].items():
        for bn, dq in v['dq'].items():
            if bn not in C: continue
            q = qmul(C[bn], dq); n = math.sqrt(sum(x * x for x in q)); q = [x / n for x in q]
            if q[3] < 0: q = [-x for x in q]
            new[bn] = q; R['changed'].append(bn)
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller()
    for bn in R['changed']:
        q = new[bn]; c.set_pin_default_value('PgK_%s.Value' % bn, '(X=%.7f,Y=%.7f,Z=%.7f,W=%.7f)' % tuple(q), True, False)
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
    json.dump({'consts': new}, open(OJ, 'w'), indent=1)
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(D + r'\lyra_cr_pistol_lock_apply.json', 'w'), indent=1); print('LYRA_CR_LOCK_APPLY', R.get('saved'), R.get('error', ''))
