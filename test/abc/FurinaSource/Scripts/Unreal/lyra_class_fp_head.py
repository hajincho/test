"""에디터(편집 전용, PIE 아님, 2026-11-22): 병과 외형 1인칭에서 머리 숨기기(lyra_classes.py 앞에 한 번).
 1인칭 카메라(FPCamera, Head 뼈 소켓)가 다른 캐릭터의 머리·모자 안에 들어가 화면을 가림(푸리나는 얼굴 뒷면이 안 그려져 보이지 않았음).
 lyra_classes.py 가 조건을 외형 != 'furina' 로 바꿈.
 시점 갱신 이벤트(FurinaViewUpdate, 0.05초) 앞에: 원함 = (FurinaLook == 'infantry') AND FPCamera.IsActive,
 원함 != IsBoneHiddenByName(Head) 일 때만 HideBoneByName / UnHideBoneByName(Head). -> Saved/ClassFPHead.json"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib, lyra_fpvm_optics; importlib.reload(lyra_fpvm_optics)
from lyra_fpvm_optics import ENGINE, MATH, PAWN, STRINGS, Graph, wire
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}; BEL = unreal.BlueprintEditorLibrary


def run():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    pawn = unreal.load_asset(PAWN); g = Graph(pawn, 'LOOKH_')
    if 'LOOKH_Diff' in g.nodes: return 'exists'
    ev = g.editor.find_event_node('FurinaViewUpdate'); assert ev, 'FurinaViewUpdate'
    old = list(ev.find_then_pin().list_connected_pins()); R['old_next'] = [p.get_owning_node().get_name() for p in old]
    mesh = g.get('FurinaMesh')
    inf = g.call('IsInf', STRINGS + 'EqualEqual_StrStr', A=g.get('FurinaLook'), B='infantry')
    act = g.call('FPActive', ENGINE + 'ActorComponent:IsActive', target=g.get('FPCamera'))
    want = g.call('Want', MATH + 'BooleanAND', A=inf.find_result_pin(), B=act.find_result_pin()).find_result_pin()
    hid = g.call('Hidden', ENGINE + 'SkinnedMeshComponent:IsBoneHiddenByName', target=mesh, BoneName='Head')
    diff = g.call('Diff', MATH + 'NotEqual_BoolBool', A=want, B=hid.find_result_pin())
    b1 = g.branch('Changed', diff.find_result_pin()); b2 = g.branch('WantHide', want)
    hide = g.call('Hide', ENGINE + 'SkinnedMeshComponent:HideBoneByName', target=g.get('FurinaMesh'), BoneName='Head', PhysBodyOption='PBO_None')
    show = g.call('Show', ENGINE + 'SkinnedMeshComponent:UnHideBoneByName', target=g.get('FurinaMesh'), BoneName='Head')
    ev.find_then_pin().break_pin_links(); wire(ev.find_then_pin(), b1.find_execute_pin())
    wire(b1.find_then_pin(), b2.find_execute_pin()); wire(b2.find_then_pin(), hide.find_execute_pin()); wire(b2.find_else_pin(), show.find_execute_pin())
    for p in old:
        for out in (b1.find_else_pin(), hide.find_then_pin(), show.find_then_pin()): wire(out, p)
    BEL.compile_blueprint(pawn); st = pawn.get_editor_property('status'); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    assert unreal.EditorAssetLibrary.save_loaded_asset(pawn, False)
    return str(st)


try: R['result'] = run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'SoldierFPHead.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8'); print('SOLDIER_FP_HEAD', R)
