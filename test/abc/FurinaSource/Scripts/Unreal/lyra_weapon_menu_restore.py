"""헤드리스: 무기창 닫을 때 게임 입력 복원. (Lyra HUD 가 이전 입력 설정을 갖고 있지 않아 CommonUI 가 Menu 상태(커서 보임, 마우스 캡처 없음)로 남았음)
 위젯 CloseMenu: DeactivateWidget -> SetInputMode_GameOnly(PC0) -> bShowMouseCursor=false.  폰의 닫기 분기(FWM2_Close)도 같은 복원.  -> Data/lyra_weapon_menu_restore.json"""
import unreal, json, traceback
CONN = unreal.BlueprintGraphPinLibrary.try_create_connection; BEL = unreal.BlueprintEditorLibrary
R = {}
def add_restore(bp, after_node_name, prefix):
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    if prefix + 'GameOnly' in N: return 'exists'
    src = N[after_node_name]; nxt = list(src.find_then_pin().list_connected_pins()); src.find_then_pin().break_pin_links()
    pc = ed.add_call_function_node('/Script/Engine.GameplayStatics:GetPlayerController'); pc.rename(prefix + 'PC'); pc.find_input_pin('PlayerIndex').set_pin_value('0')
    go = ed.add_call_function_node('/Script/UMG.WidgetBlueprintLibrary:SetInputMode_GameOnly'); go.rename(prefix + 'GameOnly')
    cu = ed.add_call_function_node('/Script/Engine.KismetSystemLibrary:SetBoolPropertyByName'); cu.rename(prefix + 'CursorOff')
    cu.find_input_pin('PropertyName').set_pin_value('bShowMouseCursor'); cu.find_input_pin('Value').set_pin_value('false')
    assert CONN(pc.find_output_pin('ReturnValue'), go.find_input_pin('PlayerController')); assert CONN(pc.find_output_pin('ReturnValue'), cu.find_input_pin('Object'))
    assert CONN(src.find_then_pin(), go.find_execute_pin()); assert CONN(go.find_then_pin(), cu.find_execute_pin())
    for p in nxt: CONN(cu.find_then_pin(), p)
    del ed, N
    return 'added'
try:
    w = unreal.load_asset('/Game/Furina/UI/WBP_FurinaWeaponMenu'); R['widget'] = add_restore(w, 'WM_Deactivate', 'WR_')
    BEL.compile_blueprint(w); R['w_status'] = str(w.get_editor_property('status')); R['w_saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(w, False))
    p = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); R['pawn'] = add_restore(p, 'FWM2_Close', 'FWM2R_')
    import gc; gc.collect()
    BEL.compile_blueprint(p); R['p_status'] = str(p.get_editor_property('status')); R['p_saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(p, False))
except Exception: R['error'] = traceback.format_exc()[-1000:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_weapon_menu_restore.json', 'w'), indent=1); print('WM_RESTORE', R)
