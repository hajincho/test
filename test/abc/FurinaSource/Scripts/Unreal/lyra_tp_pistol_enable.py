"""헤드리스(-run=pythonscript): 3인칭 권총에서도 FP 와 같은 양손 파지/상체 CR 을 쓰도록 한다. 인자: abp | cr | bp  (각각 별도 실행 권장)
 abp: ABP_Furina 의 Control Rig Alpha 를 항상 1 로 (3인칭 권총도 CR 사용)
 cr : CR_FurinaSecondary  PistW.B 링크를 끊고 1 로(= PistW = PistC: 3인칭에서도 왼손 지지/손가락 고정/롤 보정 적용),
      눈 기준 총 오프셋(PistGOff.Factor)은 FP 전용 유지: PistGW = PistC x RlFpW -> PistGOff.Factor
 bp : ThirdPersonCharacter_BP FBP_ToF(FP 여부 -> 프레임 위치/회전 보간 알파) 를 항상 1 로 (3인칭에서도 FP 와 같은 손-총 관계)
 -> Data/lyra_tp_pistol_enable_<인자>.json"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
MODE = [a for a in sys.argv[1:] if not a.endswith('.py')][0]
R = {'mode': MODE}
def do_abp():
    abp = unreal.load_asset('/Game/Furina/ABP_Furina'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(abp, 'AnimGraph')
    cr = next(n for n in ed.list_all_nodes() if n.get_name() == 'AnimGraphNode_ControlRig_0'); al = cr.find_input_pin('Alpha')
    R['before'] = [c.get_owning_node().get_name()[:30] for c in al.list_connected_pins()]
    al.break_pin_links(); al.set_pin_value('1.0'); R['alpha'] = str(al.get_pin_value())
    del ed, cr, al
    unreal.BlueprintEditorLibrary.compile_blueprint(abp); R['status'] = str(abp.get_editor_property('status'))
    if abp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_asset('/Game/Furina/ABP_Furina', False)
def do_cr():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    N = {str(n.get_node_path()): n for n in g.get_nodes()}
    assert 'PistW' in N and 'PistGOff' in N and 'RlFpW' in N and 'PistC' in N
    if 'PistGW' not in N: c.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathFloatMul', 'Execute', unreal.Vector2D(0, 0), 'PistGW')
    R['l1'] = bool(c.add_link('PistC.Value', 'PistGW.A')); R['l2'] = bool(c.add_link('RlFpW.Result', 'PistGW.B'))
    try: c.break_link('PistGOff.Factor', 'PistGOff.Factor') if False else None
    except Exception: pass
    try: R['brk1'] = bool(c.break_link('PistW.Result', 'PistGOff.Factor'))
    except Exception as e: R['brk1'] = str(e)[:80]
    R['l3'] = bool(c.add_link('PistGW.Result', 'PistGOff.Factor'))
    try: R['brk2'] = bool(c.break_link('RlFpW.Result', 'PistW.B'))
    except Exception as e: R['brk2'] = str(e)[:80]
    R['setB'] = bool(c.set_pin_default_value('PistW.B', '1.0', True, False))
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
def do_bp():
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    n = N['FBP_ToF']; p = n.find_input_pin('InBool'); R['before'] = [c.get_owning_node().get_name() for c in p.list_connected_pins()]
    p.break_pin_links(); p.set_pin_value('true'); R['val'] = str(p.get_pin_value())
    del ed, N, n, p
    import gc; gc.collect()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
def do_loco():
    abp = unreal.load_asset('/Game/Furina/ABP_Furina'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(abp, 'AnimGraph')
    sel = next(n for n in ed.list_all_nodes() if n.get_name().startswith('P220L_PistolSelect')); al = sel.find_input_pin('Alpha')
    R['before'] = [c.get_owning_node().get_name()[:30] for c in al.list_connected_pins()]
    al.break_pin_links(); al.set_pin_value('0.0'); R['alpha'] = str(al.get_pin_value())
    del ed, sel, al
    unreal.BlueprintEditorLibrary.compile_blueprint(abp); R['status'] = str(abp.get_editor_property('status'))
    if abp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_asset('/Game/Furina/ABP_Furina', False)
try: {'abp': do_abp, 'cr': do_cr, 'bp': do_bp, 'loco': do_loco}[MODE]()
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(D + r'\lyra_tp_pistol_enable_%s.json' % MODE, 'w'), indent=1, default=str); print('LYRA_TP_PISTOL_ENABLE', MODE, R.get('saved'), R.get('error', ''))
