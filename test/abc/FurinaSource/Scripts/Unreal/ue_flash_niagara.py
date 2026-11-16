"""Muzzle flash spark layer from a real Niagara system (2026-11-15). The Niagara system internals can not be authored from the Python API of this editor build (no emitter / module access), so the project's
existing system /Game/3DPlatformerGameBundle/NiagaraSystems/Sparks_FXS is spawned at the muzzle point on every shot (scale SPARK_SCALE): character BP chain
M4_FlashFinish -> FNS_SparkSpawn (NiagaraFunctionLibrary.SpawnSystemAtLocation, Location = M4_FlashPoint result, Rotation = M4_FlashRotation result) -> (what followed M4_FlashFinish before).
usage: py ue_flash_niagara.py [scale]   (PIE stopped)  -> Data/flash_niagara.json"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
SC = sys.argv[1] if len(sys.argv) > 1 else '0.07'
def main():
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}; R['flash_nodes'] = sorted(k for k in nodes if 'Flash' in k)
    fin = nodes['M4_FlashFinish']; pt = nodes['M4_FlashPoint']; rot = nodes['M4_FlashRotation']
    n = nodes.get('FNS_SparkSpawn')
    if n is None:
        n = ed.add_call_function_node('/Script/Niagara.NiagaraFunctionLibrary:SpawnSystemAtLocation'); assert n; n.rename('FNS_SparkSpawn')
        then = fin.find_then_pin(); nxt = nodes['M4_CaseSpawn'].find_execute_pin(); then.break_pin_links()
        assert unreal.BlueprintGraphPinLibrary.try_create_connection(then, n.find_execute_pin()); assert unreal.BlueprintGraphPinLibrary.try_create_connection(n.find_then_pin(), nxt)
        R['added'] = True
    assert n.find_input_pin('SystemTemplate').set_pin_value('/Game/3DPlatformerGameBundle/NiagaraSystems/Sparks_FXS.Sparks_FXS')
    for a, b in ((pt.find_result_pin(), n.find_input_pin('Location')), (rot.find_result_pin(), n.find_input_pin('Rotation'))):
        b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b)
    n.find_input_pin('Scale').set_pin_value('%s,%s,%s' % (SC, SC, SC))
    R['scale'] = SC
    del ed, nodes, n, fin, pt, rot
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\flash_niagara.json', 'w'), indent=1); print('FLASH_NIAGARA', R.get('error', R.get('status'))[-200:])
