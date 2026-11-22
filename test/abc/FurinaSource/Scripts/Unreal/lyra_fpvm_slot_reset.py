"""에디터(편집 전용, 2026-11-22): 무기를 바꾸면 판처파우스트가 안 보이던 버그 -> Saved/FpvmSlotReset.json
 원인: 재질 덮어쓰기(SetMaterialByName)는 컴포넌트에 '슬롯 번호'로 남는다. Kar98k 등에서 가린 병과 팔 슬롯 번호(예 14)가
   판처파우스트 메시에서는 본체 슬롯 'Panzerfaust60Surface' 번호라 본체가 M_FPVM_Hidden 으로 남음(무기 장착 때 0~9번만 되돌림).
 수정: 시점 갱신의 팔 슬롯 고르기(FPAS_, 외형+메시가 바뀔 때만 돎)에서 팔 슬롯이 아닌 슬롯(무기)도 기본 재질로 되돌림
   = FPAS_ArmsSlot 의 거짓 출력 -> FPAS_SetDefault. 조준경 몸통 가림(TubeHide)은 다음 갱신에서 FurinaScopeTubeHidden 을 거짓으로 돌려 다시 판정."""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import PAWN, Graph, wire
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
try:
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    bp = unreal.load_asset(PAWN); g = Graph(bp, 'FPRS_')
    arms = g.nodes['FPAS_ArmsSlot']; setd = g.nodes['FPAS_SetDefault']
    else_pin = arms.find_else_pin(); R['else_before'] = [p.get_owning_node().get_name() for p in else_pin.list_connected_pins()]
    if not R['else_before']: wire(else_pin, setd.find_execute_pin()); R['wired'] = True
    # 조준경 몸통 가림 상태도 초기화(무기 슬롯을 되돌렸으니 다음 판정에서 다시 가림)
    st = g.nodes['FPAS_StoreState']
    if 'FPRS_TubeReset' not in g.nodes:
        nxt = list(st.find_then_pin().list_connected_pins()); st.find_then_pin().break_pin_links()
        tr = g.store('TubeReset', 'FurinaScopeTubeHidden', False); wire(st.find_then_pin(), tr.find_execute_pin())
        for p in nxt: wire(tr.find_then_pin(), p)
        R['tube_reset'] = [p.get_owning_node().get_name() for p in nxt]
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); s = bp.get_editor_property('status'); R['status'] = str(s)
    assert s != unreal.BlueprintStatus.BS_ERROR
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'FpvmSlotReset.json').write_text(json.dumps(R, indent=1), encoding='utf-8'); print('SLOT_RESET', R)
