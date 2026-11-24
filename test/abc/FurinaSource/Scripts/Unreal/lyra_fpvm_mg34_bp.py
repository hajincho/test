"""에디터(편집 전용, 2026-11-22): MG34 1인칭(들고 쏘기, 50발 드럼) 가져오기 + 캐릭터 BP 등록(lyra_fpvm_smg_bp.py 와 같은 방식, 발사 타이머 연결은 이미 있음)
 1) FBX/FPVM/SK_FPVM_MG34 + AS_FPVM_MG34_<Idle|Fire|Reload> 가져오기(lyra_fpvm_reimport.smg), 병과 팔 슬롯
 2) 키 'mg34' 분기: 메시·애니·정조준·사격 간격(분당 900)·탄 50, 연사 허용, 재장전 분기(드럼 교체 4.0초) -> Saved/FPVMMg34BP.json"""
import json, sys, time
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, STRINGS, PAWN, Graph, chain, wire, literal, view_transform
import lyra_fpvm_primary as P
import lyra_fpvm_reimport as RI
ROOT = Path(unreal.Paths.project_dir()).resolve(); TOK = '%x' % (int(time.time()) % 0xFFFFF); R = {'tok': TOK}
SMG = {'mg34': ('MG34', 900, 50)}   # MG34 순환 속도 800~900발/분(Wikipedia·Athlon), 50발 탄띠 드럼   # TM-E 30-451(1945): MP 9mm 순환 500발/분, StG44 500~600(당시 교범 초당 9발=540)


def restore_reload_route(pawn):
    graph = Graph(pawn)
    names = ('MG34', 'MP40', 'MP38', 'STG44', 'PANZERFAUST', 'PANZERSCHRECK')
    branches = {}
    for key in names:
        node, = (node for name, node in graph.nodes.items() if name.endswith('_RlBranch_' + key))
        branches[key] = node
    source = graph.nodes['HistoryReload_Choose_pp'].find_else_pin()
    assert [pin.get_owning_node() for pin in source.list_connected_pins()] == [branches['MG34']]
    for first, second in zip(names[1:], names[2:]):
        linked = branches[first].find_else_pin().list_connected_pins()
        assert [pin.get_owning_node() for pin in linked] == [branches[second]], (first, second)
    fallback = branches['MG34'].find_else_pin()
    current = [pin.get_owning_node() for pin in fallback.list_connected_pins()]
    if current == [branches['MP40']]:
        return False
    assert not current and not branches['MP40'].find_execute_pin().list_connected_pins()
    wire(fallback, branches['MP40'].find_execute_pin())
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert unreal.EditorAssetLibrary.save_loaded_asset(pawn, False)
    return True


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE before editing assets'
    pawn = unreal.load_asset(PAWN); api = unreal.BlueprintEditorLibrary
    if 'route-only' in sys.argv[1:]:
        R['route_saved'] = restore_reload_route(pawn)
        return
    if 'FurinaFireInterval' not in [str(n) for n in api.list_member_variable_names(pawn)]:
        assert api.add_member_variable(pawn, 'FurinaFireInterval', api.get_basic_type_by_name('real'))
    api.compile_blueprint(pawn)
    g = Graph(pawn, 'SMG%s_' % TOK)
    if any('_Equip_MG34' in n for n in g.nodes): R['note'] = 'already installed'; return
    if any(n.startswith('SMG') and '_Equip_MG34' in n for n in g.nodes): R['note'] = 'already installed'; return
    for k, (_, _, cap) in SMG.items(): P.CLIP_SIZES[k] = cap
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); cv = 'Interchange.FeatureFlags.Import.FBX'
    unreal.SystemLibrary.execute_console_command(world, cv + ' 0')
    try: R['import'] = RI.smg('mg34')
    finally: unreal.SystemLibrary.execute_console_command(world, cv + ' 1')
    base = float(unreal.get_default_object(pawn.generated_class()).get_editor_property('FurinaFireInterval'))
    # ---- 키 바뀜 분기(권총 분기 앞)
    vm = g.get('FurinaFPVM'); key = g.get('FurinaPrimaryKey')
    swap = g.locate('VW_S_7_').find_then_pin(); after = list(swap.list_connected_pins()); swap.break_pin_links()
    reset = g.store('IntervalDefault', 'FurinaFireInterval', base); wire(swap, reset.find_execute_pin()); nxt = reset.find_then_pin()
    update = g.locate('VM_Br_12_').find_execute_pin()
    for k, (name, rpm, cap) in SMG.items():
        folder = f'/Game/Furina/FPVM/{name}'
        br = g.branch('Is_' + name, P.value(g.call('Key_' + name, STRINGS + 'EqualEqual_StrStr', A=key, B=k))); wire(nxt, br.find_execute_pin()); nxt = br.find_else_pin()
        acts = [g.call('Equip_' + name, ENGINE + 'SkeletalMeshComponent:SetSkeletalMeshAsset', target=vm, NewMesh=unreal.load_asset(f'{folder}/SK_FPVM_{name}'))]
        acts += [g.call(f'ResetMaterial_{name}_{i}', ENGINE + 'PrimitiveComponent:SetMaterial', target=vm, ElementIndex=i) for i in range(10)]
        for label in ('Idle', 'Fire', 'Reload'): acts.append(g.store(f'{label}_{name}', 'FurinaVMAnim' + label, unreal.load_asset(f'{folder}/AS_FPVM_{name}_{label}')))
        loc, rot = view_transform(k); interval = 60.0 / rpm
        acts += [g.store('ADSLocation_' + name, 'FurinaVMAdsLoc', loc), g.store('ADSRotation_' + name, 'FurinaVMAdsRot', rot),
                 g.store('FireTime_' + name, 'FurinaVMFireLen', round(0.9 * interval, 4)), g.store('ReloadTime_' + name, 'FurinaVMReloadLen', 4.0),
                 g.store('Interval_' + name, 'FurinaFireInterval', round(interval, 4)), g.store('NoScope_' + name, 'FurinaScopeZoom', 1.), g.store('Valid_' + name, 'FurinaVMValid', True)]
        P.weapon_ammo(g, chain(br.find_then_pin(), acts), k, update)
    for t in after: wire(nxt, t)
    # ---- 연사: 역사 무기 단발 조건에서 3종 제외
    single = g.nodes['HistoryPrimary_SingleShot']; a = single.find_input_pin('A'); src = list(a.list_connected_pins())[0]; a.break_pin_links()
    wid = g.get('FurinaGameWeaponId'); auto = None
    for k in SMG:
        e = P.value(g.call('Auto_' + k, STRINGS + 'EqualEqual_StrStr', A=wid, B=k)); auto = e if auto is None else P.value(g.call('AutoOr_' + k, MATH + 'BooleanOR', A=auto, B=e))
    notauto = P.value(g.call('NotAuto', MATH + 'Not_PreBool', A=auto)); wire(P.and_(g, 'HistoricSemi', src, notauto), a)
    # ---- 재장전 분기 추가
    tail = g.nodes['HistoryReload_Choose_pp'].find_else_pin(); prepare = g.nodes['HistoryReload_PrepareProp'].find_execute_pin(); wid2 = g.get('FurinaGameWeaponId')
    downstream = list(tail.list_connected_pins())
    tail.break_pin_links()
    for k, (name, _, _) in SMG.items():
        br = g.branch('RlBranch_' + name, P.value(g.call('ReloadKey_' + name, STRINGS + 'EqualEqual_StrStr', A=wid2, B=k))); wire(tail, br.find_execute_pin()); tail = br.find_else_pin()
        asset = unreal.load_asset(f'/Game/Furina/FPVM/{name}/AS_FPVM_{name}_Reload')
        plan = [g.store('ReloadClip_' + name, 'FurinaVMAnimReload', asset), g.store('ReloadLen_' + name, 'FurinaVMReloadLen', asset.get_play_length()), g.store('ReloadLoose_' + name, 'FurinaLooseReload', False)]
        wire(chain(br.find_then_pin(), plan), prepare)
    for destination in downstream:
        wire(tail, destination)
    api.compile_blueprint(pawn); R['status'] = str(pawn.get_editor_property('status'))
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert unreal.EditorAssetLibrary.save_loaded_asset(pawn, False); R['saved'] = True
    # 무기창 툴팁
    path = '/Game/Furina/UI/WBP_FurinaWeaponMenu'; menu = unreal.load_asset(path); tree = unreal.find_object(None, path + '.WBP_FurinaWeaponMenu:WidgetTree')
    tips = {'Btn_0_4_1': 'MG34 (들고 쏘기, 연사 900발/분, 50발 드럼)'}
    for w in unreal.ObjectIterator(unreal.Button):
        if w.get_outer() == tree and w.get_name() in tips: w.set_tool_tip_text(unreal.Text('1번 무기 · ' + tips[w.get_name()]))
    api.compile_blueprint(menu); assert unreal.EditorAssetLibrary.save_loaded_asset(menu, False)
try: main()
except Exception:
    import traceback; R['error'] = traceback.format_exc()[-1500:]
report = 'FPVMReloadRoute.json' if 'route-only' in sys.argv[1:] else 'FPVMMg34BP.json'
(ROOT / 'Saved' / report).write_text(json.dumps(R, indent=1, default=str), encoding='utf-8'); print('FPVM_MG34_BP', R.get('error', 'ok')[-300:])
