"""에디터(편집 전용, PIE 아님, 2026-11-22): 저격총 조준경으로 정조준할 때 마우스 감도 = 기존 감도 / 배율 -> Saved/ScopeSensitivity.json
 렌즈 속 화면은 배율(ZF39·ZF4 4배, ZF41 1.5배)만큼 확대돼 같은 마우스 이동에도 렌즈 속 그림이 배율배 빨리 움직였다.
 조준경 화면 시야각이 2·atan(tan30°/배율)(기존 정조준 60° 기준)이라 회전량에 1/배율을 곱하면 렌즈 속 움직임이 기존 감도와 같아진다.
 시점 입력(IA_Look Triggered -> AddControllerYawInput(K2Node_CallFunction_8427) -> AddControllerPitchInput(K2Node_CallFunction_8428))의
 Val = Get Look Rate × Select(FurinaScopeActive, 1/FurinaScopeZoom, 1). FurinaScopeActive 는 조준경 무기 + 정조준 + 재장전 아님일 때만 참."""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib, lyra_fpvm_optics; importlib.reload(lyra_fpvm_optics)
from lyra_fpvm_optics import ENGINE, MATH, PAWN, Graph, wire
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}; BEL = unreal.BlueprintEditorLibrary


def run():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    bp = unreal.load_asset(PAWN); g = Graph(bp, 'SENS_')
    if 'SENS_Scale' in g.nodes: return 'exists'
    import uuid
    junk = [n for k, n in g.nodes.items() if k.startswith('SENS_')]   # 실패한 이전 실행이 남긴 노드
    for n in junk:
        for p in n.list_all_pins(): p.break_pin_links()
        n.rename('Discarded_' + uuid.uuid4().hex)
    if junk: g.editor.remove_nodes(junk)
    one = g.call('One', ENGINE + 'KismetSystemLibrary:MakeLiteralDouble', Value=1.0).find_result_pin()   # 실수 핀 A 에 상수를 바로 넣으면 실패해서 상수 노드 사용
    inv = g.call('InvZoom', MATH + 'Divide_DoubleDouble', A=one, B=g.get('FurinaScopeZoom'))
    scale = g.call('Scale', MATH + 'SelectFloat', bPickA=g.get('FurinaScopeActive'), A=inv.find_result_pin(), B=one)
    out = {}
    for node_name, tag in (('K2Node_CallFunction_8427', 'Yaw'), ('K2Node_CallFunction_8428', 'Pitch')):
        val = g.nodes[node_name].find_input_pin('Val'); src = list(val.list_connected_pins()); assert len(src) == 1, (node_name, src)
        val.break_pin_links()
        mul = g.call('Mul' + tag, MATH + 'Multiply_DoubleDouble', A=src[0], B=scale.find_result_pin())
        wire(mul.find_result_pin(), val); out[tag] = src[0].get_owning_node().get_name()
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    out['status'] = str(st); return out


try: R['result'] = run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'ScopeSensitivity.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8'); print('SCOPE_SENS', R)
