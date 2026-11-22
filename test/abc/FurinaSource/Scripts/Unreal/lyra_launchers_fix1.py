"""에디터(편집 전용, 2026-11-21): 대전차 화기 보정 1
 1) 발사체 적중 기록(로그 'LCH_HIT 대상 / 부품 / 위치') — 탄두가 발사 직후 무엇에 맞는지 조사
 2) 휠 영점 바꾸기를 이름으로 부를 수 있는 이벤트 FurinaZeroUp / FurinaZeroDown(휠 입력과 같은 분기로) — 자동 확인용
 -> Saved/LaunchersFix1.json"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, STRINGS, PAWN, Graph, wire
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}; API = unreal.BlueprintEditorLibrary; SYSL = ENGINE + 'KismetSystemLibrary:'
def val(n): return n.find_result_pin()
try:
    for bpn in ('BP_FurinaPzfWarhead', 'BP_FurinaPzsRocket'):
        bp = unreal.load_asset('/Game/Furina/FP/' + bpn); g = Graph(bp, 'LCH_')
        if 'LCH_Dbg' not in g.nodes:
            hit = g.nodes['K2Node_FPB_Hit']; t = hit.find_then_pin(); nxt = list(t.list_connected_pins()); t.break_pin_links()
            a = val(g.call('DbgA', SYSL + 'GetObjectName', Object=hit.find_output_pin('Other'))); c = val(g.call('DbgC', SYSL + 'GetObjectName', Object=hit.find_output_pin('OtherComp')))
            l = val(g.call('DbgL', STRINGS + 'Conv_VectorToString', InVec=hit.find_output_pin('HitLocation')))
            s = val(g.call('Dbg3', STRINGS + 'Concat_StrStr', A=val(g.call('Dbg2', STRINGS + 'Concat_StrStr', A=val(g.call('Dbg1', STRINGS + 'Concat_StrStr', A='LCH_HIT ' + bpn + ' ', B=a)), B=val(g.call('Dbg1b', STRINGS + 'Concat_StrStr', A=' / ', B=c)))), B=val(g.call('Dbg2b', STRINGS + 'Concat_StrStr', A=' @ ', B=l))))
            pr = g.call('Dbg', SYSL + 'PrintString', InString=s, bPrintToScreen=False, bPrintToLog=True)
            wire(t, pr.find_execute_pin())
            for p in nxt: wire(pr.find_then_pin(), p)
        API.compile_blueprint(bp); assert unreal.EditorAssetLibrary.save_loaded_asset(bp, False); R[bpn] = str(bp.get_editor_property('status'))
    pawn = unreal.load_asset(PAWN); g = Graph(pawn, 'LCH_')
    for ev_name, br in (('FurinaZeroUp', 'LCH_WheelUp'), ('FurinaZeroDown', 'LCH_WheelDn')):
        if 'LCH_Ev' + ev_name not in g.nodes:
            ev = g.editor.add_custom_event_node(ev_name); assert ev, ev_name; ev.rename('LCH_Ev' + ev_name)
            wire(ev.find_then_pin(), g.nodes[br].find_execute_pin())
    API.compile_blueprint(pawn); R['pawn'] = str(pawn.get_editor_property('status')); assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert unreal.EditorAssetLibrary.save_loaded_asset(pawn, False)
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'LaunchersFix1.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8')
