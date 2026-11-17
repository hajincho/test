"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 견착 진입 전환을 2배 느리게(속도 1/2), 앉는(자세 전환)을 3배 느리게(속도 1/3). 원래 값 기준.
 견착: CR_FurinaSecondary ShW.Blend 14 -> 7 (견착 자세 보간), 폰 K2Node_FPT_NewOff / NewFov InterpSpeed 10 -> 5 (3인칭 견착 카메라 옆 오프셋/FOV 보간)
 앉기: CR_FurinaSecondary CrouchW.Blend 9 -> 3 (골반/발 IK 자세), ABP_Furina TFPCrouchSmooth InterpSpeed 10 -> 3.3333 (이동 블렌드의 서기↔앉기 보간)
 (처음에 '늘려'를 빠르게로 잘못 해석해 14->28 등으로 올렸다가 이 값으로 바로잡음.) 이미 목표값이면 건너뛴다.   -> Data/lyra_shoulder_crouch_speed.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_shoulder_crouch_speed.json'
R = {}
def setpin(bp, node, pin, new, old_expect):
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    n = [x for x in ed.list_all_nodes() if x.get_name() == node][0]; p = n.find_input_pin(pin); before = str(p.get_pin_value())
    if abs(float(before) - float(new)) > 1e-6: assert p.set_pin_value(str(new)), 'set ' + node
    return [before, str(p.get_pin_value())]
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); R['cr'] = {}
    for node, new in (('ShW', '7.0'), ('CrouchW', '3')):
        path = node + '.Blend'; node_obj = [n for n in c.get_graph().get_nodes() if str(n.get_node_path()) == node][0]
        before = [str(p.get_default_value()) for p in node_obj.get_pins() if str(p.get_name()) == 'Blend'][0]
        if abs(float(before) - float(new)) > 1e-6: R['cr'][node + '_set'] = bool(c.set_pin_default_value(path, new, True, False))
        R['cr'][node] = [before, [str(p.get_default_value()) for p in node_obj.get_pins() if str(p.get_name()) == 'Blend'][0]]
    cr.recompile_vm(); R['cr_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(cr, False)
    abp = unreal.load_asset('/Game/Furina/ABP_Furina'); R['abp'] = setpin(abp, 'TFPCrouchSmooth', 'InterpSpeed', 3.3333, 10)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp); R['abp_status'] = str(abp.get_editor_property('status')); R['abp_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(abp, False)
    pawn = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    R['pawn_off'] = setpin(pawn, 'K2Node_FPT_NewOff', 'InterpSpeed', 5, 10); R['pawn_fov'] = setpin(pawn, 'K2Node_FPT_NewFov', 'InterpSpeed', 5, 10)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn); R['pawn_status'] = str(pawn.get_editor_property('status')); R['pawn_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(pawn, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_SPEEDS', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
