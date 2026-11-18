"""Lyra 에디터(`py <파일> [remove]`, PIE 중지 상태): 메인 화면 포탈로 스테이지에 들어오면 마우스로 시점이 안 돌아가는 문제 수정.
원인(로그 확인): 포탈이 메뉴 레이어에 W_NonInteractiveSpinner 를 띄우면 CommonUI 가 입력 모드를 Menu(마우스 캡처 없음, 커서 표시)로 바꾸는데,
새 스테이지에서 게임 입력 모드로 되돌리는 곳이 없다(경험에 HUD 레이아웃이 안 올라옴).  -> 푸리나 폰의 ReceiveControllerChanged 끝에
GetPlayerController(0) -> SetInputMode_GameOnly, SetShowMouseCursor(false) 를 넣어 플레이어가 폰을 잡을 때 게임 입력으로 복구한다.
노드 이름: FPN_PIGet, FPN_PIGame, FPN_PICursor.  `remove` 면 그 노드들을 지운다.  -> Data/lyra_portal_input_fix.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_portal_input_fix.json'
CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    names = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'remove' in sys.argv:
        for k in ('FPN_PIGame', 'FPN_PICursor', 'FPN_PIGet'):
            if k in names:
                n = names[k]
                try:
                    prev = [p for p in n.find_execute_pin().list_connected_pins()] if k != 'FPN_PIGet' else []
                    nxt = [p for p in n.find_then_pin().list_connected_pins()] if k != 'FPN_PIGet' else []
                    if k != 'FPN_PIGet':
                        n.find_execute_pin().break_pin_links(); n.find_then_pin().break_pin_links()
                        for a in prev:
                            for b in nxt: CONN(a, b)
                except Exception as e: R.setdefault('rm_err', []).append(str(e)[:100])
                ed.remove_node(n) if hasattr(ed, 'remove_node') else R.setdefault('rm_err', []).append('no remove_node')
        R['removed'] = True
    elif 'FPN_PICursor' not in names:
        ev = ed.find_event_node('ReceiveControllerChanged'); assert ev, 'no ReceiveControllerChanged'
        R['event'] = ev.get_name()
        get = names.get('FPN_PIGet')
        if get is None:
            get = ed.add_call_function_node('/Script/Engine.GameplayStatics:GetPlayerController'); get.rename('FPN_PIGet'); get.find_input_pin('PlayerIndex').set_pin_value('0')
        gm = ed.add_call_function_node('/Script/UMG.WidgetBlueprintLibrary:SetInputMode_GameOnly') if 'FPN_PIGame' not in names else names['FPN_PIGame']
        gm.rename('FPN_PIGame')
        cu = ed.add_set_member_variable_node('bShowMouseCursor', '/Script/Engine.PlayerController'); cu.rename('FPN_PICursor'); cu.find_input_pin('bShowMouseCursor').set_pin_value('false')
        old = list(ev.find_then_pin().list_connected_pins()); ev.find_then_pin().break_pin_links()
        assert CONN(ev.find_then_pin(), gm.find_execute_pin())
        assert CONN(get.find_output_pin('ReturnValue'), gm.find_input_pin('PlayerController'))
        assert CONN(gm.find_then_pin(), cu.find_execute_pin())
        assert CONN(get.find_output_pin('ReturnValue'), cu.find_self_pin())
        for p in old: assert CONN(cu.find_then_pin(), p)
        R['added'] = True
    del ed, names
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PORTAL_INPUT', R.get('status'), R.get('error', '')[-300:])
