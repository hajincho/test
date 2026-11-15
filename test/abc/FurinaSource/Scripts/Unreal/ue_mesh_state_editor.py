"""Editor (not PIE): FurinaMesh skinned asset of the BP class default object (SCS template) and of every level instance; plus which assets reference SK_Furina -> Data/mesh_state_editor.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
def main():
    R = {}
    bp = unreal.load_asset(CH)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        n = str(lib.get_variable_name(lib.get_data(h)))
        if n == 'FurinaMesh':
            c = lib.get_associated_object(lib.get_data(h)); a = c.get_editor_property('skinned_asset'); R['template'] = dict(asset=a.get_path_name() if a else None, scale=str(c.get_editor_property('relative_scale3d')))
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); R['instances'] = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, bp.generated_class()):
        for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
            if c.get_name() == 'FurinaMesh': x = c.get_editor_property('skinned_asset'); R['instances'].append(dict(actor=a.get_name(), asset=x.get_path_name() if x else None, scale=str(c.get_editor_property('relative_scale3d'))))
    R['world'] = w.get_path_name()
    R['refs_to_SK_Furina'] = [str(x) for x in unreal.EditorAssetLibrary.find_package_referencers_for_asset('/Game/Furina/SK_Furina', False)][:30] if hasattr(unreal.EditorAssetLibrary, 'find_package_referencers_for_asset') else 'n/a'
    json.dump(R, open(D + r'\mesh_state_editor.json', 'w'), indent=1); print('MESH_EDITOR', R)
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(D + r'\mesh_state_editor.json', 'w'))
