"""Recoil / stance setup:
 - IA_FurinaFireRifle on LeftMouseButton (full auto with recoil, Tools/gen_fp_bullet_t3d.py); IA_FurinaFireAuto unmapped
 - flag components FurinaSpeedCap (aim stance owns MaxWalkSpeed) and FurinaShoulderLeft (shoulder camera side),
   read by the Event Tick nodes from Tools/gen_fp_aim_tick_t3d.py"""
import unreal, json
def main():
    R = {'log': []}
    eal = unreal.EditorAssetLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools()
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    def key(n): k = unreal.Key(); k.set_editor_property('key_name', n); return k
    def listing(): return [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None)
                           for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    p = '/Game/Furina/Input/IA_FurinaFireRifle'
    ia = unreal.load_asset(p) if eal.does_asset_exist(p) else tools.create_asset('IA_FurinaFireRifle', '/Game/Furina/Input', unreal.InputAction, None)
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN); ia.set_editor_property('triggers', [])
    eal.save_loaded_asset(ia, False)
    if ('LeftMouseButton', 'IA_FurinaFireRifle') not in listing(): imc.map_key(ia, key('LeftMouseButton'))
    old = unreal.load_asset('/Game/Furina/Input/IA_FurinaFireAuto')
    if ('LeftMouseButton', 'IA_FurinaFireAuto') in listing(): imc.unmap_key(old, key('LeftMouseButton'))
    eal.save_loaded_asset(imc, False)
    R['lmb'] = [m for m in listing() if m[0] == 'LeftMouseButton']
    del ia, old, imc
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    for name in ('FurinaSpeedCap', 'FurinaShoulderLeft'):
        hs = handles()
        if name not in hs:
            h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs['FurinaMesh'], new_class=unreal.SceneComponent, blueprint_context=bp))
            sub.rename_subobject(h, unreal.Text(name)); R['log'].append('added ' + name)
        comp = lib.get_associated_object(lib.get_data(handles()[name]))
        comp.set_editor_property('auto_activate', False); comp.set_editor_property('component_tags', [name])
        del comp
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status')); R['saved'] = eal.save_loaded_asset(bp, False)
    del bp
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_recoil_setup.json', 'w'), indent=1, default=str)
    print('FP_RECOIL_SETUP', R)
main()
del main
