"""Finds classes having methods about emitters / stack inputs / modules (Niagara authoring API entry point) -> Data/niagara_probe3.json"""
import unreal, json, re
pat = re.compile('emitter|stack_input|niagara_system|module', re.I)
R = {}
for n in dir(unreal):
    c = getattr(unreal, n, None)
    if not isinstance(c, type) or n.startswith('MovieScene'): continue
    try: ms = [a for a in dir(c) if pat.search(a) and not a.startswith('_') and a not in dir(unreal.Object)]
    except Exception: continue
    if ms and ('Niagara' in n or 'Library' in n or 'Subsystem' in n or 'Utilit' in n or 'Scripting' in n): R[n] = ms[:60]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\niagara_probe3.json', 'w'), indent=1); print('NIAGARA_PROBE3', len(R))
