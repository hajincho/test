"""Probe: which locomotion anims does the Manny ABP use (blend space samples), and the curves on them."""
import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    eal = unreal.EditorAssetLibrary
    for p in eal.list_assets('/Game', True, False):
        p = p.split('.')[0]
        if str(eal.find_asset_data(p).asset_class_path.asset_name) in ('BlendSpace', 'BlendSpace1D'):
            bs = unreal.load_asset(p)
            samples = []
            try:
                for s in bs.get_editor_property('sample_data'):
                    an = s.get_editor_property('animation')
                    samples.append([an.get_path_name() if an else None, s.get_editor_property('sample_value').to_tuple()])
            except Exception as e: samples = repr(e)
            res[p] = samples
    for p in set(x[0].split('.')[0] for v in res.values() if isinstance(v, list) for x in v if x[0]):
        a = unreal.load_asset(p)
        res['curves ' + p] = [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(a, unreal.RawCurveTrackTypes.RCT_FLOAT)]
    cdo = unreal.get_default_object(unreal.load_asset('/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter').generated_class()) if unreal.EditorAssetLibrary.does_asset_exist('/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter') else None
    res['cdo'] = str(cdo)
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(D, 'ue_probe_bs.json'), 'w', encoding='utf-8'), indent=1, default=str)
print('PROBE_BS_DONE')
