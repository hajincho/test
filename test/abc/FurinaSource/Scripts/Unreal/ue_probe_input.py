"""Lists Default_IMC mappings (key -> action) and CharacterMovement crouch / capsule settings -> Data/probe_input.json"""
import unreal, json
def main():
    R = {}
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    R['map'] = [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None)
                for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        o = lib.get_associated_object(lib.get_data(h))
        if isinstance(o, unreal.CharacterMovementComponent):
            R['cmc'] = {k: str(o.get_editor_property(k)) for k in ('max_walk_speed', 'max_walk_speed_crouched', 'crouched_half_height', 'nav_agent_props', 'max_acceleration')}
        if isinstance(o, unreal.CapsuleComponent):
            R['capsule'] = dict(hh=o.get_editor_property('capsule_half_height'), r=o.get_editor_property('capsule_radius'))
        if isinstance(o, unreal.SpringArmComponent): R['arm'] = o.get_editor_property('target_arm_length')
        del o
    del bp, imc
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\probe_input.json', 'w'), indent=1)
    print('PROBE_INPUT')
main(); del main
