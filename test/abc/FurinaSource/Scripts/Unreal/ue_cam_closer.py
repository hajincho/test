"""Third-person camera closer and higher (2026-11-15): CameraBoom.TargetArmLength 469 -> 330 (shoulder 234.5 -> 165), CameraBoom.TargetOffset z +55 so the
screen-centre crosshair is above the character's body, shoulder camera side offset 110 -> 60 cm (80 put the body at the screen edge) and its height 20 -> 30 cm."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    b = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in sub.k2_gather_subobject_data_for_blueprint(b):
        if str(lib.get_variable_name(lib.get_data(h))) == 'CameraBoom':
            boom = lib.get_associated_object(lib.get_data(h))
            boom.set_editor_property('target_arm_length', 330.0); boom.set_editor_property('target_offset', unreal.Vector(0, 0, 55)); R['boom'] = [boom.get_editor_property('target_arm_length'), str(boom.get_editor_property('target_offset'))]; del boom
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(b, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    for node, pin, value in (('TFP_ArmTarget', 'A', '165'), ('TFP_ArmTarget', 'B', '330'), ('K2Node_FPT_Lat1', 'B', '60'), ('K2Node_FPT_TgtZ', 'A', '30')):
        n = nodes.get(node); R[node + '.' + pin] = (n.find_input_pin(pin).set_pin_value(value) if n else 'missing')
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(b); R['status'] = str(b.get_editor_property('status'))
    if b.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(b, False)
    del b
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\cam_closer.json', 'w'), indent=1); print('CAM_CLOSER', R)
