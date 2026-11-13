import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
for n in ['AnimNode_AnimDynamics', 'AnimPhysBodyDefinition', 'AnimPhysConstraintSetup', 'AnimPhysSphericalLimit', 'AnimNode_RetargetPoseFromMesh', 'AnimNode_ConvertLocalToComponentSpace', 'AnimNode_ConvertComponentToLocalSpace', 'AnimPhysPlanarLimit', 'RotationRetargetingInfo']:
    try:
        c = getattr(unreal, n)
        o = c()
        res[n] = dict(props=[p for p in dir(o) if not p.startswith('_') and p not in dir(unreal.StructBase)], text=o.export_text())
    except Exception:
        res[n] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_probe.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('PROBE_DONE')
