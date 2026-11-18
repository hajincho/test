"""Lyra 에디터(`py <파일>`, PIE 중지 상태): lyra_fp_mag_base_grab3.py 후속 - 높이 제한을 켜는 시점.
측정(3차): 쥐는 중(MagState 0->1)에도 높이 제한이 일부 켜져서, 옆에서 다가오던 손(부드럽게 거른 값이 아직 P_G 와 어긋남)이 탄창이 붙기 전에 11cm 아래로 눌렸다.
수정: 제한 가중치 = max(붙은 뒤(MagState>=0.98), 놓는 중(MagState 감소 중) x MagState) -> 쥐는 중에는 0, 들고 있는 동안/놓을 때(아래에서 곧게 올라갈 때)는 켜짐.
노드: RcStep/RcDms/RcDec/RcRel/RcHold2 (RcW.A 를 RcHold -> RcHold2 로). -> Data/lyra_fp_mag_base_grab4.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_mag_base_grab4.json'
R = {}
U = '/Script/ControlRig.RigUnit_'
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    L = []
    def link(a, b):
        try: L.append(['+', a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append(['+', a, b, 'err ' + str(e)[:80]])
    if 'RcHold2' not in nodes():
        mk('MathFloatRemap', 'RcStep', SourceMinimum='0.97', SourceMaximum='0.99', TargetMinimum='0', TargetMaximum='1', bClamp='True')
        mk('DeltaFromPreviousFloat', 'RcDms')
        mk('MathFloatRemap', 'RcDec', SourceMinimum='0.0', SourceMaximum='-0.0005', TargetMinimum='0', TargetMaximum='1', bClamp='True')
        mk('MathFloatMul', 'RcRel'); mk('MathFloatMax', 'RcHold2')
        link('RcMagC.Value', 'RcStep.Value'); link('RcMagC.Value', 'RcDms.Value'); link('RcDms.Delta', 'RcDec.Value')
        link('RcHold.Result', 'RcRel.A'); link('RcDec.Result', 'RcRel.B')
        link('RcStep.Result', 'RcHold2.A'); link('RcRel.Result', 'RcHold2.B')
        try: L.append(['x', bool(c.break_link('RcHold.Result', 'RcW.A'))])
        except Exception as e: L.append(['x', 'err ' + str(e)[:60]])
        link('RcHold2.Result', 'RcW.A')
    R['links'] = L
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_MAG_BASE4', R.get('saved'), R.get('error', '')[-200:])
