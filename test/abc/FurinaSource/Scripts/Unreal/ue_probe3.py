import unreal, json, os, traceback
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
for n in ['AnimNode_SequencePlayer', 'AnimNode_TwoWayBlend', 'AnimNode_LayeredBoneBlend', 'AnimNode_ControlRig', 'InputBlendPose', 'BranchFilter']:
    try: res[n] = getattr(unreal, n)().export_text()
    except Exception as e: res[n] = 'ERR ' + repr(e)
res['cr_class'] = str(unreal.load_object(None, '/Game/Furina/CR_FurinaSecondary.CR_FurinaSecondary_C'))
json.dump(res, open(os.path.join(S, 'ue_probe3.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('PROBE3_DONE')
