"""Lyra 에디터(`py <파일>`, 새로 시작한 에디터에서 한 번): 1인칭에서 긴급 재장전의 장전손잡이 구간에는 탄창 잡기용 1인칭 보정을 끈다.
 원인(PIE 측정 lyra_empty_reload_probe_hFP.json): 1인칭에서는 재장전 중 가중치 RlEnvFp(= 재장전 곡선 x (1 - TpW))가 왼손 목표에 상수 오프셋 RlDeltaFp(탄창 바닥 잡기용)를 더하고, 손을 손바닥이 위로 오게 돌리고(RlRotA), 손가락을 편 모양으로 만든다.
 그래서 손목이 목표보다 (-4.5, +3.9, -5.3)cm 어긋나 검지 끝이 래치보다 앞쪽 8cm·아래 4cm 에 있었고(3인칭은 목표대로) 장전손잡이에 손이 닿지 않았다.
 수정: 곡선 HandleFp(0~1, 손잡이 구간에서 1)를 읽어 RlEnvFp.B(= RlFpW)를 RlFpW x (1 - HandleFp) 로 바꾼다 -> 손잡이 구간에서는 1인칭도 3인칭과 같은 손 위치/회전.
 추가 노드: RlHC(GetCurveValue HandleFp), RlHInv(1 - 값), RlFpW2(곱).  되돌리기: RlEnvFp.B 를 RlFpW.Result 로 다시 연결.   -> Data/lyra_fp_handle_fade.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_handle_fade.json'
U = '/Script/ControlRig.RigUnit_'
R = {}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('RlEnvFp', 'RlFpW'): assert need in N, 'missing ' + need
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    if 'RlFpW2' in N: R['note'] = 'exists'
    else:
        mk('GetCurveValue', 'RlHC', Curve='HandleFp')
        mk('MathFloatRemap', 'RlHInv', SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        mk('MathFloatMul', 'RlFpW2')
        link('RlHC.Value', 'RlHInv.Value'); link('RlFpW.Result', 'RlFpW2.A'); link('RlHInv.Result', 'RlFpW2.B')
        srcs = []
        for p in N['RlEnvFp'].get_pins():
            if str(p.get_name()) == 'B': srcs = [str(s.get_pin_path()) for s in p.get_linked_source_pins()]
        R['old_b_src'] = srcs
        for s in srcs:
            try: c.break_link(s, 'RlEnvFp.B')
            except Exception as e: L.append(['break', s, str(e)[:60]])
        link('RlFpW2.Result', 'RlEnvFp.B')
    R['links'] = L
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_HANDLE_FADE', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
