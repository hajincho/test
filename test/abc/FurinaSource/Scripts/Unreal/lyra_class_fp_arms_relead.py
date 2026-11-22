"""에디터(편집 전용, PIE 아님, 2026-11-22): 1인칭 팔 리더 포즈 다시 걸기 -> Saved/ClassFPArmsRelead.json
 무기를 바꾸면 FurinaFPVM 의 메시가 바뀌어 팔(FurinaFPArmsChar)의 뼈 대응이 끊기고 휴식 자세(카메라 뒤)로 남아 안 보였다.
 시점 갱신(FurinaViewUpdate, 0.05초)마다: FurinaFPVM 메시 != FurinaArmsLeaderMesh 이면 SetLeaderPoseComponent 다시 + 그 메시 저장."""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib, lyra_fpvm_optics; importlib.reload(lyra_fpvm_optics)
from lyra_fpvm_optics import ENGINE, PAWN, Graph, wire
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}; BEL = unreal.BlueprintEditorLibrary; COMP = 'FurinaFPArmsChar'

def run():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    bp = unreal.load_asset(PAWN)
    if 'FurinaArmsLeaderMesh' not in [str(v) for v in BEL.list_member_variable_names(bp)]:
        assert BEL.add_member_variable(bp, 'FurinaArmsLeaderMesh', BEL.get_object_reference_type(unreal.SkeletalMesh))
    g = Graph(bp, 'FPAR_')
    if 'FPAR_Relead' in g.nodes: return 'exists'
    ev = g.editor.find_event_node('FurinaViewUpdate'); old = list(ev.find_then_pin().list_connected_pins())
    cur = g.call('VMMesh', ENGINE + 'SkeletalMeshComponent:GetSkeletalMeshAsset', target=g.get('FurinaFPVM')).find_result_pin()
    ne = g.call('Changed', ENGINE + 'KismetMathLibrary:NotEqual_ObjectObject', A=cur, B=g.get('FurinaArmsLeaderMesh')).find_result_pin()
    br = g.branch('IfChanged', ne)
    lead = g.call('Relead', ENGINE + 'SkinnedMeshComponent:SetLeaderPoseComponent', target=g.get(COMP), NewLeaderBoneComponent=g.get('FurinaFPVM'), bForceUpdate='true')
    store = g.store('Store', 'FurinaArmsLeaderMesh', cur)
    ev.find_then_pin().break_pin_links(); wire(ev.find_then_pin(), br.find_execute_pin())
    wire(br.find_then_pin(), lead.find_execute_pin()); wire(lead.find_then_pin(), store.find_execute_pin())
    for p in old: wire(store.find_then_pin(), p); wire(br.find_else_pin(), p)
    # 외형을 바꿀 때도 다시 걸리게(팔 메시가 바뀌면 대응도 다시 만들어야 함): 각 외형 이벤트의 리더 설정은 그대로 두고, 저장값을 비워 다음 갱신에서 다시 걸게
    for Key in ('Officer', 'Infantry', 'Assault', 'AntiTank', 'Heavy', 'Sniper', 'Armor'):
        n = g.nodes['FPAC_Leader_' + Key]; t = n.find_then_pin(); nxt = list(t.list_connected_pins()); t.break_pin_links()
        clr = g.store('Reset_' + Key, 'FurinaArmsLeaderMesh', '')
        wire(t, clr.find_execute_pin())
        for p in nxt: wire(clr.find_then_pin(), p)
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, False); return {'next': [p.get_owning_node().get_name() for p in old], 'status': str(st)}

try: R['result'] = run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'ClassFPArmsRelead.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8'); print('FPAR', R)
