"""Lyra 에디터(`py <파일> keep [dx dy dz]`, PIE 중지 상태): 3인칭 재장전 중 왼손 손바닥이 탄창을 감싸게 왼손 목표를 옮긴다.
측정(lyra_reload_mag_probe.py, 손목+중지 1마디 중간 = 손바닥 중심): 잡는 순간 손바닥 중심이 탄창 중심에서 총 기준 (좌 +8.4, 앞 -2.0, 위 +2.6)cm 떨어져 있었다(탄창 옆 허공).
왼손 목표(LHandOff3 = LHandOff2 + RLV)에 TP 전용 보정 벡터(기본 (-4.8, -2.0, +2.1))를 더한다. 가중치 = clamp(ReloadLX/6, 0, 1) x TpW:
 ReloadLX 곡선은 손이 탄창으로 가며 0 -> 약 6 이 되고 탄창을 쥔 동안(뽑기/허리춤/끼우기) 6 이상, 핸드가드로 돌아가면 0 이 되므로 접근/복귀는 부드럽게, 쥐는 동안은 일정하게 적용된다.
쥐는 동안 보정이 일정해야 손에 든 탄창이 끼우는 위치(장착 자세)와 어긋나지 않는다(탄창은 잡을 때 손목 기준 오프셋으로 붙는다).
앞서 넣었던 LBack 페이드(NotReloadL)는 쥐기/끼우기 때 값이 달라져 끼울 때 9cm 어긋남을 만들어서 끄고(TargetMaximum=1) 노드는 남겨 둔다.   -> Data/lyra_reload_palm_fix.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_reload_palm_fix.json'
R = {}
nums = [a for a in sys.argv[1:] if a.replace('-', '', 1).replace('.', '', 1).isdigit()]
D = [float(x) for x in nums[:3]] if len(nums) >= 3 else [-4.8, 7.2, 2.1]
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    nodes = {str(n.get_node_path()): n for n in g.get_nodes()}
    if 'NotReloadL' in nodes: R['fade_off'] = bool(c.set_pin_default_value('NotReloadL.TargetMaximum', '1', True, False))
    R['has'] = 'RlDelta' in nodes
    if not R['has']:
        U = '/Script/ControlRig.RigUnit_'
        for typ, nm in (('MathFloatMul', 'RlEnvRaw'), ('MathFloatClamp', 'RlEnv'), ('MathFloatMul', 'RlEnvTp'), ('MathVectorScale', 'RlDelta'), ('MathVectorAdd', 'RLV2')):
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
        L = [c.add_link('RLCX.Value', 'RlEnvRaw.A'), c.add_link('RlEnvRaw.Result', 'RlEnv.Value'), c.add_link('RlEnv.Result', 'RlEnvTp.A'), c.add_link('TpW.Result', 'RlEnvTp.B'),
             c.add_link('RlEnvTp.Result', 'RlDelta.Factor'), c.add_link('RLV.Result', 'RLV2.A'), c.add_link('RlDelta.Result', 'RLV2.B')]
        R['links'] = [bool(x) for x in L]
        R['broke'] = bool(c.break_link('RLV.Result', 'LHandOff3.B')); R['relink'] = bool(c.add_link('RLV2.Result', 'LHandOff3.B'))
        R['set_static'] = [bool(c.set_pin_default_value('RlEnvRaw.B', '%.6f' % (1.0 / 6.0), True, False)), bool(c.set_pin_default_value('RlEnv.Minimum', '0', True, False)), bool(c.set_pin_default_value('RlEnv.Maximum', '1', True, False))]
    R['delta'] = D; R['set_delta'] = bool(c.set_pin_default_value('RlDelta.Value', '(X=%.4f,Y=%.4f,Z=%.4f)' % tuple(D), True, False))
    nodes = {str(n.get_node_path()): n for n in g.get_nodes()}
    lb = [p for p in nodes['LHandOff3'].get_pins() if str(p.get_name()) == 'B'][0]
    R['LHandOff3.B_from'] = [str(t.get_pin_path()) for t in lb.get_linked_source_pins()]
    cr.recompile_vm(); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(cr, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PALM_FIX', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
