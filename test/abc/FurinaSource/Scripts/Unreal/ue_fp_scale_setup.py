"""Rifle at real size: FurinaRifle relative transform (gun in right wrist) and scale from Data/fp_rig.json (scale 1.0);
FPCamera gets the tag 'FurinaFPCamera' (ABP_Furina reads it for the ViewTP curve)."""
import unreal, json
def main():
    FR = json.load(open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_rig.json'))
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    hs = {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    rifle = lib.get_associated_object(lib.get_data(hs['FurinaRifle']))
    q = FR['gun_in_rw_q']
    rifle.set_editor_property('relative_location', unreal.Vector(*FR['gun_in_rw_t']))
    rifle.set_editor_property('relative_rotation', unreal.Quat(q[0], q[1], q[2], q[3]).rotator())
    rifle.set_editor_property('relative_scale3d', unreal.Vector(FR['scale'], FR['scale'], FR['scale']))
    R['rifle'] = [str(rifle.get_editor_property('relative_location')), str(rifle.get_editor_property('relative_scale3d'))]
    cam = lib.get_associated_object(lib.get_data(hs['FPCamera']))
    cam.set_editor_property('component_tags', ['FurinaFPCamera'])
    del rifle, cam
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status')); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_scale_setup.json', 'w'), indent=1)
    print('FP_SCALE_SETUP', R)
main(); del main
