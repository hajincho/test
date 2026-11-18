"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 1인칭 재장전 - 손바닥으로 탄창 바닥을 받치고, 손가락은 편 채 살짝만 오므린다.
측정(Data/lyra_reload_mag_probe_fp.json): (a) 쥐는 동안 손바닥 법선이 총 기준 (0.75, -0.08, 0.66) = 위에서 49도 왼쪽으로 누워 있어 손 옆면이 탄창 바닥에 닿았다(손목 회전 +90도는 과했음).
    (b) 손가락은 재장전 애니메이션 값 그대로: 2번 관절 굽힘 검지 39 / 중지 39 / 약지 59 / 소지 104도 -> 소지가 꺾인 이상한 모양.
수정(1인칭 재장전 중에만: 가중치 RlEnvFp = 재장전 곡선 x (1 - TpW)):
 (1) 손목 회전 RlRotA.B = ROT_DEG(41.3도, 정확히 손바닥 법선이 위(+Z)를 향하는 값: 손바닥 법선 = cross(손가락 방향, 검지-소지) 로 계산).
 (2) 손가락 IK: 검지/중지/약지/소지 각각 TwoBoneIK(1번 관절 -> 2번 관절, 이펙터 3번 관절). 목표 = 1번 관절 + 손바닥 앞방향 u x L1 + (u를 손바닥 법선 쪽으로 BEND 도 굽힌 방향) x L2,
     3번 관절 방향은 2배 굽힘. 폴 벡터 = 손바닥 법선. u/법선은 총 회전(GRotR)으로 구하므로 손목 회전이 바뀌어도 따라간다. 엄지는 애니메이션 그대로.
 실행 순서: RLArmIK -> (손가락 IK 4개) -> 원래 다음 노드. 값은 Data/fp_reload_palm.json 으로 바꿀 수 있다.   -> Data/lyra_fp_reload_palm.json"""
import unreal, json, os, math, traceback
D_DIR = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
OUT = D_DIR + r'\lyra_fp_reload_palm.json'
P = {'rot_deg': 41.3, 'bend': {'Index': 16.0, 'Middle': 18.0, 'Ring': 20.0, 'Little': 24.0}, 'u': [0.0, 0.99682, 0.07972], 'n': [0.0, -0.07972, 0.99682]}   # u 와 n 은 서로 수직인 단위벡터(아니면 목표 거리가 팔 길이를 넘어 손가락이 쭉 펴진다)
if os.path.exists(D_DIR + r'\fp_reload_palm.json'): P.update(json.load(open(D_DIR + r'\fp_reload_palm.json')))
LEN = {'Index': (2.485, 1.986), 'Middle': (2.842, 2.376), 'Ring': (2.765, 2.157), 'Little': (2.21, 1.484)}   # 1번->2번, 2번->3번 관절 거리(cm)
R = {'params': P}
U = '/Script/ControlRig.RigUnit_'
def V(v): return '(X=%.5f,Y=%.5f,Z=%.5f)' % tuple(v)
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('RlRotA', 'RlEnvFp', 'GRotR', 'RLArmIK'): assert need in N, 'missing ' + need
    L = []
    def link(a, b):
        try: L.append(['+', a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append(['+', a, b, 'err ' + str(e)[:80]])
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    R['rot'] = bool(c.set_pin_default_value('RlRotA.B', '%.6f' % math.radians(P['rot_deg']), True, False))
    had = 'FgIndexIK' in N; R['had'] = had
    # 공통: 방향 벡터
    mk('MathQuaternionRotateVector', 'FgU', Vector=V(P['u'])); mk('MathQuaternionRotateVector', 'FgN', Vector=V(P['n']))
    if not had: link('GRotR.Result', 'FgU.Transform'); link('GRotR.Result', 'FgN.Transform')
    c.set_pin_default_value('FgU.Vector', V(P['u']), True, False); c.set_pin_default_value('FgN.Vector', V(P['n']), True, False)
    chain = []
    for f in ('Index', 'Middle', 'Ring', 'Little'):
        th = math.radians(P['bend'][f]); l1, l2 = LEN[f]
        j1, j2, j3 = ['(Type=Bone,Name="%sFinger%d_L")' % (f, k) for k in (1, 2, 3)]
        p = 'Fg' + f
        mk('GetTransform', p + 'J1', Item=j1, Space='GlobalSpace'); mk('GetTransform', p + 'J3', Item=j3, Space='GlobalSpace')
        mk('MathVectorScale', p + 'U1', Factor='%.5f' % l1); mk('MathVectorScale', p + 'U2', Factor='%.5f' % (l2 * math.cos(th))); mk('MathVectorScale', p + 'N2', Factor='%.5f' % (l2 * math.sin(th)))
        mk('MathVectorAdd', p + 'S1'); mk('MathVectorAdd', p + 'S2'); mk('MathVectorAdd', p + 'Tg')
        mk('MathVectorScale', p + 'D3u', Factor='%.5f' % math.cos(2 * th)); mk('MathVectorScale', p + 'D3n', Factor='%.5f' % math.sin(2 * th)); mk('MathVectorAdd', p + 'D3')
        mk('MathQuaternionRotateVector', p + 'Cur', Vector='(X=0.0,Y=-1.0,Z=0.0)'); mk('MathQuaternionFromTwoVectors', p + 'Qs'); mk('MathQuaternionMul', p + 'Qn')
        mk('TwoBoneIKSimplePerItem', p + 'IK', ItemA=j1, ItemB=j2, EffectorItem=j3, PrimaryAxis='(X=0.0,Y=-1.0,Z=0.0)', SecondaryAxis='(X=0.0,Y=0.0,Z=1.0)', SecondaryAxisWeight='0.0',
           PoleVectorKind='Direction', bPropagateToChildren='True', ItemALength='%.4f' % l1, ItemBLength='%.4f' % l2)
        if not had:
            link('FgU.Result', p + 'U1.Value'); link('FgU.Result', p + 'U2.Value'); link('FgN.Result', p + 'N2.Value')
            link(p + 'J1.Transform.Translation', p + 'S1.A'); link(p + 'U1.Result', p + 'S1.B')
            link(p + 'U2.Result', p + 'S2.A'); link(p + 'N2.Result', p + 'S2.B'); link(p + 'S1.Result', p + 'Tg.A'); link(p + 'S2.Result', p + 'Tg.B')
            link('FgU.Result', p + 'D3u.Value'); link('FgN.Result', p + 'D3n.Value'); link(p + 'D3u.Result', p + 'D3.A'); link(p + 'D3n.Result', p + 'D3.B')
            link(p + 'J3.Transform.Rotation', p + 'Cur.Transform'); link(p + 'Cur.Result', p + 'Qs.A'); link(p + 'D3.Result', p + 'Qs.B')
            link(p + 'Qs.Result', p + 'Qn.A'); link(p + 'J3.Transform.Rotation', p + 'Qn.B')
            link(p + 'Tg.Result', p + 'IK.Effector.Translation'); link(p + 'Qn.Result', p + 'IK.Effector.Rotation'); link('FgN.Result', p + 'IK.PoleVector'); link('RlEnvFp.Result', p + 'IK.Weight')
        else:
            c.set_pin_default_value(p + 'U2.Factor', '%.5f' % (l2 * math.cos(th)), True, False); c.set_pin_default_value(p + 'N2.Factor', '%.5f' % (l2 * math.sin(th)), True, False)
            c.set_pin_default_value(p + 'D3u.Factor', '%.5f' % math.cos(2 * th), True, False); c.set_pin_default_value(p + 'D3n.Factor', '%.5f' % math.sin(2 * th), True, False)
        chain.append(p + 'IK')
    if not had:
        N = nodes()
        def ep(node):
            for pn in N[node].get_pins():
                if str(pn.get_name()) == 'ExecutePin': return pn
        ik = ep('RLArmIK'); nxt = [str(t.get_pin_path()) for t in ik.get_linked_target_pins()]; R['next'] = nxt
        for t in nxt:
            try: L.append(['x', t, bool(c.break_link('RLArmIK.ExecutePin', t))])
            except Exception as e: L.append(['x', t, 'err ' + str(e)[:60]])
        prev = 'RLArmIK.ExecutePin'
        for nd in chain: link(prev, nd + '.ExecutePin'); prev = nd + '.ExecutePin'
        for t in nxt: link(prev, t)
    R['links'] = L
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_RELOAD_PALM', R.get('saved'), R.get('error', '')[-200:])
