"""에디터(편집 전용, 2026-11-21): lyra_hist_fx.py 보정
 1) 권총 애니 13종 다시 가져오기(견착 자세 총을 안쪽으로 20° 기울임, 비조준 -8°) 2) 연기 재질 다시(총열 방향을 HLSL 로) 3) 연기 생성 실행선 다시 잇기
 4) 조준 중 조준경 받침(마운트) 슬롯도 가림 -> Saved/HistFXFix.json("done": true)"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lyra_hist_fx as H
from lyra_fpvm_optics import ENGINE, PAWN, Graph, chain, wire
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
def run():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try:
        out = {}
        for key in H.PISTOLS:
            n = key.upper(); folder = f'/Game/Furina/FPVM/{n}'; skel = unreal.load_asset(f'{folder}/SK_FPVM_{n}').get_editor_property('skeleton')
            for c in H.PCLIPS:
                a = H.import_clip(folder, skel, f'AS_FPVM_{n}_{c}'); assert H.ASSETS.save_loaded_asset(a, False); out[a.get_name()] = round(a.get_play_length(), 3)
        R['clips'] = len(out)
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
    R['smoke'] = H.smoke.__wrapped__() if hasattr(H.smoke, '__wrapped__') else H.smoke()
    # 연기 액터: 크기 되돌리기(SetActorScale3D 1)를 맨 뒤로. 순수 노드(GetActorScale3D)는 쓰는 순간 다시 읽혀서, 먼저 되돌리면 지속·농도가 1로 읽혔음
    sbp = unreal.load_asset(H.FX + '/BP_HistSmoke'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(sbp, 'EventGraph'); nn = {n.get_name(): n for n in ed.list_all_nodes()}
    begin = ed.find_event_node('ReceiveBeginPlay'); order = [nn[k] for k in ('HS_Life', 'HS_MID', 'HS_SetSpawn', 'HS_SetDensity', 'HS_SetLife', 'HS_SetSize', 'HS_Reset')]
    begin.find_then_pin().break_pin_links()
    for n in order: n.find_then_pin().break_pin_links()
    tail = begin.find_then_pin()
    for n in order: wire(tail, n.find_execute_pin()); tail = n.find_then_pin()
    unreal.BlueprintEditorLibrary.compile_blueprint(sbp); assert H.ASSETS.save_loaded_asset(sbp, False); R['smoke_bp'] = 'reordered'
    pawn = unreal.load_asset(PAWN); g = Graph(pawn, 'HFX_')
    ns = g.nodes['HFX_NSShell'].find_then_pin(); nxt = [p for p in ns.list_connected_pins()]; R['ns_next_before'] = [p.get_owning_node().get_name() for p in nxt]
    ns.break_pin_links(); wire(ns, g.nodes['HFX_SmokeSpawn'].find_execute_pin())
    fin = g.nodes['HFX_SmokeFinish'].find_then_pin(); fin.break_pin_links()
    for p in nxt:
        if p.get_owning_node().get_name() != 'HFX_SmokeSpawn': wire(fin, p)
    R['smoke_next'] = [p.get_owning_node().get_name() for p in fin.list_connected_pins()]
    if 'HFX_TubeHide_Mount_K98_Blued' not in g.nodes:
        hid = unreal.load_asset(H.FX + '/M_FPVM_Hidden')
        for last, tag, mat in (('HFX_TubeHide_ZF4_Glass', 'TubeHide_', hid), ('HFX_TubeShow_ZF4_Glass', 'TubeShow_', None)):
            t = g.nodes[last].find_then_pin(); old = list(t.list_connected_pins()); t.break_pin_links()
            nodes = []
            for s_ in H.MOUNT_SLOTS:
                kw = dict(MaterialSlotName=s_); 
                if mat: kw['Material'] = mat
                nodes.append(g.call(tag + s_, ENGINE + 'PrimitiveComponent:SetMaterialByName', target=g.get('FurinaFPVM'), **kw))
            tail = chain(t, nodes)
            for p in old: wire(tail, p)
        R['mounts'] = 'added'
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn); R['status'] = str(pawn.get_editor_property('status'))
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    R['saved'] = bool(H.ASSETS.save_loaded_asset(pawn, False))
try: run()
except Exception: R['error'] = traceback.format_exc()[-1800:]
R['done'] = True; (ROOT / 'Saved' / 'HistFXFix.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8'); print('HIST_FX_FIX', R.get('error', 'ok')[-200:])
