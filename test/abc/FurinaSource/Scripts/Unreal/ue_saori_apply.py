"""Switches the player character (ThirdPersonCharacter_BP, component FurinaMesh) from SK_Furina to /Game/Saori/SK_Saori and scales the mesh component so Saori is HEIGHT cm tall (head top, halo excluded):
SK_Saori is bound to the Furina skeleton (Furina proportions: 149.6 cm from sole to head top), so a uniform component scale of HEIGHT / 149.6 is used (children - rifle, FP camera socket - scale with it).
Also applies the level instances. usage: py ue_saori_apply.py [height_cm] [mesh: saori|furina]   -> Data/saori_apply.json"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
BASE_HEIGHT = 149.6          # Saori sole -> head top at the Furina skeleton scale (build_saori_on_furina.py: -2.09 .. 147.53 cm)
def main():
    R = {}
    height = float(sys.argv[1]) if len(sys.argv) > 1 else 167.0
    which = sys.argv[2] if len(sys.argv) > 2 else 'saori'
    E = unreal.EditorAssetLibrary
    mesh = unreal.load_asset('/Game/Saori/SK_Saori' if which == 'saori' else '/Game/Furina/SK_Furina'); assert mesh
    scale = height / BASE_HEIGHT if which == 'saori' else 1.0; R['scale'] = scale
    bp = unreal.load_asset(CH)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    comp = None
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        if str(lib.get_variable_name(lib.get_data(h))) == 'FurinaMesh': comp = lib.get_object(lib.get_data(h))      # the SCS template (get_associated_object is not what the compile uses)
    assert comp, 'FurinaMesh not found'
    R['before'] = str(comp.get_editor_property('skeletal_mesh_asset').get_name()) if comp.get_editor_property('skeletal_mesh_asset') else None
    comp.set_editor_property('skeletal_mesh_asset', mesh)       # the real (serialized) property; 'skinned_asset' is only the base-class view of it
    t = comp.get_editor_property('relative_scale3d'); R['scale_before'] = str(t)
    comp.set_editor_property('relative_scale3d', unreal.Vector(scale, scale, scale))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = E.save_loaded_asset(bp, False)
    R['after'] = str(comp.get_editor_property('skeletal_mesh_asset').get_name())
    # level instances of the character
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); R['instances'] = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, bp.generated_class()):
        for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
            if c.get_name() == 'FurinaMesh':
                # the level instance had its own override of the mesh asset: clear it so the instance follows the Blueprint template (set it explicitly if the reset does not take)
                try: c.reset_editor_property('skeletal_mesh_asset')
                except Exception as e: R['reset_err'] = str(e)[:100]
                if c.get_editor_property('skeletal_mesh_asset') != mesh: c.set_editor_property('skeletal_mesh_asset', mesh)
                R['instances'].append(dict(actor=a.get_name(), mesh=str(c.get_editor_property('skinned_asset').get_name()), scale=str(c.get_editor_property('relative_scale3d'))))
    try: R['level_saved'] = unreal.EditorLevelLibrary.save_current_level()
    except Exception as e: R['level_saved'] = 'ERR ' + str(e)[:100]
    del comp, bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\saori_apply.json', 'w'), indent=1); print('SAORI_APPLY', R)
