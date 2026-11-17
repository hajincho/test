"""Lyra 에디터(`py <파일> keep [도]`, PIE 중지 상태): CR_FurinaSecondary 의 3인칭 소총에 'cant'(수직축 yaw 회전)를 더한다.
앞으로 옮기는 방식은 팔이 닿는 거리에서 막혀(명령 +4/+10cm 이 모두 +1.6cm 에서 멈춤, lyra_stock_probe) 개머리판을 몸 밖으로 못 뺀다.
그래서 소총을 쥔 손(원점) 기준으로 총구를 몸 안쪽(왼쪽)으로 돌려 개머리판이 몸 바깥(오른쪽)으로 나가게 한다.
각도 = TpW(3인칭 가중, 정조준 때 0) x 기본 -도(기본 10도). 새 노드: TpCantAng, TpCantQ, GRotC. GRot 의 결과를 쓰던 곳은 GRotC 로 연결을 옮긴다. 이미 있으면 각도만 바꾼다.
 -> Data/lyra_tp_cant.json"""
import unreal, json, sys, math, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_tp_cant.json'
R = {}
DEG = float(sys.argv[-1]) if sys.argv[-1].replace('.', '', 1).replace('-', '', 1).isdigit() else 10.0
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    nodes = {str(n.get_node_path()): n for n in g.get_nodes()}
    R['has'] = 'GRotC' in nodes
    if 'GRotC' not in nodes:
        grot = nodes['GRot']; res = [p for p in grot.get_pins() if str(p.get_name()) == 'Result'][0]
        targets = [str(t.get_pin_path()) for t in res.get_linked_target_pins()] if hasattr(res, 'get_linked_target_pins') else [str(t.get_pin_path()) for t in res.get_linked_pins()]  # 나중에 옮길 연결
        R['targets'] = targets
        c.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_MathFloatMul', 'Execute', unreal.Vector2D(0, 0), 'TpCantAng')
        c.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(0, 0), 'TpCantQ')
        c.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_MathQuaternionMul', 'Execute', unreal.Vector2D(0, 0), 'GRotC')
        R['links'] = [bool(c.add_link('TpW.Result', 'TpCantAng.A')), bool(c.add_link('TpCantAng.Result', 'TpCantQ.Angle')), bool(c.add_link('TpCantQ.Result', 'GRotC.A')), bool(c.add_link('GRot.Result', 'GRotC.B'))]
        for t in targets:
            if t.startswith('GRotC'): continue
            R.setdefault('moved', []).append([t, bool(c.break_link('GRot.Result', t)), bool(c.add_link('GRotC.Result', t))])
        c.set_pin_default_value('TpCantQ.Axis', '(X=0.0,Y=0.0,Z=1.0)', True, False)
    R['rad'] = math.radians(-DEG)
    R['set'] = bool(c.set_pin_default_value('TpCantAng.B', '%.6f' % math.radians(-DEG), True, False))
    cr.recompile_vm(); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(cr, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_TP_CANT', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
