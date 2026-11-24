"""에디터(편집 전용, PIE 아님, 2026-11-23): 캐릭터 통일 = Sparxie(Downloads/Sparxie.zip, 붕괴: 스타레일 MMD, 147.7cm) -> Saved/Sparxie.json
 Blender build_class_on_furina.py -- sparxie build 결과(FBX/Classes/sparxie_cm.fbx)를 병과 캐릭터와 같은 길로 넣는다.
 단계(각 단계 뒤 저장·기록, 다시 돌리면 끝난 단계는 건너뜀):
  assets : 텍스처·재질(lyra_classes.import_class) -> 자기 뼈대 메시 SKM_Sparxie(lyra_class_skeletons.import_class) -> 임시 SK_Class_Sparxie 삭제
  event  : 캐릭터 BP 이벤트 FurinaLookSparxie(메시 교체 -> 재질 덮어쓰기 비우기 -> FurinaLook = 'sparxie')
  start  : BeginPlay 의 LOOK_StartLook(보병 외형)을 FurinaLookSparxie 로, FurinaMesh 기본 메시 = SKM_Sparxie, FurinaLook 기본값 'sparxie'
  menu   : 무기창 '병과 (외형)' 버튼 Look_1..14 모두 비활성(툴팁 '캐릭터 통일로 비활성'), 현재 외형 글자"""
import json, sys, time, traceback, uuid
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib, lyra_fpvm_optics, lyra_classes, lyra_class_skeletons
for _m in (lyra_fpvm_optics, lyra_classes, lyra_class_skeletons): importlib.reload(_m)
from lyra_fpvm_optics import ENGINE, MATH, PAWN, Graph, wire
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]
KEY = next((a.split('=', 1)[1] for a in ARGS if a.startswith('char=')), 'sparxie'); Key = {'sparxie': 'Sparxie', 'robin': 'Robin'}.get(KEY, KEY.title())   # 2026-11-23: Robin 으로 교체(char=robin)
ROOT = Path(unreal.Paths.project_dir()).resolve(); OUTP = ROOT / 'Saved' / f'{Key}.json'
R = json.loads(OUTP.read_text(encoding='utf-8')) if OUTP.exists() else {}
ASSETS = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary
BASE = '/Game/Furina/Classes'; MENU = '/Game/Furina/UI/WBP_FurinaWeaponMenu'
SKM = f'{BASE}/{Key}/SKM_{Key}'; TOK = '%x' % (int(time.time()) % 0xFFFFF)


def save(a): assert ASSETS.save_loaded_asset(a, False), a.get_path_name()


def step_assets():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try:
        out = {'tmp': lyra_classes.import_class(KEY, Key), 'skm': lyra_class_skeletons.import_class(KEY, Key, lyra_class_skeletons.body_bones())}
    finally: unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
    tmp = f'{BASE}/{Key}/SK_Class_{Key}'
    if ASSETS.does_asset_exist(tmp): out['tmp_deleted'] = ASSETS.delete_asset(tmp)
    m = unreal.load_asset(SKM); b = m.get_bounds(); out['height_cm'] = round(b.origin.z + b.box_extent.z, 1)
    out['unset_slots'] = [str(s.material_slot_name) for s in m.materials if not s.material_interface]
    return out


def step_event():
    bp = unreal.load_asset(PAWN); g = Graph(bp, 'LOOK_')
    if 'LOOK_Set_' + Key in g.nodes: return 'already'
    ev = g.editor.add_custom_event_node('FurinaLook' + Key); assert ev; ev.rename('LOOK_Ev_' + Key)
    setm = g.call('Set_' + Key, ENGINE + 'SkeletalMeshComponent:SetSkeletalMeshAsset', target=g.get('FurinaMesh'), NewMesh=unreal.load_asset(SKM))
    num = g.call('Num_' + Key, ENGINE + 'PrimitiveComponent:GetNumMaterials', target=g.get('FurinaMesh'))
    last = g.call('Last_' + Key, MATH + 'Subtract_IntInt', A=num.find_result_pin(), B=1)
    loop = g.editor.add_macro_node('/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForLoop'); loop.rename('LOOK_Loop_' + Key)
    loop.find_input_pin('FirstIndex').set_pin_value('0'); wire(last.find_result_pin(), loop.find_input_pin('LastIndex'))
    clear = g.call('Clear_' + Key, ENGINE + 'PrimitiveComponent:SetMaterial', target=g.get('FurinaMesh'))
    wire(loop.find_output_pin('Index'), clear.find_input_pin('ElementIndex')); wire(loop.find_output_pin('LoopBody'), clear.find_execute_pin())
    store = g.store('Store_' + Key, 'FurinaLook', KEY)
    wire(ev.find_then_pin(), setm.find_execute_pin()); wire(setm.find_then_pin(), loop.find_input_pin('execute')); wire(loop.find_output_pin('Completed'), store.find_execute_pin())
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    save(bp); return str(st)


def step_start():
    bp = unreal.load_asset(PAWN); g = Graph(bp, 'LOOK_'); out = {}
    old = g.nodes['LOOK_StartLook']
    out['old_function'] = old.get_name()
    ins = list(old.find_execute_pin().list_connected_pins()); outs = list(old.find_then_pin().list_connected_pins())
    out['in'] = [p.get_owning_node().get_name() for p in ins]; out['out'] = [p.get_owning_node().get_name() for p in outs]   # 실패해도 다시 이을 수 있게 먼저 기록
    R['start_links'] = out; OUTP.write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
    new = g.editor.add_call_function_node(bp.generated_class().get_path_name() + ':FurinaLook' + Key); assert new
    old.rename('Discarded_' + uuid.uuid4().hex); new.rename('LOOK_StartLook')
    for p in ins: wire(p, new.find_execute_pin())
    for p in outs: wire(new.find_then_pin(), p)
    for p in old.list_all_pins(): p.break_pin_links()
    g.editor.remove_nodes([old])
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    comp = next(lib.get_associated_object(lib.get_data(h)) for h in sub.k2_gather_subobject_data_for_blueprint(bp) if str(lib.get_variable_name(lib.get_data(h))) == 'FurinaMesh')
    comp.set_editor_property('skeletal_mesh_asset', unreal.load_asset(SKM))
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    unreal.get_default_object(unreal.SystemLibrary).call_method('SetStringPropertyByName', (unreal.get_default_object(bp.generated_class()), 'FurinaLook', KEY))
    save(bp); out['status'] = str(st); out['default_mesh'] = comp.get_editor_property('skeletal_mesh_asset').get_name(); return out


def step_menu():
    wbp = unreal.load_asset(MENU); wt = unreal.find_object(None, MENU + '.WBP_FurinaWeaponMenu:WidgetTree')
    W = {o.get_name(): o for o in unreal.ObjectIterator(unreal.Widget) if o.get_outer() == wt}
    off = []
    for n, w in W.items():
        if n.startswith('Look_') and n[5:].isdigit():
            w.set_is_enabled(False); w.set_tool_tip_text(unreal.Text(f'캐릭터 통일({Key})로 비활성')); off.append(n)
    if 'LookCurrent' in W: W['LookCurrent'].set_text(unreal.Text(f'현재 외형: {Key} (통일, 병과 선택 비활성)'))
    BEL.compile_blueprint(wbp); s = wbp.get_editor_property('status'); assert s != unreal.BlueprintStatus.BS_ERROR, str(s)
    save(wbp); return {'disabled': sorted(off, key=lambda x: int(x[5:])), 'status': str(s)}


try:
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    only = [a for a in ARGS if not a.startswith('char=')]
    for name, fn in (('assets', step_assets), ('event', step_event), ('start', step_start), ('menu', step_menu)):
        if only and name not in only[0].split('+'): continue
        if R.get(name + '_done') and not only: continue
        R[name] = fn(); R[name + '_done'] = True; OUTP.write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
    R['error'] = None
except Exception:
    R['error'] = traceback.format_exc()[-1800:]
OUTP.write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8'); print('SPARXIE', json.dumps(R, default=str, ensure_ascii=False)[-2500:])
