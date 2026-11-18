"""Lyra 에디터(`py <파일>`, PIE 중지 상태): lyra_fp_mag_base_grab.py 후속(1인칭 재장전 탄창 바닥 잡기).
측정(Data/lyra_reload_mag_probe_fp.json, 1차): 바닥 잡는 위치·손바닥 방향은 맞았지만, MagState 가 0->1 로 오르는 사이(탄창이 실제로 손에 붙기 전)에 손이 이미 8cm 내려가서
 탄창이 손바닥보다 4cm 더 위에 붙었다(손-탄창 간격 6.6 -> 10.8cm). 그래서 '곧게 빼기' 높이 제한을 지켜도 탄창 윗부분이 삽입구 안에 남은 채 옆으로 움직였다.
수정:
 (1) 붙는 순간 고정: MagState 가 0.02~0.98 사이(쥐는 중/놓는 중)에는 왼손 목표를 잡는 자리 P_G 에 고정(RgW = 창 x 1인칭) -> 탄창이 설계한 간격으로 붙고, 놓을 때도 장착 자리에서 놓는다.
 (2) 매끄럽게: 위 고정과 높이 제한이 켜지고 꺼질 때 손이 튀지 않도록 1인칭 왼손 목표 오프셋을 AccumulateVectorLerp(Blend=BLEND)로 거른다.
 (3) 높이 여유 CLEAR 9.5cm(탄창 윗부분이 삽입구 아래 -4.5cm 이하로 빠질 때까지 옆으로 못 감).
노드: RgWa/RgWb/RgWin/RgW/RgFrz/RgSm/RgOut. -> Data/lyra_fp_mag_base_grab2.json"""
import unreal, json, os, traceback
D_DIR = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
OUT = D_DIR + r'\lyra_fp_mag_base_grab2.json'
BLEND = 18.0; CLEAR = 9.5
R = {'BLEND': BLEND, 'CLEAR': CLEAR}
U = '/Script/ControlRig.RigUnit_'
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('RcOut', 'RcPg', 'RcMagC', 'RlFpW', 'RLHOff', 'LHandOff3', 'RcZlim'): assert need in N, 'missing ' + need
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    if 'RgOut' not in N:
        mk('MathFloatRemap', 'RgWa', SourceMinimum='0.0', SourceMaximum='0.02', TargetMinimum='0', TargetMaximum='1', bClamp='True')
        mk('MathFloatRemap', 'RgWb', SourceMinimum='0.98', SourceMaximum='1.0', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        mk('MathFloatMul', 'RgWin'); mk('MathFloatMul', 'RgW'); mk('MathVectorLerp', 'RgFrz')
        mk('AccumulateVectorLerp', 'RgSm', bIntegrateDeltaTime='True'); mk('MathVectorLerp', 'RgOut')
        link('RcMagC.Value', 'RgWa.Value'); link('RcMagC.Value', 'RgWb.Value'); link('RgWa.Result', 'RgWin.A'); link('RgWb.Result', 'RgWin.B')
        link('RgWin.Result', 'RgW.A'); link('RlFpW.Result', 'RgW.B')
        link('RcOut.Result', 'RgFrz.A'); link('RcPg.Result', 'RgFrz.B'); link('RgW.Result', 'RgFrz.T')
        link('RgFrz.Result', 'RgSm.TargetValue')
        link('LHandOff3.Result', 'RgOut.A'); link('RgSm.Result', 'RgOut.B'); link('RlFpW.Result', 'RgOut.T')
        try: c.break_link('RcOut.Result', 'RLHOff.Vector')
        except Exception as e: L.append(['break', str(e)[:60]])
        link('RgOut.Result', 'RLHOff.Vector')
    R['links'] = L
    pgz = float(str([p for p in nodes()['RcZlim'].get_pins() if str(p.get_name()) == 'TargetMinimum'][0].get_default_value()))
    S = [c.set_pin_default_value('RgSm.Blend', '%.3f' % BLEND, True, False), c.set_pin_default_value('RcZlim.TargetMaximum', '%.4f' % (pgz - CLEAR), True, False)]
    R['pgz'] = pgz; R['set'] = [bool(x) for x in S]
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_MAG_BASE2', R.get('saved'), R.get('error', '')[-200:])
