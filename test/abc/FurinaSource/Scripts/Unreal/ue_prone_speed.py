"""Sets the prone walk / Shift speed (cm/s) in the character BP (nodes FPN_ProneWalk / FPN_ProneRun, pin A) and the stance table. usage: py ue_prone_speed.py <cm_s>"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    v = sys.argv[1] if len(sys.argv) > 1 else '61'
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    for k in ('FPN_ProneWalk', 'FPN_ProneRun'): nodes[k].find_input_pin('A').set_pin_value(v)
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R = {'status': str(bp.get_editor_property('status')), 'speed': v}
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\prone_speed.json', 'w'), indent=1); print('PRONE_SPEED', R)
