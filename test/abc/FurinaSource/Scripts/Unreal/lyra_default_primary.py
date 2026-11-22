"""에디터(편집 전용, 2026-11-22): 시작 무기를 Kar98k 로 -> Saved/DefaultPrimary.json
 문제: 시작할 때 FurinaPrimaryKey 가 비어 있어 예전 M4 + 푸리나 전용 1인칭 팔(SM_FurinaFPArm*)이 나옴 -> 병과를 골라도 '1인칭이 푸리나 손'.
 독일·일본 무기(SK_FPVM_*)에는 병과 팔 14종이 들어 있으므로, BeginPlay 의 LOOK_StartLook(보병 외형) 바로 뒤에
 FurinaPrimaryKey = IsEmpty(FurinaPrimaryKey) ? 'kar98k' : FurinaPrimaryKey 를 넣는다(무기창에서 고른 값은 그대로). 노드 이름 DEFW_*. 다시 돌리면 건너뜀."""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import PAWN, MATH, STRINGS, Graph, relay
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
try:
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    bp = unreal.load_asset(PAWN); g = Graph(bp, 'DEFW_')
    if any(n.startswith('DEFW_') for n in g.nodes): R['skipped'] = 'already'
    else:
        start = g.locate('LOOK_StartLook')
        empty = g.call('IsEmpty', STRINGS + 'IsEmpty', InString=g.get('FurinaPrimaryKey'))
        sel = g.call('Select', MATH + 'SelectString', A='kar98k', B=g.get('FurinaPrimaryKey'))
        from lyra_fpvm_optics import wire
        wire(empty.get_return_value_pin() if hasattr(empty, 'get_return_value_pin') else empty.find_output_pin('ReturnValue'), sel.find_input_pin('bPickA'))
        st = g.store('SetPrimary', 'FurinaPrimaryKey', sel.find_output_pin('ReturnValue'))
        relay(start.find_then_pin(), st.find_execute_pin(), st.find_then_pin())
        R['inserted'] = True
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); st_ = bp.get_editor_property('status'); R['status'] = str(st_)
    assert st_ != unreal.BlueprintStatus.BS_ERROR, str(st_)
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'DefaultPrimary.json').write_text(json.dumps(R, indent=1), encoding='utf-8'); print('DEFAULT_PRIMARY', R)
