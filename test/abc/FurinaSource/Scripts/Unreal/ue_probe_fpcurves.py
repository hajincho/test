import unreal, json
def main():
    R = {}
    for p in ('/Game/Furina/FP/Anim/AS_Furina_FP_Fire', '/Game/Furina/FP/Anim/AS_Furina_FP_Reload', '/Game/Furina/FP/Anim/AM_Furina_FP_Fire', '/Game/Furina/FP/Anim/AM_Furina_FP_Reload'):
        a = unreal.load_asset(p)
        try: R[p] = [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(a, unreal.RawCurveTrackTypes.RCT_FLOAT)]
        except Exception as e: R[p] = repr(e)[:150]
        if 'AS_' in p:
            try:
                n = R[p][0] if R[p] else None
                if n: R[p + ' keys'] = str(unreal.AnimationLibrary.get_float_keys(a, n))[:300]
            except Exception as e: R[p + ' keys'] = repr(e)[:150]
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_curves.json', 'w'), indent=1)
    print('FP_CURVES_DONE')
main()
del main
