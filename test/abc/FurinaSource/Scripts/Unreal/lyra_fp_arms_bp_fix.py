"""헤드리스(에디터 세션당 한 번): lyra_fp_arms_bp.py 로 넣은 FPA_* 로직 수정.
 원인: UE5.8 에서 add_call_function_node('Subtract_DoubleDouble'/'Less_DoubleDouble'/'LessEqual_DoubleDouble') 은 승격 연산자(float - float 등)가 되어
       set_pin_value 상수가 비어 있었다(0.033 감소 안 됨 -> LHold 0.8 고정, 거리 < '' -> 항상 거짓).  IsBoneHiddenByName 은 비순수(실행 핀) 함수라 실행선에 없으면 항상 거짓.
 수정: LHold 감소 = FInterpTo_Constant(현재, 0, 0.033, 1.0) / 거리 < 0.5 = InRange(거리, -1, 0.5) / LHold <= 0 = InRange(LHold, -1, 0)
       IsBoneHiddenByName(R/L) 를 실행선에 넣음(SetVisibility L -> HidR -> BrR ... -> HidL -> BrL).   -> Data/lyra_fp_arms_bp_fix.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'log': []}
def run():
    bp = unreal.load_asset(PAWN)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    R['ed_methods'] = [m for m in dir(ed) if 'node' in m.lower() or 'remove' in m.lower()]
    K = '/Script/Engine.KismetMathLibrary:'
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name); return p
    def link(a, b):
        assert CONN(a, b), ('link', a.get_owning_node().get_name(), a.get_pin_name(), '->', b.get_owning_node().get_name(), b.get_pin_name())
    def fn(name, path, **vals):
        n = ed.add_call_function_node(path); assert n, path; n.rename(name)
        for k, v in vals.items(): pin(n, k).set_pin_value(str(v)); R['log'].append([name, k, str(pin(n, k).get_pin_value())])
        return n
    def kill(nm):
        n = N.get(nm)
        if n is None: return
        for p in n.list_all_pins(): p.break_pin_links()
        done = False
        for m in ('remove_node', 'delete_node', 'destroy_node'):
            if hasattr(ed, m):
                try: getattr(ed, m)(n); done = True; break
                except Exception as e: R['log'].append(['kill err', nm, str(e)[:80]])
        if not done: n.rename(nm.replace('FPA_', 'FPAold_'))
        R['log'].append(['killed', nm, done])
    if 'FPA_HoldDecay' in N: R['note'] = 'already fixed'; return
    # 1) LHold 감소
    kill('FPA_HoldDec'); kill('FPA_HoldMax0')
    dec = fn('FPA_HoldDecay', K + 'FInterpTo_Constant', Target=0.0, DeltaTime=0.033, InterpSpeed=1.0)
    link(pin(N['FPA_HoldG'], 'FurinaFPArmLHold', True), pin(dec, 'Current')); link(pin(dec, 'ReturnValue', True), pin(N['FPA_HoldSel'], 'B'))
    # 2) 거리 < 0.5, LHold <= 0
    kill('FPA_Near'); kill('FPA_HoldDone')
    nr = fn('FPA_NearR', K + 'InRange_FloatFloat', Min=-1.0, Max=0.5, InclusiveMin='true', InclusiveMax='false')
    link(pin(N['FPA_LWDist'], 'ReturnValue', True), pin(nr, 'Value')); link(pin(nr, 'ReturnValue', True), pin(N['FPA_LOk'], 'B'))
    hd = fn('FPA_HoldDoneR', K + 'InRange_FloatFloat', Min=-1.0, Max=0.0001, InclusiveMin='true', InclusiveMax='true')
    link(pin(N['FPA_HoldG2'], 'FurinaFPArmLHold', True), pin(hd, 'Value')); link(pin(hd, 'ReturnValue', True), pin(N['FPA_LOk'], 'A'))
    # 3) IsBoneHiddenByName 실행선
    vl = N['FPA_VisL']; hr = N['FPA_HidR']; brr = N['FPA_BrR']; hl = N['FPA_HidL']; brl = N['FPA_BrL']
    vl.find_then_pin().break_pin_links(); link(vl.find_then_pin(), hr.find_execute_pin()); link(hr.find_then_pin(), brr.find_execute_pin())
    srcs = list(brl.find_execute_pin().list_connected_pins()); R['brl_srcs'] = [p.get_owning_node().get_name() + '.' + str(p.get_pin_name()) for p in srcs]
    brl.find_execute_pin().break_pin_links()
    for s in srcs: link(s, hl.find_execute_pin())
    link(hl.find_then_pin(), brl.find_execute_pin())
    R['fixed'] = True
    del ed, N
    import gc; gc.collect()
def finish():
    bp = unreal.load_asset(PAWN)
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
try: run(); finish()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\lyra_fp_arms_bp_fix.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_ARMS_BP_FIX', R.get('status'), R.get('error', ''))
import gc; gc.collect()
