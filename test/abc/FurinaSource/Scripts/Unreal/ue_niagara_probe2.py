"""Finds where the NiagaraExt_* Python authoring API lives: classes with attributes matching add_emitter / topology / stack_input; dumps NiagaraExt_* class members -> Data/niagara_probe2.json"""
import unreal, json, re
R = {'hits': {}, 'ext': {}}
pat = re.compile('add_emitter|topology|stack_input|set_stack|niagara_ext|emitter_data|add_module|add_renderer|create_system|create_emitter', re.I)
for n in dir(unreal):
    c = getattr(unreal, n, None)
    if not isinstance(c, type): continue
    try: ms = [a for a in dir(c) if pat.search(a) and not a.startswith('_')]
    except Exception: continue
    if ms and 'Niagara' in n or (ms and any('niagara' in m.lower() or 'emitter' in m.lower() for m in ms)): R['hits'][n] = ms[:40]
    if n.startswith('NiagaraExt'):
        R['ext'][n] = [a for a in dir(c) if not a.startswith('_') and a not in dir(unreal.Object)][:50]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\niagara_probe2.json', 'w'), indent=1); print('NIAGARA_PROBE2', len(R['hits']), len(R['ext']))
