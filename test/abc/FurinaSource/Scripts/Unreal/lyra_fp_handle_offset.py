"""Lyra 에디터(`py <파일> [dx dy dz]`): 1인칭 장전손잡이 구간의 왼손 위치를 3인칭과 같게 맞춘다.
 lyra_fp_handle_fade.py 로 1인칭 탄창 보정(RlDeltaFp 등)을 끈 뒤에도 1인칭 손목이 3인칭 규칙(손목 = 곡선 변위 + (-1.91, 9.83, 4.28))보다 (+4.3, +4.2, -2.4)cm 어긋나 있었다
 (lyra_empty_reload_probe_hFP4.json: 손잡이 유지 구간 손목 - 곡선 변위 = (2.4, 14.0, 1.9)).  -> 손잡이 구간(HandleFp)에만 1인칭 가중치로 (-4.3, -4.2, +2.4)를 더한다.
 노드: RlEnvH(= RlEnv x RlFpW), RlEnvFpH(x HandleFp), RlDeltaFpH(벡터), RLV4(= RLV3 + RlDeltaFpH) -> LHandOff3.B.   인자로 오프셋 변경(이미 있으면 값만 바꿈).   -> Data/lyra_fp_handle_offset.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_handle_offset.json'
U = '/Script/ControlRig.RigUnit_'
nums = [float(a) for a in sys.argv[1:] if a.replace('.', '', 1).replace('-', '', 1).isdigit()]
OFS = tuple(nums[:3]) if len(nums) >= 3 else (-4.3, -4.2, 2.4)
R = {'offset': OFS}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('RlEnv', 'RlFpW', 'RlHC', 'RLV3', 'LHandOff3'): assert need in N, 'missing ' + need
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    if 'RLV4' not in N:
        mk('MathFloatMul', 'RlEnvH'); mk('MathFloatMul', 'RlEnvFpH'); mk('MathVectorScale', 'RlDeltaFpH'); mk('MathVectorAdd', 'RLV4')
        link('RlEnv.Result', 'RlEnvH.A'); link('RlFpW.Result', 'RlEnvH.B'); link('RlEnvH.Result', 'RlEnvFpH.A'); link('RlHC.Value', 'RlEnvFpH.B')
        link('RlEnvFpH.Result', 'RlDeltaFpH.Factor'); link('RLV3.Result', 'RLV4.A'); link('RlDeltaFpH.Result', 'RLV4.B')
        srcs = []
        for p in N['LHandOff3'].get_pins():
            if str(p.get_name()) == 'B': srcs = [str(s.get_pin_path()) for s in p.get_linked_source_pins()]
        R['old_b_src'] = srcs
        for s in srcs:
            if s.startswith('RLV4'): continue
            try: c.break_link(s, 'LHandOff3.B')
            except Exception as e: L.append(['break', s, str(e)[:60]])
        link('RLV4.Result', 'LHandOff3.B')
    R['set'] = bool(c.set_pin_default_value('RlDeltaFpH.Value', '(X=%.4f,Y=%.4f,Z=%.4f)' % OFS, True, False))
    R['links'] = L
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_HANDLE_OFFSET', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
