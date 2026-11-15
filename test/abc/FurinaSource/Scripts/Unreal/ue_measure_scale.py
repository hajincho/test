"""Measures Furina's height (mesh bounds, Head bone top) and the rifle length in UE units, plus locomotion anim lengths -> Data/measure_scale.json"""
import unreal, json
def main():
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        o = lib.get_associated_object(lib.get_data(h))
        if isinstance(o, unreal.SkeletalMeshComponent) and o.get_name().startswith(('FurinaMesh', 'FurinaRifle')):
            sm = o.get_editor_property('skeletal_asset') if hasattr(o, 'skeletal_asset') else o.get_editor_property('skeletal_mesh')
            b = sm.get_bounds()
            R[o.get_name()] = dict(mesh=sm.get_name(), comp_scale=str(o.get_editor_property('relative_scale3d')),
                                   origin=[round(v, 1) for v in b.origin.to_tuple()], extent=[round(v, 1) for v in b.box_extent.to_tuple()])
            ib = sm.get_editor_property('imported_bounds') if hasattr(sm, 'imported_bounds') else None
            if ib: R[o.get_name()]['imported'] = [[round(v, 1) for v in ib.origin.to_tuple()], [round(v, 1) for v in ib.box_extent.to_tuple()]]
        del o
    del bp
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in reg.get_assets_by_path('/Game/Furina', recursive=True):
        if str(a.asset_class_path.asset_name) == 'AnimSequence' and any(k in str(a.asset_name) for k in ('Run', 'Walk', 'Sprint')):
            seq = unreal.load_asset(str(a.package_name))
            R.setdefault('anims', {})[str(a.package_name)] = round(seq.get_play_length(), 3)
            del seq
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\measure_scale.json', 'w'), indent=1, default=str)
    print('MEASURE_SCALE', R)
main(); del main
