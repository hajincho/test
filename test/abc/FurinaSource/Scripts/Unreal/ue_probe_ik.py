import unreal, json, os
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
res['ik_units'] = [n for n in dir(unreal) if n.startswith('RigUnit_') and ('TwoBone' in n or 'Trace' in n or 'BasicIK' in n)]
for n in ['RigUnit_TwoBoneIKSimplePerItem', 'RigUnit_SphereTraceWorld', 'RigUnit_SphereTraceByTraceChannel', 'RigUnit_MathQuaternionFromTwoVectors',
          'RigUnit_ToRigSpace_Location', 'RigUnit_MathVectorMake', 'RigUnit_MathFloatMin', 'RigUnit_MathFloatMax', 'RigUnit_MathFloatSub',
          'RigUnit_MathQuaternionSlerp', 'RigUnit_MathVectorAdd', 'RigUnit_SetTranslation', 'RigUnit_MathVectorFromFloat', 'RigUnit_MathFloatLerp']:
    try: res[n] = getattr(unreal, n)().export_text()
    except Exception as e: res[n] = 'ERR ' + repr(e)[:80]
json.dump(res, open(os.path.join(D, 'ue_probe_ik.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('PROBE_IK_DONE')
