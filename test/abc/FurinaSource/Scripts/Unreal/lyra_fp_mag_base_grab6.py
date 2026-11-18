"""Lyra 에디터(`py <파일>`, PIE 중지 상태): lyra_fp_mag_base_grab5.py 후속 - 쥐는 순간 손이 3.6cm 툭 떨어지는 것 제거.
측정(5차): MagState 0.97 -> 1.0 한 프레임에 손바닥이 -8.8 -> -12.5 로 떨어지고 그 순간 탄창이 붙어(간격 11cm) 탄창이 위로 튀었다.
 원인: 높이 제한이 켜질 때 쓰는 '옆으로 벗어난 거리 r' 을 부드럽게 거른 손(RgSm)에서 쟀는데, 쥐는 동안 고정 목표(P_G)로 아직 다 오지 못해 r 이 0.3~0.5cm(R0 근처) -> 즉시 아래로 눌림.
수정: r = lerp(고정 목표 기준 r(RgFrz, 쥘 때 0), 거른 손 기준 r(RgSm), RcStepS). 쥐는 순간(RcStepS 0)엔 0 이라 안 눌리고, 들고 있는 동안/끼울 때(RcStepS 1)는 거른 손 기준.
 + 거르기 속도 RgSm.Blend 18 -> 30 (고정 목표로 더 빨리 도착). -> Data/lyra_fp_mag_base_grab6.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_mag_base_grab6.json'
BLEND = 30.0
R = {'BLEND': BLEND}
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
    if 'RcRmix' not in nodes():
        mk('MathVectorSub', 'RcDf'); mk('MathVectorMul', 'RcDfxy', B='(X=1.0,Y=1.0,Z=0.0)'); mk('MathVectorLength', 'RcRf'); mk('MathFloatLerp', 'RcRmix')
        link('RgFrz.Result', 'RcDf.A'); link('RcPg.Result', 'RcDf.B'); link('RcDf.Result', 'RcDfxy.A'); link('RcDfxy.Result', 'RcRf.Value')
        link('RcRf.Result', 'RcRmix.A'); link('RcR.Result', 'RcRmix.B'); link('RcStepS.Result', 'RcRmix.T')
        brk('RcR.Result', 'RcZlim.Value'); link('RcRmix.Result', 'RcZlim.Value')
    R['links'] = L
    R['blend'] = bool(c.set_pin_default_value('RgSm.Blend', '%.3f' % BLEND, True, False))
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_MAG_BASE6', R.get('saved'), R.get('error', '')[-200:])
