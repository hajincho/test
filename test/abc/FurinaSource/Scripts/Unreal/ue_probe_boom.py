"""Dumps ThirdPersonCharacter_BP camera boom / follow camera / movement defaults -> Data/probe_boom.json"""
import unreal, json
def main():
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    R = {}
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        d = lib.get_data(h); n = str(lib.get_variable_name(d)); o = lib.get_associated_object(d)
        if o is None: continue
        R.setdefault('comps', []).append([n, o.get_class().get_name()])
        if isinstance(o, unreal.SpringArmComponent):
            R[n] = {k: str(o.get_editor_property(k)) for k in ('target_arm_length', 'socket_offset', 'target_offset', 'use_pawn_control_rotation', 'enable_camera_lag', 'do_collision_test', 'relative_location')}
        if isinstance(o, unreal.CameraComponent):
            R[n] = {k: str(o.get_editor_property(k)) for k in ('field_of_view', 'use_pawn_control_rotation', 'relative_location', 'auto_activate')}
        if isinstance(o, unreal.CharacterMovementComponent):
            R[n] = {k: str(o.get_editor_property(k)) for k in ('max_walk_speed', 'max_acceleration', 'orient_rotation_to_movement')}
        del o
    del bp
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\probe_boom.json', 'w'), indent=1)
    print('PROBE_BOOM')
main(); del main
