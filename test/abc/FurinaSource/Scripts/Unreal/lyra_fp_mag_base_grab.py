"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 1인칭 재장전 - 탄창 '바닥'을 손바닥을 위로 해서 잡고, 삽입구를 뚫지 않게 탄창 축(아래)으로 곧게 뽑고/끼우게 한다.
측정(Data/lyra_reload_mag_probe_fp.json): 뽑을 때 탄창이 아래로 내려가면서 동시에 왼쪽(+X)으로 4~6cm 움직여, 탄창 윗부분이 삽입구 안에 있는 동안 옆벽을 뚫고 지나갔다(끼울 때도 옆에서 들어옴).
수정(가중치는 모두 1인칭에서만):
 (1) 손 방향: 재장전 중(RlEnvFp) 왼손 회전에 총 기준 Y(앞)축 ROT_DEG 회전을 더해 손바닥을 위로(RlRotQ -> RLHRot.B).
 (2) 잡는 위치: lyra_fp_reload_sway.py 의 RlDeltaFp 값을 FP_D 로 바꿔 손바닥 중심이 탄창 바닥 바로 아래(탄창 중심 X/Y, 바닥 -1.5cm)에 오게.
 (3) 곧게 뽑기: 왼손 목표 P(총 기준점 좌표)를 탄창을 든 동안(MagState) 제한: 잡은 자리 P_G 에서 옆으로 r 만큼 벗어나면 높이를 P_G.z - CLEAR x clamp(r/R0) 이하로 내린다.
     -> 옆으로 움직이기 전에 먼저 탄창 길이만큼 아래로 빠지고, 끼울 때는 아래에서 축을 맞춘 뒤 곧게 올라간다(연속, 순간이동 없음).
 노드: RlRotA/RlRotQ0/RlRotQ, RcPg/RcD/RcDxy/RcR/RcZlim/RcZ/RcP/RcMagC/RcHold/RcW/RcOut. 값은 아래 상수 또는 Data/fp_mag_grab.json 으로 갱신.
-> Data/lyra_fp_mag_base_grab.json"""
import unreal, json, os, math, traceback
D_DIR = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
OUT = D_DIR + r'\lyra_fp_mag_base_grab.json'
P = {'rot_deg': 90.0, 'fp_d': [-9.55, -2.3, -2.95], 'p_g': [0.42, 1.9, -9.33], 'clear': 8.5, 'r0': 0.8}
if os.path.exists(D_DIR + r'\fp_mag_grab.json'): P.update(json.load(open(D_DIR + r'\fp_mag_grab.json')))
R = {'params': P}
U = '/Script/ControlRig.RigUnit_'
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('RlEnvFp', 'RlFpW', 'RlDeltaFp', 'LHandOff3', 'RLHOff', 'RLHRot'): assert need in N, 'missing ' + need
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    def pin(path):
        node, rest = path.split('.', 1)
        for p in N[node].get_pins():
            if str(p.get_name()) == rest: return p
    if 'RcOut' not in N:
        # (1) 손 회전
        qb = str(pin('RLHRot.B').get_default_value()); R['q_l'] = qb
        mk('MathFloatMul', 'RlRotA'); mk('MathQuaternionFromAxisAndAngle', 'RlRotQ0', Axis='(X=0.0,Y=1.0,Z=0.0)'); mk('MathQuaternionMul', 'RlRotQ')
        link('RlEnvFp.Result', 'RlRotA.A'); link('RlRotA.Result', 'RlRotQ0.Angle'); link('RlRotQ0.Result', 'RlRotQ.A')
        c.set_pin_default_value('RlRotQ.B', qb, True, False); link('RlRotQ.Result', 'RLHRot.B')
        # (3) 곧게 뽑기 제한
        mk('MathVectorAdd', 'RcPg', B='(X=0.0,Y=0.0,Z=0.0)'); mk('MathVectorSub', 'RcD'); mk('MathVectorMul', 'RcDxy', B='(X=1.0,Y=1.0,Z=0.0)')
        mk('MathVectorLength', 'RcR'); mk('MathFloatRemap', 'RcZlim', SourceMinimum='0', bClamp='True'); mk('MathFloatMin', 'RcZ'); mk('MathVectorMake', 'RcP')
        mk('GetCurveValue', 'RcMagC', Curve='MagState'); mk('MathFloatClamp', 'RcHold', Minimum='0', Maximum='1'); mk('MathFloatMul', 'RcW'); mk('MathVectorLerp', 'RcOut')
        link('LHandOff3.Result', 'RcD.A'); link('RcPg.Result', 'RcD.B'); link('RcD.Result', 'RcDxy.A'); link('RcDxy.Result', 'RcR.Value')
        link('RcR.Result', 'RcZlim.Value'); link('LHandOff3.Result.Z', 'RcZ.A'); link('RcZlim.Result', 'RcZ.B')
        link('LHandOff3.Result.X', 'RcP.X'); link('LHandOff3.Result.Y', 'RcP.Y'); link('RcZ.Result', 'RcP.Z')
        link('RcMagC.Value', 'RcHold.Value'); link('RcHold.Result', 'RcW.A'); link('RlFpW.Result', 'RcW.B')
        link('LHandOff3.Result', 'RcOut.A'); link('RcP.Result', 'RcOut.B'); link('RcW.Result', 'RcOut.T')
        srcs = [str(s.get_pin_path()) for s in pin('RLHOff.Vector').get_linked_source_pins()]; R['rlhoff_src'] = srcs
        for s in srcs:
            try: c.break_link(s, 'RLHOff.Vector')
            except Exception as e: L.append(['break', s, str(e)[:60]])
        link('RcOut.Result', 'RLHOff.Vector')
    R['links'] = L
    pg = P['p_g']
    S = [c.set_pin_default_value('RlRotA.B', '%.6f' % math.radians(P['rot_deg']), True, False),
         c.set_pin_default_value('RlDeltaFp.Value', '(X=%.4f,Y=%.4f,Z=%.4f)' % tuple(P['fp_d']), True, False),
         c.set_pin_default_value('RcPg.A', '(X=%.4f,Y=%.4f,Z=%.4f)' % tuple(pg), True, False),
         c.set_pin_default_value('RcZlim.SourceMaximum', '%.4f' % P['r0'], True, False),
         c.set_pin_default_value('RcZlim.TargetMinimum', '%.4f' % pg[2], True, False),
         c.set_pin_default_value('RcZlim.TargetMaximum', '%.4f' % (pg[2] - P['clear']), True, False)]
    R['set'] = [bool(x) for x in S]
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_MAG_BASE', R.get('saved'), R.get('error', '')[-200:])
