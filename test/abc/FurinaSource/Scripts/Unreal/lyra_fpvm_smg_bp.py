"""에디터/헤드리스(편집 전용): MP40·MP38·StG44 1인칭 뷰모델을 캐릭터 BP 에 등록(lyra_fpvm_primary.py 다음, 한 번만).
 1) 무기 키가 바뀔 때(권총 분기 앞에) 키별 분기: 메시 교체 + 재질 덮어쓰기 비우기 + 애니 3개 + 정조준 변환 + 사격 간격 + 탄창 용량(32/32/30)
 2) 사격 간격 변수 FurinaFireInterval: 키가 바뀔 때마다 기본(M4) 값으로 되돌린 뒤 기관단총이면 분당 발사수로(MP40 500, MP38 500, StG44 550)
    발사 타이머(FurinaRifleShot) 의 Time 을 이 변수로 연결
 3) 연사: 역사 무기는 모두 단발이던 조건에서 기관단총 3종 제외
 4) 재장전: 키별 재장전 분기(HistoryReload_Choose_*) 끝에 3종 추가(없으면 재장전이 시작되지 않음)
 -> Saved/FPVMSmgBP.json"""
import json, sys, time
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, STRINGS, PAWN, Graph, chain, wire, literal, view_transform
import lyra_fpvm_primary as P
ROOT = Path(unreal.Paths.project_dir()).resolve(); TOK = '%x' % (int(time.time()) % 0xFFFFF); R = {'tok': TOK}
SMG = {'mp40': ('MP40', 500, 32), 'mp38': ('MP38', 500, 32), 'stg44': ('STG44', 550, 30)}   # TM-E 30-451(1945): MP 9mm 순환 500발/분, StG44 500~600(당시 교범 초당 9발=540)
def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE before editing assets'
    pawn = unreal.load_asset(PAWN); api = unreal.BlueprintEditorLibrary
    if 'FurinaFireInterval' not in [str(n) for n in api.list_member_variable_names(pawn)]:
        assert api.add_member_variable(pawn, 'FurinaFireInterval', api.get_basic_type_by_name('real'))
    api.compile_blueprint(pawn)
    g = Graph(pawn, 'SMG%s_' % TOK)
    if any(n.startswith('SMG') and '_Equip_MP40' in n for n in g.nodes): R['note'] = 'already installed'; return
    for k, (_, _, cap) in SMG.items(): P.CLIP_SIZES[k] = cap
    # ---- 발사 타이머 Time -> 변수
    timer = None
    for n in g.nodes.values():
        if n.get_class().get_name() != 'K2Node_CallFunction': continue
        fp = n.find_input_pin('FunctionName'); tp = n.find_input_pin('Time')
        if fp and fp.is_valid() and tp and tp.is_valid() and str(fp.get_pin_value()) == 'FurinaRifleShot': timer = n; break
    assert timer, 'fire timer not found'
    base = float(str(timer.find_input_pin('Time').get_pin_value()) or 0.075); R['timer'] = [timer.get_name(), base]
    cdo = unreal.get_default_object(pawn.generated_class()); cdo.set_editor_property('FurinaFireInterval', base)
    tp = timer.find_input_pin('Time'); tp.break_pin_links(); wire(g.get('FurinaFireInterval'), tp)
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
                 g.store('FireTime_' + name, 'FurinaVMFireLen', round(0.9 * interval, 4)), g.store('ReloadTime_' + name, 'FurinaVMReloadLen', 2.85),
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
    for k, (name, _, _) in SMG.items():
        br = g.branch('RlBranch_' + name, P.value(g.call('ReloadKey_' + name, STRINGS + 'EqualEqual_StrStr', A=wid2, B=k))); wire(tail, br.find_execute_pin()); tail = br.find_else_pin()
        asset = unreal.load_asset(f'/Game/Furina/FPVM/{name}/AS_FPVM_{name}_Reload')
        plan = [g.store('ReloadClip_' + name, 'FurinaVMAnimReload', asset), g.store('ReloadLen_' + name, 'FurinaVMReloadLen', asset.get_play_length()), g.store('ReloadLoose_' + name, 'FurinaLooseReload', False)]
        wire(chain(br.find_then_pin(), plan), prepare)
    api.compile_blueprint(pawn); R['status'] = str(pawn.get_editor_property('status'))
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert unreal.EditorAssetLibrary.save_loaded_asset(pawn, False); R['saved'] = True
    # 무기창 툴팁
    path = '/Game/Furina/UI/WBP_FurinaWeaponMenu'; menu = unreal.load_asset(path); tree = unreal.find_object(None, path + '.WBP_FurinaWeaponMenu:WidgetTree')
    tips = {'Btn_0_2_0': 'MP40 (연사 500발/분, 32발)', 'Btn_0_2_1': 'MP38 (연사 500발/분, 32발, 개머리판 편 상태)', 'Btn_0_2_2': 'StG44 (연사 550발/분, 30발)', 'Btn_0_1_2': 'StG44 (연사 550발/분, 30발)', 'Btn_0_6_2': 'MP40 (연사 500발/분, 32발)'}
    for w in unreal.ObjectIterator(unreal.Button):
        if w.get_outer() == tree and w.get_name() in tips: w.set_tool_tip_text(unreal.Text('1번 무기 · ' + tips[w.get_name()]))
    api.compile_blueprint(menu); assert unreal.EditorAssetLibrary.save_loaded_asset(menu, False)
try: main()
except Exception:
    import traceback; R['error'] = traceback.format_exc()[-1500:]
(ROOT / 'Saved' / 'FPVMSmgBP.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8'); print('FPVM_SMG_BP', R.get('error', 'ok')[-300:])
