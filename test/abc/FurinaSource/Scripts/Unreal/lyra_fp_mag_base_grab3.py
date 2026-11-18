"""Lyra 에디터(`py <파일>`, PIE 중지 상태): lyra_fp_mag_base_grab2.py 후속 - 순서 바꾸기.
측정(2차): 끼우기는 아래에서 곧게 올라가게 됐지만, 뽑기 첫 순간 탄창 윗부분이 삽입구 안에 있는 동안 옆으로 1.5cm 흘렀다(벽 침범 31샘플).
 원인: 높이 제한(급격히 내림)을 적용한 '뒤에' 부드럽게(AccumulateVectorLerp) 걸러서, 아래+옆 이동이 대각선으로 섞였다.
수정: 원래 목표 -> (붙는 순간 고정 RgFrz) -> (부드럽게 RgSm) -> (높이 제한 Rc*, 마지막에 그대로 적용) -> 1인칭 가중 RgOut.
 높이 제한 R0 를 0.4cm 로 줄여(탄창-삽입구 여유 0.43cm) 축에서 0.4cm 벗어나기 전에 탄창이 삽입구를 빠져나오게 한다.
-> Data/lyra_fp_mag_base_grab3.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_mag_base_grab3.json'
R0 = 0.4
R = {'R0': R0}
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller()
    L = []
    def brk(a, b):
        try: L.append(['x', a, b, bool(c.break_link(a, b))])
        except Exception as e: L.append(['x', a, b, 'err ' + str(e)[:60]])
    def link(a, b):
        try: L.append(['+', a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append(['+', a, b, 'err ' + str(e)[:60]])
    # 고정은 원래 목표에 먼저
    brk('RcOut.Result', 'RgFrz.A'); link('LHandOff3.Result', 'RgFrz.A')
    # 높이 제한 입력을 부드럽게 거른 값으로
    for dst in ('RcD.A', 'RcOut.A'): brk('LHandOff3.Result', dst); link('RgSm.Result', dst)
    for sub, dst in (('Z', 'RcZ.A'), ('X', 'RcP.X'), ('Y', 'RcP.Y')): brk('LHandOff3.Result.' + sub, dst); link('RgSm.Result.' + sub, dst)
    # 최종: 1인칭이면 제한된 값
    brk('RgSm.Result', 'RgOut.B'); link('RcOut.Result', 'RgOut.B')
    R['links'] = L
    R['r0'] = bool(c.set_pin_default_value('RcZlim.SourceMaximum', '%.4f' % R0, True, False))
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_MAG_BASE3', R.get('saved'), R.get('error', '')[-200:])
