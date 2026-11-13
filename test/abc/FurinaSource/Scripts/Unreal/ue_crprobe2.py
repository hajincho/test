import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
for n in ['RigUnit_GetTransform', 'RigUnit_ToWorldSpace_Location', 'RigUnit_DeltaFromPreviousVector', 'RigUnit_GetDeltaTime',
          'RigUnit_MathVectorLength', 'RigUnit_MathFloatDiv', 'RigUnit_MathFloatMax', 'RigUnit_MathFloatRemap', 'RigUnit_AccumulateFloatLerp',
          'RigUnit_MathFloatMul', 'RigUnit_MathVectorMake', 'RigUnit_MathVectorScale', 'RigUnit_MathQuaternionFromAxisAndAngle', 'RigUnit_MathQuaternionMul',
          'RigUnit_SetRotation', 'RigUnit_SetTransform', 'RigUnit_MathFloatSin', 'RigUnit_GetCurveValue', 'RigUnit_ToRigSpace_Location',
          'RigUnit_MathVectorFromFloat', 'RigUnit_MathVectorAdd', 'RigUnit_MathFloatAdd', 'RigUnit_MathFloatClamp', 'RigUnit_AccumulateVectorLerp',
          'RigUnit_MathQuaternionRotateVector', 'RigUnit_ToRigSpace_Rotation', 'RigUnit_ToWorldSpace_Rotation', 'RigUnit_MathVectorSub', 'RigUnit_MathVectorClampLength']:
    try: res[n] = getattr(unreal, n)().export_text()
    except Exception as e: res[n] = 'ERR ' + repr(e)
q = unreal.Quat();
try:
    q = unreal.Quat.from_axis_and_angle if hasattr(unreal.Quat, 'from_axis_and_angle') else None
except Exception: pass
try:
    qq = unreal.MathLibrary.quat_make_from_euler(unreal.Vector(30, 0, 0))
    res['euler_roll30_rot_down'] = str(unreal.MathLibrary.quat_rotate_vector(qq, unreal.Vector(0, 0, -1)))
    r = unreal.Rotator(roll=30, pitch=0, yaw=0)
    res['rotator_roll30'] = str(r.rotate_vector(unreal.Vector(0, 0, -1)))
except Exception as e: res['quat'] = repr(e)
json.dump(res, open(os.path.join(S, 'ue_crprobe2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('CRPROBE2_DONE')
