"""에디터(편집 전용, 2026-11-21): 권총 견착 = 팔을 뻗은 자세를 부각(사용자 지정)
 팔 길이(39.2cm)가 이미 거의 끝(38.3)이라 팔을 더 펼 수 없어서, 견착(권총·정조준 아님)일 때 뷰모델 전체를 앞 12cm·아래 1cm 로 밀어
 손과 권총이 눈에서 멀어지고 뻗은 팔(아래팔·위팔)이 화면에 더 길게 보이게 함. 가중치 FurinaVMShW 를 0.033초마다 보간(속도 10)해 부드럽게.
 대기 기준 위치(A) = 기존(STC_ALoc) + (12, 0, -1) × FurinaVMShW -> Saved/PistolShoulderReach.json("done": true)"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, STRINGS, PAWN, Graph, wire
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
MAP = ENGINE + 'BlueprintMapLibrary:'; OFS = (12.0, 0.0, -1.0)
try:
    pawn = unreal.load_asset(PAWN); api = unreal.BlueprintEditorLibrary
    if 'FurinaVMShW' not in {str(n) for n in api.list_member_variable_names(pawn)}:
        assert api.add_member_variable(pawn, 'FurinaVMShW', api.get_basic_type_by_name('real'))
    api.compile_blueprint(pawn)
    g = Graph(pawn, 'PSR_')
    if 'PSR_Store' in g.nodes: R['note'] = 'already installed'
    else:
        val = lambda n: n.find_result_pin()
        def active(name, comp): return val(g.call(name, ENGINE + 'ActorComponent:IsActive', target=g.get(comp)))
        key = g.get('FurinaVMLastKey')
        isp = g.call('IsPistolFind', MAP + 'Map_Find', TargetMap=g.get('FurinaPAnims'), Key=val(g.call('IsPistolKey', STRINGS + 'Concat_StrStr', A=key, B='_IdleS'))).find_output_pin('ReturnValue')
        sh = val(g.call('ShOn', MATH + 'BooleanOR', A=active('ShA', 'FurinaShoulder'), B=active('ShB', 'FurinaShoulderAuto')))
        noads = val(g.call('NoAds', MATH + 'Not_PreBool', A=active('AdsA', 'FurinaADS')))
        want = val(g.call('Want', MATH + 'BooleanAND', A=val(g.call('WantA', MATH + 'BooleanAND', A=isp, B=sh)), B=noads))
        tgt = val(g.call('Target', MATH + 'SelectFloat', A=1.0, B=0.0, bPickA=want))
        wi = val(g.call('Interp', MATH + 'FInterpTo', Current=g.get('FurinaVMShW'), Target=tgt, DeltaTime=0.033, InterpSpeed=10.0))
        store = g.store('Store', 'FurinaVMShW', wi)
        rlw = g.nodes['STC_RlW']; t = rlw.find_then_pin(); nxt = list(t.list_connected_pins()); t.break_pin_links()
        wire(t, store.find_execute_pin())
        for p in nxt: wire(store.find_then_pin(), p)
        aloc = g.nodes['STC_ALoc'].find_result_pin(); dst = list(aloc.list_connected_pins()); aloc.break_pin_links()
        ofs = val(g.call('Ofs', MATH + 'MakeVector', X=OFS[0], Y=OFS[1], Z=OFS[2]))
        add = val(g.call('ALoc2', MATH + 'Add_VectorVector', A=aloc, B=val(g.call('OfsW', MATH + 'Multiply_VectorFloat', A=ofs, B=g.get('FurinaVMShW')))))
        for p in dst: wire(add, p)
        R['into'] = [p.get_owning_node().get_name() for p in dst]; R['after'] = [p.get_owning_node().get_name() for p in nxt]
    api.compile_blueprint(pawn); R['status'] = str(pawn.get_editor_property('status'))
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(pawn, False))
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'PistolShoulderReach.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8')
