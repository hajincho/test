"""Right mouse aiming setup:
 - IA_FurinaADS (Tap trigger, <0.2 s)  -> aim down sights toggle;  IA_FurinaShoulder (Hold trigger, >=0.2 s) -> shouldered while held
 - flag SceneComponents on the character (tagged, read by ABP_Furina / BP_FurinaHUD with FindComponentByTag):
   FurinaADS, FurinaShoulder, FurinaADSRestoreTP (ADS entered from third person -> go back after)
Graph logic: Tools/gen_fp_aim_t3d.py."""
import unreal, json
def main():
    R = {'log': []}
    eal = unreal.EditorAssetLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools()
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    def key(n): k = unreal.Key(); k.set_editor_property('key_name', n); return k
    def listing(): return [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None)
                           for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    for name, trig_cls, prop, val in (('IA_FurinaADS', unreal.InputTriggerTap, 'tap_release_time_threshold', 0.2),
                                      ('IA_FurinaShoulder', unreal.InputTriggerHold, 'hold_time_threshold', 0.2)):
        p = '/Game/Furina/Input/' + name
        ia = unreal.load_asset(p) if eal.does_asset_exist(p) else tools.create_asset(name, '/Game/Furina/Input', unreal.InputAction, None)
        ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
        trig = unreal.new_object(trig_cls, outer=ia)
        trig.set_editor_property(prop, val)
        ia.set_editor_property('triggers', [trig])
        eal.save_loaded_asset(ia, False)
        if ('RightMouseButton', name) not in listing(): imc.map_key(ia, key('RightMouseButton'))
        R['log'].append((name, [t.get_class().get_name() for t in ia.get_editor_property('triggers')]))
    eal.save_loaded_asset(imc, False)
    R['rmb'] = [m for m in listing() if m[0] == 'RightMouseButton']
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    for name in ('FurinaADS', 'FurinaShoulder', 'FurinaADSRestoreTP'):
        hs = handles()
        if name not in hs:
            h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs['FurinaMesh'], new_class=unreal.SceneComponent, blueprint_context=bp))
            sub.rename_subobject(h, unreal.Text(name)); R['log'].append('added ' + name)
        comp = lib.get_associated_object(lib.get_data(handles()[name]))
        comp.set_editor_property('auto_activate', False)
        comp.set_editor_property('component_tags', [name])
        del comp
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status')); R['saved'] = eal.save_loaded_asset(bp, False)
    del bp
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_aim_setup.json', 'w'), indent=1, default=str)
    print('FP_AIM_SETUP', R)
main()
del main
