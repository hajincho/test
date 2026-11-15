"""Enables / disables the prone stance (2026-11-15). The Z key stays mapped (IA_FurinaProne in IMC_FurinaStance); the character BP's input event FPN_ProneToggle.Started is linked to /
unlinked from FPN_ProneBranch (the toggle logic). Disabled = the key does nothing. Character nodes, ABP states, Control Rig prone blocks and the crawl assets stay in place.
usage: py ue_prone_enable.py <on|off>  -> Data/prone_enable.json"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    on = (sys.argv[1] if len(sys.argv) > 1 else 'off') == 'on'
    E = unreal.EditorAssetLibrary
    R = {'mode': 'on' if on else 'off'}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    started = nodes['FPN_ProneToggle'].find_output_pin('Started'); branch = nodes['FPN_ProneBranch']
    R['linked_before'] = len(started.list_connected_pins())
    started.break_pin_links()
    if on: assert unreal.BlueprintGraphPinLibrary.try_create_connection(started, branch.find_execute_pin()), 'link failed'
    R['linked_after'] = len(started.list_connected_pins())
    del ed, nodes, started, branch
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = E.save_loaded_asset(bp, False)
    del bp
    # in-memory input mapping: make sure Z is mapped (an earlier unmap attempt removed it in memory only; the file on disk was never changed)
    ia = unreal.load_asset('/Game/Furina/Input/IA_FurinaProne'); imc = unreal.load_asset('/Game/Furina/Input/IMC_FurinaStance')
    names = [str(m.get_editor_property('action').get_name()) for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')] if hasattr(imc.get_editor_property('default_key_mappings'), 'get_editor_property') else []
    if 'IA_FurinaProne' not in names:
        k = unreal.Key(); k.set_editor_property('key_name', 'Z'); imc.map_key(ia, k); R['imc_remapped_in_memory'] = True
    R['imc_actions'] = names
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\prone_enable.json', 'w'), indent=1); print('PRONE_ENABLE', R)
