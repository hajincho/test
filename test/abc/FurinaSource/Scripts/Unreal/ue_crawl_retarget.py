"""Retargets the 10 animations of the purchased 'Free Crawl Animation' pack (Content/Free_Crawl_Animation, UE5 Manny skeleton SK_Mannequin) to Furina:
IK rig IK_CrawlManny (copy of IK_TFPManny with the pack's mesh as source), retargeter RTG_CrawlToFurina (copy of RTG_TFPToFurina), output /Game/Furina/Crawl/AS_Furina_Crawl_*.
Writes Data/crawl_retarget.json (asset list, lengths, root motion flags). usage: py ue_crawl_retarget.py"""
import unreal, json, os, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools(); dest = '/Game/Furina/Crawl'
    source = None
    for p in ('/Game/Free_Crawl_Animation/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple', '/Game/Free_Crawl_Animation/Demo/Characters/Mannequins/Meshes/SK_Mannequin'):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.SkeletalMesh): source = a; R['source'] = p; break
    assert source, 'no source mesh'
    target = unreal.load_asset('/Game/Furina/SK_Furina')
    R['skeleton'] = str(source.get_editor_property('skeleton').get_path_name())
    p = dest + '/IK_CrawlManny'
    rig = unreal.load_asset(p) if E.does_asset_exist(p) else T.duplicate_asset('IK_CrawlManny', dest, unreal.load_asset('/Game/Furina/TFP/IK_TFPManny'))
    unreal.IKRigController.get_controller(rig).set_skeletal_mesh(source); E.save_loaded_asset(rig, False)
    p = dest + '/RTG_CrawlToFurina'
    rtg = unreal.load_asset(p) if E.does_asset_exist(p) else T.duplicate_asset('RTG_CrawlToFurina', dest, unreal.load_asset('/Game/Furina/TFP/RTG_TFPToFurina'))
    c = unreal.IKRetargeterController.get_controller(rtg); c.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, rig); c.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, source)
    c.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, rig); E.save_loaded_asset(rtg, False)
    paths = E.list_assets('/Game/Free_Crawl_Animation/Animations', True, False)
    items = [E.find_asset_data(p) for p in paths if isinstance(unreal.load_asset(p), unreal.AnimSequence)]
    R['source_anims'] = [str(i.asset_name) for i in items]
    out = unreal.IKRetargetBatchOperation.duplicate_and_retarget(items, source, target, rtg, search='anim_', replace='AS_Furina_Crawl_', target_path=dest, use_source_path=False, include_referenced_assets=True, overwrite_existing_files=True)
    R['assets'] = []
    for a in out:
        E.save_asset(str(a.package_name)); an = unreal.load_asset(str(a.package_name))
        if isinstance(an, unreal.AnimSequence):
            R['assets'].append(dict(name=an.get_name(), length=round(an.get_editor_property('sequence_length'), 3), root_motion=bool(an.get_editor_property('enable_root_motion')), rate_scale=an.get_editor_property('rate_scale')))
    R['ok'] = len(R['assets']) >= 8
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'crawl_retarget.json'), 'w'), indent=1); print('CRAWL_RETARGET', R.get('ok'), R.get('error', '')[-400:])
