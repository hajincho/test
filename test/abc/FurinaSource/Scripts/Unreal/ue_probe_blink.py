import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
for n in ['RigUnit_MathFloatFloor', 'RigUnit_MathFloatFrac', 'RigUnit_MathFloatMod', 'RigUnit_MathFloatSin', 'RigUnit_MathFloatSub',
          'RigUnit_MathFloatSmoothStep', 'RigUnit_GetCurveValue', 'RigUnit_SetCurveValue', 'RigUnit_AccumulateFloatAdd', 'RigUnit_MathFloatMin',
          'RigUnit_MathFloatAbs', 'RigUnit_MathFloatLess', 'RigUnit_MathFloatSelectBool', 'RigUnit_RandomFloat', 'RigUnit_MathFloatRound']:
    try: res[n] = getattr(unreal, n)().export_text()
    except Exception as e: res[n] = 'ERR ' + repr(e)[:80]
res['random'] = [n for n in dir(unreal) if n.startswith('RigUnit_') and 'Random' in n]
# is the IdleBlink morph actually driven by the curve? check curve metadata on mesh/skeleton
sk = unreal.load_asset('/Game/Furina/SK_Furina')
res['mesh_curve_api'] = [m for m in dir(sk) if 'curve' in m.lower() or 'morph' in m.lower()]
skel = sk.get_editor_property('skeleton')
res['skel_curve_api'] = [m for m in dir(skel) if 'curve' in m.lower() or 'morph' in m.lower()]
json.dump(res, open(os.path.join(D, 'ue_probe_blink.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('PROBE_BLINK_DONE')
