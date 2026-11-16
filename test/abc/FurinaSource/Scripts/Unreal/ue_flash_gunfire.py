"""Switches the Niagara layer of the muzzle flash from Sparks_FXS to the Niagara Examples muzzle flash /Game/NiagaraExamples/FX_Weapons/MuzzleFlashes/NS_MuzzleFlash (2026-11-16).
Character BP chain: M4_FlashFinish -> FNS_SparkSpawn (SpawnSystemAtLocation, now NS_MuzzleFlash, Rotation = ComposeRotators(yaw 90, M4_FlashRotation): the system fires along +X, the rifle along +Y)
-> FNS_SetGlobalScale (SetVariableFloat 'Global Scale') -> FNS_SetUseShell (SetVariableBool 'Use Bullet Shell' = false, our own physical empty case is ejected by BP_223Case) -> M4_CaseSpawn.
usage: py ue_flash_gunfire.py [global_scale]  (PIE stopped) -> Data/flash_gunfire.json"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
GS = sys.argv[1] if len(sys.argv) > 1 else '0.5'
def main():
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def link(a, b): b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link'
    def mk(name, path):
        n = nodes.get(name)
        if n is None: n = ed.add_call_function_node(path); assert n, path; n.rename(name); nodes[name] = n; R.setdefault('added', []).append(name)
        return n
    sp = nodes['FNS_SparkSpawn']
    assert sp.find_input_pin('SystemTemplate').set_pin_value('/Game/NiagaraExamples/FX_Weapons/MuzzleFlashes/NS_MuzzleFlash.NS_MuzzleFlash')
    sp.find_input_pin('Scale').set_pin_value('1,1,1')
    comp = mk('FNS_ComposeYaw', '/Script/Engine.KismetMathLibrary:ComposeRotators'); comp.find_input_pin('A').set_pin_value('0,90,0')   # Rotator text order: Pitch,Yaw,Roll
    link(nodes['M4_FlashRotation'].find_result_pin(), comp.find_input_pin('B')); link(comp.find_result_pin(), sp.find_input_pin('Rotation'))
    gs = mk('FNS_SetGlobalScale', '/Script/Niagara.NiagaraComponent:SetVariableFloat'); gs.find_input_pin('InVariableName').set_pin_value('Global Scale'); gs.find_input_pin('InValue').set_pin_value(GS)
    ub = mk('FNS_SetUseShell', '/Script/Niagara.NiagaraComponent:SetVariableBool'); ub.find_input_pin('InVariableName').set_pin_value('Use Bullet Shell'); ub.find_input_pin('InValue').set_pin_value('false')
    nxt = nodes['M4_CaseSpawn'].find_execute_pin()
    link(sp.find_result_pin(), gs.find_self_pin()); link(sp.find_result_pin(), ub.find_self_pin())
    link(sp.find_then_pin(), gs.find_execute_pin()); link(gs.find_then_pin(), ub.find_execute_pin()); link(ub.find_then_pin(), nxt)
    R['global_scale'] = GS
    del ed, nodes, sp, comp, gs, ub, nxt
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\flash_gunfire.json', 'w'), indent=1); print('FLASH_GUNFIRE', R.get('error', R.get('status'))[-300:])
