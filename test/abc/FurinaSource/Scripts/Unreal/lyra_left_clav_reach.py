"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 왼팔이 총에 안 닿을 때 왼쪽 어깨 관절을 '평행이동'(팔이 늘어나 보임)하던 것을 '쇄골 회전'(왼쪽 어깨를 기울여 앞으로 빼기)으로 바꾼다.
기존: LShOver(목표까지 거리 - 37cm) 만큼 Left-arm 을 목표 쪽으로 SetTranslation(propagate) -> 쇄골이 늘어나 왼팔이 길어 보였다(사용자 캡처: 위를 볼 때 특히).
새로: 같은 목표점(LShNew = Left-arm + 초과분 x GAIN)을 향하도록 Left-shoulder(쇄골) 뼈를 그 뿌리 기준으로 회전(FromTwoVectors) -> 쇄골 길이는 그대로, 어깨만 앞/위로 기울어진다.
 매 프레임 목표(조준 피치·자세에 따라 움직이는 왼손 목표)로 계산하므로 고개를 들고 내릴 때 실시간으로 반영된다. 회전각은 MAX_DEG 로 제한.
LShSet(평행이동)은 Weight 0 으로 끄고 노드는 남긴다(되돌리려면 `py <파일> revert`: LShSet.Weight 1, ClSet.Weight 0).
-> Data/lyra_left_clav_reach.json"""
import unreal, json, sys, math, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_left_clav_reach.json'
GAIN = 2.6        # 회전은 목표 방향 성분만 얻으므로 초과분보다 조금 더 크게 겨냥
MAX_DEG = 45.0
REVERT = 'revert' in sys.argv
R = {'GAIN': GAIN, 'MAX_DEG': MAX_DEG, 'revert': REVERT}
U = '/Script/ControlRig.RigUnit_'
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('LShSet', 'LShXf', 'LShMove', 'RLArmIK'): assert need in N, 'missing ' + need
    had = 'ClSet' in N; R['had'] = had
    def mk(typ, nm, x, y):
        if nm not in nodes(): c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(x, y), nm)
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    if not had:
        mk('GetTransform', 'ClXf', 0, 0); mk('MathVectorScale', 'ClMv', 0, 100); mk('MathVectorAdd', 'ClGoal', 0, 200)
        mk('MathVectorSub', 'ClV1', 0, 300); mk('MathVectorSub', 'ClV2', 0, 400); mk('MathQuaternionFromTwoVectors', 'ClQ0', 0, 500)
        mk('MathQuaternionToAxisAndAngle', 'ClAA', 0, 600); mk('MathFloatClamp', 'ClAng', 0, 700); mk('MathQuaternionFromAxisAndAngle', 'ClQ', 0, 800)
        mk('MathQuaternionMul', 'ClRot', 0, 900); mk('SetRotation', 'ClSet', 0, 1000)
        c.set_pin_default_value('ClXf.Item', '(Type=Bone,Name="Left-shoulder")', True, False); c.set_pin_default_value('ClXf.Space', 'GlobalSpace', True, False)
        c.set_pin_default_value('ClSet.Item', '(Type=Bone,Name="Left-shoulder")', True, False); c.set_pin_default_value('ClSet.Space', 'GlobalSpace', True, False)
        c.set_pin_default_value('ClSet.bPropagateToChildren', 'True', True, False)
        link('LShMove.Result', 'ClMv.Value')
        link('LShXf.Transform.Translation', 'ClGoal.A'); link('ClMv.Result', 'ClGoal.B')
        link('LShXf.Transform.Translation', 'ClV1.A'); link('ClXf.Transform.Translation', 'ClV1.B')
        link('ClGoal.Result', 'ClV2.A'); link('ClXf.Transform.Translation', 'ClV2.B')
        link('ClV1.Result', 'ClQ0.A'); link('ClV2.Result', 'ClQ0.B')
        link('ClQ0.Result', 'ClAA.Value'); link('ClAA.Angle', 'ClAng.Value'); link('ClAA.Axis', 'ClQ.Axis'); link('ClAng.Result', 'ClQ.Angle')
        link('ClQ.Result', 'ClRot.A'); link('ClXf.Transform.Rotation', 'ClRot.B'); link('ClRot.Result', 'ClSet.Value')
        # 실행 흐름: LShSet -> ClSet -> RLArmIK
        N = nodes()
        def ep(node):
            for p in N[node].get_pins():
                if 'Execute' in str(p.get_name()): return p
        ik = ep('RLArmIK'); cs = ep('ClSet')
        srcs = [str(s.get_pin_path()) for s in ik.get_linked_source_pins()]; R['ik_exec_from'] = srcs
        for s in srcs: L.append(['exec', bool(c.break_link(s, str(ik.get_pin_path()))), bool(c.add_link(s, str(cs.get_pin_path())))])
        L.append(['exec_tail', bool(c.add_link(str(cs.get_pin_path()), str(ik.get_pin_path())))])
    R['links'] = L
    S = [c.set_pin_default_value('ClMv.Factor', '%.4f' % GAIN, True, False),
         c.set_pin_default_value('ClAng.Minimum', '0.0', True, False), c.set_pin_default_value('ClAng.Maximum', '%.6f' % math.radians(MAX_DEG), True, False),
         c.set_pin_default_value('LShSet.Weight', '1.0' if REVERT else '0.0', True, False), c.set_pin_default_value('ClSet.Weight', '0.0' if REVERT else '1.0', True, False)]
    R['set'] = [bool(x) for x in S]
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_LEFT_CLAV', R.get('saved'), R.get('error', '')[-200:])
