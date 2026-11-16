"""Lists unreal.RigUnit_* classes whose name matches argv substrings and their editor properties -> Data/rigunit_find.json"""
import unreal, json, sys
keys = [k.lower() for k in sys.argv[1:]] or ['addbone']
R = {}
for n in dir(unreal):
    if n.startswith('RigUnit') and any(k in n.lower() for k in keys):
        c = getattr(unreal, n)
        try: R[n] = [a for a in dir(c) if not a.startswith('_') and a not in dir(unreal.Object)][:40]
        except Exception as e: R[n] = str(e)
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\rigunit_find.json', 'w'), indent=1); print('RIGUNIT_FIND', len(R))
