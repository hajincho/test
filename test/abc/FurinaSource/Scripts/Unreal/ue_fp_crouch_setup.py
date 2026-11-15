"""Crouch / stance setup (2026-11-15):
 - IA_FurinaCrouch on the C key (Default_IMC); reports what C and Left Ctrl were mapped to before
 - flag components FurinaCrouch (set from IsCrouching by the Event Tick graph -> ABP 'Crouch' curve) and FurinaShoulderAuto
   (shoulder stance entered by firing while sprinting)
 - CharacterMovement: can crouch, crouched half height = standing half height - 38 (the CR drops the pelvis by 38 cm)
 - Tools/gen_fp_aim_tick_t3d.py draws the Event Tick / crouch nodes, Tools/gen_fp_bullet_t3d.py the fire rules."""
import unreal, json
CROUCH_DROP = 38.0
def main():
    R = {'log': []}
    eal = unreal.EditorAssetLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools()
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    def key(n): k = unreal.Key(); k.set_editor_property('key_name', n); return k
    def listing(): return [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None)
                           for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    R['before_C'] = [m for m in listing() if m[0] in ('C', 'LeftControl')]
    p = '/Game/Furina/Input/IA_FurinaCrouch'
    ia = unreal.load_asset(p) if eal.does_asset_exist(p) else tools.create_asset('IA_FurinaCrouch', '/Game/Furina/Input', unreal.InputAction, None)
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN); ia.set_editor_property('triggers', [])
    eal.save_loaded_asset(ia, False)
    if ('C', 'IA_FurinaCrouch') not in listing(): imc.map_key(ia, key('C'))
    eal.save_loaded_asset(imc, False)
    R['C'] = [m for m in listing() if m[0] == 'C']
    del ia, imc
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    for name in ('FurinaCrouch', 'FurinaShoulderAuto'):
        hs = handles()
        if name not in hs:
            h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs['FurinaMesh'], new_class=unreal.SceneComponent, blueprint_context=bp))
            sub.rename_subobject(h, unreal.Text(name)); R['log'].append('added ' + name)
        comp = lib.get_associated_object(lib.get_data(handles()[name]))
        comp.set_editor_property('auto_activate', False); comp.set_editor_property('component_tags', [name])
        del comp
    hs = handles()
    cap = lib.get_associated_object(lib.get_data(hs['CapsuleComponent'])); standing = cap.get_editor_property('capsule_half_height'); del cap
    cmc = lib.get_associated_object(lib.get_data(hs['CharacterMovement']))
    nav = cmc.get_editor_property('nav_agent_props')
    for prop in ('can_crouch', 'b_can_crouch'):
        try: nav.set_editor_property(prop, True); R['nav_prop'] = prop; break
        except Exception as e: R['log'].append('nav ' + prop + ' ' + str(e))
    cmc.set_editor_property('nav_agent_props', nav)
    cmc.set_editor_property('crouched_half_height', standing - CROUCH_DROP)
    R['standing_half_height'] = standing; R['crouched_half_height'] = cmc.get_editor_property('crouched_half_height')
    R['can_crouch'] = str(cmc.get_editor_property('nav_agent_props'))
    del cmc, nav
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status')); R['saved'] = eal.save_loaded_asset(bp, False)
    del bp
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_crouch_setup.json', 'w'), indent=1, default=str)
    print('FP_CROUCH_SETUP', R)
main()
del main
