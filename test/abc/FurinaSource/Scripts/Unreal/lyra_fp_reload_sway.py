"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 1인칭 전용 두 가지.
(A) 1인칭 재장전 손-탄창 맞추기. 측정(Data/lyra_reload_mag_probe_fp.json, 총 기준 X왼쪽/Y앞/Z위): 탄창을 쥐는 순간(MagState 0.5) 손바닥 중심(손목과 중지 1마디 중간)이
    (9.5, 0.4, -6.5), 탄창 중심이 (-0.1, -1.9, -2.2) -> 손바닥이 탄창 왼쪽 9.5cm 허공. 탄창은 쥐는 순간의 위치 그대로 손에 붙으므로(KeepWorld) 이후 내내 떨어져 보였다.
    3인칭 보정(RlDelta, x TpW)과 같은 방식으로 1인칭 보정 RlDeltaFp = FP_D x RlEnv x (1 - TpW) 를 왼손 목표에 더한다(RLV3 = RLV2 + RlDeltaFp -> LHandOff3.B).
    FP_D = 손바닥이 탄창 왼쪽 면(중심 +3.5cm), 탄창 높이 -5cm 에 오도록 (-6.0, -2.3, +1.5).
(B) 1인칭에서 팔(팔꿈치)에만 은은한 흔들림: 양팔 IK 의 폴 벡터(팔꿈치 방향)에 느린 사인파(주기 약 4.8초/7초)를 더한다. 손 위치(IK 목표)는 그대로라 손은 총에 붙어 있고 팔꿈치만 1~2cm 움직인다.
    가중치 = 1 - ViewTP 커브(1인칭에서만). 크기는 SWAY(폴 방향 길이 약 1.8 대비).
여러 번 실행해도 노드는 한 번만 만들고 값만 갱신. -> Data/lyra_fp_reload_sway.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_reload_sway.json'
FP_D = (-6.0, -2.3, 1.5)
SWAY = 0.15
R = {'FP_D': FP_D, 'SWAY': SWAY}
U = '/Script/ControlRig.RigUnit_'
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('RLV2', 'RlEnv', 'TpW', 'LHandOff3', 'RRArmIK', 'RLArmIK'): assert need in N, 'missing ' + need
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    def src_of(pin_path):
        node, pin = pin_path.split('.', 1)
        for p in N[node].get_pins():
            if str(p.get_name()) == pin.split('.')[0]: return [str(s.get_pin_path()) for s in p.get_linked_source_pins()], str(p.get_default_value())
        return [], None
    # ---------- (A) 재장전
    if 'RLV3' not in N:
        mk('MathFloatRemap', 'RlFpW', SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        mk('MathFloatMul', 'RlEnvFp'); mk('MathVectorScale', 'RlDeltaFp'); mk('MathVectorAdd', 'RLV3')
        link('TpW.Result', 'RlFpW.Value'); link('RlEnv.Result', 'RlEnvFp.A'); link('RlFpW.Result', 'RlEnvFp.B')
        link('RlEnvFp.Result', 'RlDeltaFp.Factor'); link('RLV2.Result', 'RLV3.A'); link('RlDeltaFp.Result', 'RLV3.B')
        srcs, _ = src_of('LHandOff3.B'); R['lho3_b_src'] = srcs
        for s in srcs:
            try: c.break_link(s, 'LHandOff3.B')
            except Exception as e: L.append(['break', s, str(e)[:60]])
        link('RLV3.Result', 'LHandOff3.B')
    R['setA'] = bool(c.set_pin_default_value('RlDeltaFp.Value', '(X=%.4f,Y=%.4f,Z=%.4f)' % FP_D, True, False))
    # ---------- (B) 팔꿈치 흔들림
    N = nodes()
    if 'SwT' not in N:
        mk('GetCurveValue', 'SwViewTP', Curve='ViewTP')
        mk('MathFloatRemap', 'SwFpW', SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        mk('AccumulateFloatAdd', 'SwT', Increment='1.0', bIntegrateDeltaTime='True')
        mk('MathFloatMul', 'SwP1', B='1.3'); mk('MathFloatMul', 'SwP2', B='0.9'); mk('MathFloatAdd', 'SwP2o', B='1.7')
        mk('MathFloatSin', 'SwS1'); mk('MathFloatSin', 'SwS2')
        mk('MathFloatMul', 'SwAmp'); mk('MathFloatMul', 'SwA1'); mk('MathFloatMul', 'SwA2')
        link('SwViewTP.Value', 'SwFpW.Value'); link('SwFpW.Result', 'SwAmp.A')
        link('SwT.Result', 'SwP1.A'); link('SwT.Result', 'SwP2.A'); link('SwP2.Result', 'SwP2o.A')
        link('SwP1.Result', 'SwS1.Value'); link('SwP2o.Result', 'SwS2.Value')
        link('SwS1.Result', 'SwA1.A'); link('SwAmp.Result', 'SwA1.B'); link('SwS2.Result', 'SwA2.A'); link('SwAmp.Result', 'SwA2.B')
        for side, ik, a, b in (('R', 'RRArmIK', 'SwA1', 'SwA2'), ('L', 'RLArmIK', 'SwA2', 'SwA1')):
            mk('MathVectorMake', 'SwV' + side); link(a + '.Result', 'SwV%s.X' % side); link(b + '.Result', 'SwV%s.Z' % side)
            srcs, dflt = src_of(ik + '.PoleVector'); R['pole_' + side] = [srcs, dflt]
            mk('MathVectorAdd', 'SwPole' + side)
            if srcs:
                for s in srcs:
                    c.break_link(s, ik + '.PoleVector'); link(s, 'SwPole%s.A' % side)
            else: c.set_pin_default_value('SwPole%s.A' % side, dflt, True, False)
            link('SwV%s.Result' % side, 'SwPole%s.B' % side); link('SwPole%s.Result' % side, ik + '.PoleVector')
    R['setB'] = bool(c.set_pin_default_value('SwAmp.B', '%.4f' % SWAY, True, False))
    R['links'] = L
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_RELOAD_SWAY', R.get('saved'), R.get('error', '')[-200:])
