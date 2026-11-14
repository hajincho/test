"""Forced third person setup: IA_FurinaViewToggle on V (the old IA_FurinaView direct switch is unmapped, so its graph
nodes stay inert), FurinaFPWanted SceneComponent (its active flag = the view the player chose). Graph: gen_fp_view_t3d.py."""
import unreal, json
def main():
    R = {'log': []}
    eal = unreal.EditorAssetLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools()
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    def key(n): k = unreal.Key(); k.set_editor_property('key_name', n); return k
    def listing(): return [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None)
                           for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    p = '/Game/Furina/Input/IA_FurinaViewToggle'
    ia = unreal.load_asset(p) if eal.does_asset_exist(p) else tools.create_asset('IA_FurinaViewToggle', '/Game/Furina/Input', unreal.InputAction, None)
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN); eal.save_loaded_asset(ia, False)
    old = unreal.load_asset('/Game/Furina/Input/IA_FurinaView')
    if ('V', 'IA_FurinaView') in listing(): imc.unmap_key(old, key('V'))
    if ('V', 'IA_FurinaViewToggle') not in listing(): imc.map_key(ia, key('V'))
    eal.save_loaded_asset(imc, False)
    R['v_mappings'] = [m for m in listing() if m[0] == 'V']
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    hs = {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    if 'FurinaFPWanted' not in hs:
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs['FurinaMesh'], new_class=unreal.SceneComponent, blueprint_context=bp))
        sub.rename_subobject(h, unreal.Text('FurinaFPWanted')); R['log'].append('added FurinaFPWanted ' + str(fail))
        hs = {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    comp = lib.get_associated_object(lib.get_data(hs['FurinaFPWanted']))
    comp.set_editor_property('auto_activate', False)
    del comp
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status')); R['saved'] = eal.save_loaded_asset(bp, False)
    del bp, hs
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_view_setup.json', 'w'), indent=1, default=str)
    print('FP_VIEW_SETUP', R)
main()
del main
