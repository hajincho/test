"""에디터(편집 전용, PIE 아님, 2026-11-22): 병과 캐릭터별 1인칭 팔 = 1인칭 무기 메시 안의 팔 슬롯 고르기 -> Saved/ClassFPArms2.json("done": true)
 Blender(fpvm_lib.class_arm_objects)가 모든 1인칭 무기 메시(SK_FPVM_*)에 캐릭터 7종 팔을 같은 팔 뼈대로 넣음(재질 슬롯 CA<Key>_MatNN).
 (먼저 시도한 별도 팔 메시 + 리더 포즈는 이 뷰모델에서 팔이 축소·엇나가 보이지 않아 버림: lyra_class_fp_arms.py / _relead.py 의 FPAC_/FPAR_ 노드·FurinaFPArmsChar 컴포넌트 삭제)
 1) 모든 SK_FPVM_* 의 CA<Key>_MatNN 슬롯 = /Game/Furina/Classes/<Key>/Materials/MI_<Key>_MatNN
 2) 시점 갱신(FurinaViewUpdate, 0.05초)마다 (외형 + 무기 메시)가 바뀌었으면 FurinaFPVM 의 재질 슬롯을 돌며:
    CA 슬롯 = 지금 외형(대소문자 무시 'CA'+FurinaLook 로 시작)이면 원래 재질, 아니면 가림 재질(M_FPVM_Hidden)
    Furina_ 슬롯 = 외형이 푸리나면 원래 재질, 아니면 가림 재질. 무기 슬롯은 건드리지 않음."""
import json, sys, traceback, uuid
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib, lyra_fpvm_optics; importlib.reload(lyra_fpvm_optics)
from lyra_fpvm_optics import ENGINE, MATH, PAWN, STRINGS, Graph, wire, chain
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
ASSETS = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary
HIDDEN = '/Game/Furina/FX/M_FPVM_Hidden'; SYS = ENGINE + 'KismetSystemLibrary:'


def assign_slots():
    ar = unreal.AssetRegistryHelpers.get_asset_registry(); out = {}
    for a in ar.get_assets_by_path('/Game/Furina/FPVM', True):
        if str(a.asset_class_path.asset_name) != 'SkeletalMesh' or not str(a.asset_name).startswith('SK_FPVM_'): continue
        m = unreal.load_asset(str(a.package_name)); slots = list(m.materials); n = 0; miss = []
        for s in slots:
            sn = str(s.material_slot_name)
            if not sn.startswith('CA'): continue
            Key, mat = sn[2:].split('_', 1)
            mi = unreal.load_asset(f'/Game/Furina/Classes/{Key}/Materials/MI_{Key}_{mat}')
            if mi: s.material_interface = mi; n += 1
            else: miss.append(sn)
        if n or miss:
            m.set_editor_property('materials', slots); assert ASSETS.save_loaded_asset(m, False)
        out[str(a.asset_name)] = [n, miss]
    return out


def discard(editor, nodes):
    for n in nodes:
        for p in n.list_all_pins(): p.break_pin_links()
        n.rename('Discarded_' + uuid.uuid4().hex)
    if nodes: editor.remove_nodes(nodes)
    return len(nodes)


def pawn():
    bp = unreal.load_asset(PAWN); g = Graph(bp, 'FPAS_'); out = {}
    if 'FPAS_Loop' in g.nodes: return 'exists'
    # 이전 방식(별도 팔 메시) 노드 삭제 + 시점 갱신 흐름 복구
    ev = g.editor.find_event_node('FurinaViewUpdate')
    old = [n for k, n in g.nodes.items() if k.startswith(('FPAC_', 'FPAR_'))]
    after = g.nodes['LOOKH_Changed'].find_execute_pin()
    out['removed'] = discard(g.editor, old)
    g = Graph(bp, 'FPAS_')
    for k, n in g.nodes.items():   # 외형 이벤트의 저장 노드 뒤가 끊겼는지(원래 끝) 확인용
        pass
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    hs = {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    if 'FurinaFPArmsChar' in hs:
        root = sub.k2_gather_subobject_data_for_blueprint(bp)[0]
        out['comp_deleted'] = sub.delete_subobject(root, hs['FurinaFPArmsChar'], bp)
    for v in ('FurinaArmsLeaderMesh',):   # 이전 방식 변수(더는 안 씀)
        if v in [str(x) for x in BEL.list_member_variable_names(bp)]:
            try: g.editor.remove_member_variable(v)
            except Exception as e: out['var_keep'] = str(e)[:80]
    if 'FurinaArmsState' not in [str(x) for x in BEL.list_member_variable_names(bp)]:
        BEL.add_member_variable(bp, 'FurinaArmsState', BEL.get_basic_type_by_name('string'))
    BEL.compile_blueprint(bp); g = Graph(bp, 'FPAS_')
    ev = g.editor.find_event_node('FurinaViewUpdate'); ev.find_then_pin().break_pin_links()
    vm = lambda: g.get('FurinaFPVM')
    mesh = g.call('Mesh', ENGINE + 'SkeletalMeshComponent:GetSkeletalMeshAsset', target=vm()).find_result_pin()
    path = g.call('MeshPath', SYS + 'GetPathName', Object=mesh).find_result_pin()
    state = g.call('State', STRINGS + 'Concat_StrStr', A=g.get('FurinaLook'), B=path).find_result_pin()
    changed = g.call('Changed', STRINGS + 'NotEqual_StrStr', A=state, B=g.get('FurinaArmsState')).find_result_pin()
    br = g.branch('IfChanged', changed)
    names = g.call('Slots', ENGINE + 'PrimitiveComponent:GetMaterialSlotNames', target=vm()).find_result_pin()
    loop = g.editor.add_macro_node('/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop'); loop.rename('FPAS_Loop')
    wire(names, loop.find_input_pin('Array'))
    nm = g.call('SlotStr', STRINGS + 'Conv_NameToString', InName=loop.find_output_pin('Array Element')).find_result_pin()
    is_ca = g.call('IsCA', STRINGS + 'StartsWith', SourceString=nm, InPrefix='CA').find_result_pin()
    is_fur = g.call('IsFur', STRINGS + 'StartsWith', SourceString=nm, InPrefix='Furina_').find_result_pin()
    prefix = g.call('Mine', STRINGS + 'Concat_StrStr', A='CA', B=g.get('FurinaLook')).find_result_pin()
    mine = g.call('IsMine', STRINGS + 'StartsWith', SourceString=nm, InPrefix=prefix).find_result_pin()
    not_mine = g.call('NotMine', MATH + 'Not_PreBool', A=mine).find_result_pin()
    ca_hide = g.call('CAHide', MATH + 'BooleanAND', A=is_ca, B=not_mine).find_result_pin()
    not_f = g.call('NotFurina', STRINGS + 'NotEqual_StrStr', A=g.get('FurinaLook'), B='furina').find_result_pin()
    fur_hide = g.call('FurHide', MATH + 'BooleanAND', A=is_fur, B=not_f).find_result_pin()
    hide = g.call('Hide', MATH + 'BooleanOR', A=ca_hide, B=fur_hide).find_result_pin()
    arms = g.call('IsArms', MATH + 'BooleanOR', A=is_ca, B=is_fur).find_result_pin()
    b_arms = g.branch('ArmsSlot', arms); b_hide = g.branch('HideSlot', hide)
    set_h = g.call('SetHidden', ENGINE + 'PrimitiveComponent:SetMaterialByName', target=vm(), MaterialSlotName=loop.find_output_pin('Array Element'), Material=unreal.load_asset(HIDDEN))
    set_d = g.call('SetDefault', ENGINE + 'PrimitiveComponent:SetMaterialByName', target=vm(), MaterialSlotName=loop.find_output_pin('Array Element'))
    store = g.store('StoreState', 'FurinaArmsState', state)
    wire(ev.find_then_pin(), br.find_execute_pin()); wire(br.find_then_pin(), loop.find_input_pin('Exec'))
    wire(loop.find_output_pin('LoopBody'), b_arms.find_execute_pin()); wire(b_arms.find_then_pin(), b_hide.find_execute_pin())
    wire(b_hide.find_then_pin(), set_h.find_execute_pin()); wire(b_hide.find_else_pin(), set_d.find_execute_pin())
    wire(loop.find_output_pin('Completed'), store.find_execute_pin())
    for p in (store.find_then_pin(), br.find_else_pin()): wire(p, after)
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    assert ASSETS.save_loaded_asset(bp, False); out['status'] = str(st)
    return out


def run():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    only = [a for a in sys.argv[1:] if not a.endswith('.py')]
    if not only or 'slots' in only[0]: R['slots'] = assign_slots()
    if not only or 'pawn' in only[0]: R['pawn'] = pawn()


try: run()
except Exception: R['error'] = traceback.format_exc()[-1800:]
R['done'] = True; (ROOT / 'Saved' / 'ClassFPArms2.json').write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
print('CLASS_FP_ARMS2', json.dumps(R, default=str, ensure_ascii=False)[:2500])
