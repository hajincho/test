"""Lyra 에디터(`py <파일> keep`, PIE 중지 후): 발사 경로 보강 + 최적화.
 [BP_FurinaBullet]
  - Bullet 구의 Visibility/Camera 응답을 Block -> Ignore: 조준선(Visibility 라인 트레이스)과 카메라 붐(Camera 프로브)이 날아가는 총알에 걸리지 않게.
  - 적중 경로의 디버그 PrintString 2개(FRC_PrintHit, FRC_PrintTrue)를 실행 경로에서 뺀다 (맞을 때마다 문자열 ~20개를 만들어 화면 출력하던 것). Hit -> FRC_Branch, FRC_SetCount -> FRC_RSpawn 직결.
 [ThirdPersonCharacter_BP]
  - 총구 가드: 발사 때 카메라 -> 총구 선분(Visibility, 자신 무시)이 막혀 있으면(총구가 벽 반대편) 총알을 카메라 위치에서 생성. 노드 FSG_*.
  - FurinaMagUpdate 타이머 0.016 -> 0.033초 (MagState 전환 폭이 0.06초라 충분).
 -> Data/lyra_fix_shots.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fix_shots.json'
R = {'log': []}
def link(a, b):
    assert a.is_valid() and b.is_valid(), (a, b); b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
try:
    # ---- 총알 BP
    bul = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet')
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    sphere = None
    for h in S.k2_gather_subobject_data_for_blueprint(bul):
        d = L.get_data(h)
        if str(L.get_variable_name(d)) == 'Bullet': sphere = L.get_associated_object(d)
    R['before'] = {c: str(sphere.get_collision_response_to_channel(getattr(unreal.CollisionChannel, c))).split('.')[-1] for c in ('ECC_VISIBILITY', 'ECC_CAMERA')}
    sphere.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionResponseType.ECR_IGNORE)
    sphere.set_collision_response_to_channel(unreal.CollisionChannel.ECC_CAMERA, unreal.CollisionResponseType.ECR_IGNORE)
    R['after'] = {c: str(sphere.get_collision_response_to_channel(getattr(unreal.CollisionChannel, c))).split('.')[-1] for c in ('ECC_VISIBILITY', 'ECC_CAMERA')}
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bul, 'EventGraph'); bn = {n.get_name(): n for n in ed.list_all_nodes()}
    if bn['K2Node_FPB_Hit'].find_then_pin().list_connected_pins()[0].get_owning_node().get_name() == 'FRC_PrintHit':
        link(bn['K2Node_FPB_Hit'].find_then_pin(), bn['FRC_Branch'].find_input_pin('execute')); R['log'].append('bullet: Hit -> FRC_Branch')
    if 'FRC_PrintTrue' in bn and bn['FRC_SetCount'].find_then_pin().list_connected_pins()[0].get_owning_node().get_name() == 'FRC_PrintTrue':
        link(bn['FRC_SetCount'].find_then_pin(), bn['FRC_RSpawn'].find_input_pin('execute')); R['log'].append('bullet: SetCount -> RSpawn')
    unreal.BlueprintEditorLibrary.compile_blueprint(bul); R['bullet_status'] = str(bul.get_editor_property('status')); R['bullet_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bul, False)
    # ---- 폰 BP
    pawn = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(pawn, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    tm = nodes['FMG_Timer'].find_input_pin('Time'); R['timer_before'] = tm.get_pin_value(); tm.set_pin_value('0.033')
    camloc = nodes['K2Node_FPF_CamLoc']; muz = nodes['K2Node_FPF_Muzzle']; aim = nodes['K2Node_FPF_Aim']; bolt = nodes['K2Node_FPF_Bolt']
    tr = nodes.get('FSG_Trace')
    if tr is None:
        tr = ed.add_call_function_node('/Script/Engine.KismetSystemLibrary:LineTraceSingle'); tr.rename('FSG_Trace')
    tr.find_input_pin('TraceChannel').set_pin_value('TraceTypeQuery1'); tr.find_input_pin('bIgnoreSelf').set_pin_value('true'); tr.find_input_pin('bTraceComplex').set_pin_value('false')
    link(camloc.find_output_pin('ReturnValue'), tr.find_input_pin('Start')); link(muz.find_output_pin('ReturnValue'), tr.find_input_pin('End'))
    sel = nodes.get('FSG_Select')
    if sel is None:
        sel = ed.add_call_function_node('/Script/Engine.KismetMathLibrary:SelectVector'); sel.rename('FSG_Select')
    R['trace_pins'] = [str(p.get_pin_name()) for p in tr.list_all_pins()]
    link(camloc.find_output_pin('ReturnValue'), sel.find_input_pin('A')); link(muz.find_output_pin('ReturnValue'), sel.find_input_pin('B')); link(tr.find_output_pin('ReturnValue'), sel.find_input_pin('bPickA'))
    link(sel.find_result_pin(), nodes['K2Node_FPF_ShotXf'].find_input_pin('Location')); link(sel.find_result_pin(), nodes['K2Node_FPF_ToAim'].find_input_pin('B'))
    link(bolt.find_then_pin(), tr.find_input_pin('execute')); link(tr.find_output_pin('then'), aim.find_input_pin('execute')); R['log'].append('pawn: muzzle guard linked')
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn); R['pawn_status'] = str(pawn.get_editor_property('status')); R['pawn_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(pawn, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIX_SHOTS', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
