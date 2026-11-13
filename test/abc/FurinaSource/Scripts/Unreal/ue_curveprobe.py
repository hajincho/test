import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    bp = unreal.load_asset('/Game/Furina/CR_FurinaSecondary')
    h = bp.get_hierarchy()
    keys = [k for k in h.get_all_keys(True) if k.type == unreal.RigElementType.CURVE]
    res['cr_curves'] = [str(k.name) for k in keys][:200]
    res['cr_curve_count'] = len(keys)
    hc = bp.get_hierarchy_controller()
    res['hc_methods'] = [m for m in dir(hc) if 'curve' in m.lower() or 'import' in m.lower()]
    seq = unreal.load_asset('/Game/Furina/Anim/AS_Furina_Idle')
    res['idle_curves'] = [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(seq, unreal.RawCurveTrackTypes.RCT_FLOAT)]
    sk = unreal.load_asset('/Game/Furina/SK_Furina')
    res['morph_names'] = [str(m) for m in sk.get_all_morph_target_names()][:80] if hasattr(sk, 'get_all_morph_target_names') else None
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(D, 'ue_curveprobe.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('CURVEPROBE_DONE')
