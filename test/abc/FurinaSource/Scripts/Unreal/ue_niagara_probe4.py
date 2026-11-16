"""Inspects what can be edited from Python on template Niagara systems: system / emitter properties, renderer properties, exposed (user) parameters -> Data/niagara_probe4.json"""
import unreal, json
R = {}
def tryget(o, n):
    try: return str(o.get_editor_property(n))[:300]
    except Exception as e: return 'ERR ' + str(e)[:80]
for p in ('/Niagara/DefaultAssets/Templates/Systems/DirectionalBurst', '/Niagara/DefaultAssets/Templates/Systems/SimpleExplosion', '/Game/3DPlatformerGameBundle/NiagaraSystems/Sparks_FXS'):
    s = unreal.load_asset(p); d = {'class': str(s.get_class().get_name())}
    props = [a for a in dir(s) if not a.startswith('_') and a not in dir(unreal.Object)]
    d['attrs'] = props[:120]
    for n in ('emitter_handles', 'exposed_parameters', 'user_parameters', 'fixed_bounds', 'warmup_time', 'effect_type', 'system_spawn_script', 'system_update_script'): d[n] = tryget(s, n)
    try:
        hs = s.get_editor_property('emitter_handles'); d['n_handles'] = len(hs); d['handles'] = []
        for h in hs:
            hd = {'attrs': [a for a in dir(h) if not a.startswith('_')][:40]}
            try:
                em = h.get_editor_property('instance') if hasattr(h, 'get_editor_property') else None
            except Exception as e: em = None; hd['err'] = str(e)[:100]
            d['handles'].append(hd)
    except Exception as e: d['hderr'] = str(e)[:200]
    R[p] = d
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\niagara_probe4.json', 'w'), indent=1); print('NIAGARA_PROBE4')
