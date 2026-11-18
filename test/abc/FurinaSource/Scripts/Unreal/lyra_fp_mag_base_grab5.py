"""Lyra 에디터(`py <파일>`, PIE 중지 상태): lyra_fp_mag_base_grab4.py 후속 - 고정/제한 가중치에 '느린 꺼짐' 추가.
측정(4차): (a) 쥐는 고정이 MagState 0.98 에서 바로 풀려, 탄창이 실제로 붙는 몇 프레임 사이 손이 4.7cm 내려가 탄창이 손바닥 위 11cm 에 붙었다.
          (b) 끼울 때 MagState 가 0.97 아래로 내려가는 순간 높이 제한이 꺼져 탄창이 옆으로 1.3cm 벗어난 채 7cm 위로 튀었다.
수정: 두 가중치 모두 '바로 켜지고 천천히 꺼지게'(max(값, AccumulateFloatLerp(값, Blend=DECAY))).
 RgWin -> RgWinS/RgWinM -> RgW.A,  RcStep -> RcStepS/RcHold3 -> RcW.A (RcHold2 감소 감지 경로는 쓰지 않음).
-> Data/lyra_fp_mag_base_grab5.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_mag_base_grab5.json'
DECAY = 6.0
R = {'DECAY': DECAY}
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
    def brk(a, b):
        try: L.append(['x', a, b, bool(c.break_link(a, b))])
        except Exception as e: L.append(['x', a, b, 'err ' + str(e)[:60]])
    if 'RcHold3' not in nodes():
        mk('AccumulateFloatLerp', 'RgWinS', bIntegrateDeltaTime='True'); mk('MathFloatMax', 'RgWinM')
        link('RgWin.Result', 'RgWinS.TargetValue'); link('RgWin.Result', 'RgWinM.A'); link('RgWinS.Result', 'RgWinM.B')
        brk('RgWin.Result', 'RgW.A'); link('RgWinM.Result', 'RgW.A')
        mk('AccumulateFloatLerp', 'RcStepS', bIntegrateDeltaTime='True'); mk('MathFloatMax', 'RcHold3')
        link('RcStep.Result', 'RcStepS.TargetValue'); link('RcStep.Result', 'RcHold3.A'); link('RcStepS.Result', 'RcHold3.B')
        brk('RcHold2.Result', 'RcW.A'); link('RcHold3.Result', 'RcW.A')
    R['links'] = L
    R['set'] = [bool(c.set_pin_default_value('RgWinS.Blend', '%.3f' % DECAY, True, False)), bool(c.set_pin_default_value('RcStepS.Blend', '%.3f' % DECAY, True, False))]
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_MAG_BASE5', R.get('saved'), R.get('error', '')[-200:])
