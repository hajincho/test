"""Editor(Lyra): AS/AM_Furina_FP_Reload 의 ReloadLX/LY/LZ/MagState 키가 Data/reload_curves_new.json 과 일치하는지 확인 -> Data/lyra_reload_verify.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
R = {}
try:
    c = json.load(open(D + r'\reload_curves_new.json')); AL = unreal.AnimationLibrary
    exp = {'ReloadLX': (c['times'], c['LX']), 'ReloadLY': (c['times'], c['LY']), 'ReloadLZ': (c['times'], c['LZ']), 'MagState': ([k[0] for k in c['magstate']], [float(k[1]) for k in c['magstate']])}
    for name in ('AS_Furina_FP_Reload', 'AM_Furina_FP_Reload'):
        a = unreal.load_asset('/Game/Furina/FP/Anim/' + name); R[name] = {}
        for cn, (tt, vv) in exp.items():
            t, v = AL.get_float_keys(a, cn)
            R[name][cn] = {'keys': len(t), 'expected': len(tt), 'max_err': round(max(abs(x - y) for x, y in zip(sorted(zip(t, v)), sorted(zip(tt, vv)))[0:0] or [(0, 0)]), 4) if False else None}
            pairs = sorted(zip([float(x) for x in t], [float(x) for x in v])); exp_pairs = sorted(zip(tt, vv))
            err = 0.0
            if len(pairs) == len(exp_pairs):
                err = max(max(abs(p[0] - e[0]), abs(p[1] - e[1])) for p, e in zip(pairs, exp_pairs))
            R[name][cn]['max_err'] = round(err, 4); R[name][cn]['first'] = pairs[:2]; R[name][cn]['last'] = pairs[-2:]
        del a
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\lyra_reload_verify.json', 'w'), indent=1, default=str); print('LYRA_RELOAD_VERIFY', R.get('error', 'ok')[-300:])
