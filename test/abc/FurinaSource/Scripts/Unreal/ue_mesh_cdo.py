"""Editor: skinned asset of the FurinaMesh component on (a) the BP's class default object, (b) the SCS template, (c) the level instance; optional arg 'fix' sets the CDO + instance via
set_skinned_asset_and_update / set_editor_property and saves. -> Data/mesh_cdo.json"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
def name(a): return a.get_path_name() if a else None
def main():
    R = {}
    bp = unreal.load_asset(CH); cdo = unreal.get_default_object(bp.generated_class()); saori = unreal.load_asset('/Game/Saori/SK_Saori')
    c = cdo.get_editor_property('FurinaMesh'); R['cdo'] = name(c.get_editor_property('skinned_asset')) if c else 'no component on the CDO'
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    inst = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, bp.generated_class())][0]
    ic = inst.get_editor_property('FurinaMesh'); R['instance'] = name(ic.get_editor_property('skinned_asset')); R['instance_class'] = inst.get_class().get_path_name()
    R['instance_archetype'] = str(ic.get_archetype().get_path_name()) if hasattr(ic, 'get_archetype') else None
    if len(sys.argv) > 1 and sys.argv[1] == 'fix':
        ic.set_skinned_asset_and_update(saori); R['inst_after_set'] = name(ic.get_editor_property('skinned_asset'))
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
        R['inst_after_compile'] = name(unreal.GameplayStatics.get_all_actors_of_class(w, bp.generated_class())[0].get_editor_property('FurinaMesh').get_editor_property('skinned_asset'))
        R['level_saved'] = unreal.EditorLevelLibrary.save_current_level()
    json.dump(R, open(D + r'\mesh_cdo.json', 'w'), indent=1); print('MESH_CDO', R)
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(D + r'\mesh_cdo.json', 'w'))
