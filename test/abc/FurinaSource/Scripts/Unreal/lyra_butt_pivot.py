"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 3인칭에서 조준 피치(고개 들기/내리기)에 따라 총이 '눈'을 축으로 돌아 개머리판이 어깨에서 떨어지던 것을, 개머리판을 축으로 돌도록 보정.
측정(Data/lyra_fire_pose_clav_up.json, 위로 35도): 개머리판 끝이 어깨 앞 5cm -> 16cm 로 밀려나고 왼손이 총의 잡는 자리에서 10cm 뒤에 멈췄다(팔 39.16cm 다 펴짐).
CR: GPos = EyePos + AimQ*GOffB. 개머리판 위치 = GPos + AimQ*b (b = 총 기준점에서 본 개머리판, 총을 손에 대해 +7.3 옮긴 것 반영: (0, -39.37+7.3, 4.53)).
 피치가 없을 때의 개머리판 위치를 유지하려면 GPos 에 (I - AimQ)*(GOffB + b) 를 더하면 된다 -> PbOff/PbRot/PbD/PbW/GPos2 노드, 가중치 TpW(3인칭만. 1인칭·정조준 조준선은 그대로).
GPos.Result 를 쓰던 곳은 모두 GPos2 로 바꾼다. 되돌리기: `py <파일> revert` (가중치 0). -> Data/lyra_butt_pivot.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_butt_pivot.json'
BUTT = (0.0, -39.37 + 7.3, 4.53)
REVERT = 'revert' in sys.argv
R = {'BUTT': BUTT, 'revert': REVERT}
U = '/Script/ControlRig.RigUnit_'
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('GPos', 'GOffB', 'AimQ', 'TpW'): assert need in N, 'missing ' + need
    had = 'GPos2' in N; R['had'] = had
    def mk(typ, nm, x, y):
        if nm not in nodes(): c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(x, y), nm)
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    if not had:
        # GPos.Result 를 쓰는 곳 목록(나중에 GPos2 로 옮김)
        out = [p for p in N['GPos'].get_pins() if str(p.get_name()) == 'Result'][0]
        targets = [str(t.get_pin_path()) for t in out.get_linked_target_pins()]; R['gpos_targets'] = targets
        mk('MathVectorAdd', 'PbOff', 0, 0); mk('MathQuaternionRotateVector', 'PbRot', 0, 100); mk('MathVectorSub', 'PbD', 0, 200)
        mk('MathFloatMul', 'PbWf', 0, 300); mk('MathVectorScale', 'PbW', 0, 400); mk('MathVectorAdd', 'GPos2', 0, 500)
        link('GOffB.Result', 'PbOff.A')
        link('AimQ.Result', 'PbRot.Transform'); link('PbOff.Result', 'PbRot.Vector')
        link('PbOff.Result', 'PbD.A'); link('PbRot.Result', 'PbD.B')
        link('TpW.Result', 'PbWf.A'); link('PbD.Result', 'PbW.Value'); link('PbWf.Result', 'PbW.Factor')
        link('GPos.Result', 'GPos2.A'); link('PbW.Result', 'GPos2.B')
        for t in targets:
            try: c.break_link('GPos.Result', t)
            except Exception as e: L.append(['break', t, str(e)[:60]])
            link('GPos2.Result', t)
    R['links'] = L
    S = [c.set_pin_default_value('PbOff.B', '(X=%.4f,Y=%.4f,Z=%.4f)' % BUTT, True, False), c.set_pin_default_value('PbWf.B', '0.0' if REVERT else '1.0', True, False)]
    R['set'] = [bool(x) for x in S]
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_BUTT_PIVOT', R.get('saved'), R.get('error', '')[-200:])
