"""Lyra 에디터(`py <파일> [전진cm]`, 기본 4): 1인칭(비조준) 총을 앞으로 뺀다.
 - OffHS.A (허리 자세 총 위치, 눈 기준 X왼쪽·Y앞·Z위) = (-7, 10, -10) -> (-7, 10 + D, -10).  견착(OffHS.B)과 정조준(OffAim.B)은 그대로.
 - 왼팔 도달: 이 자세는 원래 팔 길이 39.2 중 38.4 까지 뻗어 있어(set_fp_poses.py) 총만 앞으로 가면 왼손이 닿지 않는다 -> 왼손을 핸드가드를 따라 D 만큼 뒤로 미끄러뜨려 손의 몸 기준 위치를 유지한다.
   (3인칭의 LBack = -9.6 x LBackW 와 같은 방식)  가중치 = 1인칭(RlFpW) x 정조준 아님(NotAds) x 견착 아님(1-ShW) x 재장전 아님(1-ReloadSm) -> 재장전의 총 기준 손 경로는 그대로.
 오른손은 권총손잡이에 IK 로 붙어 총을 따라 움직인다.
 3인칭 보정: TpD.A.Y = 6.0748 - D (3인칭 총 위치 불변).
 노드: FpNotSh, FpBk1, FpBk2, FpNotRl, FpBk3, FpBack, AllLeftBack2 -> LBackV.Y.   값을 바꾸려면 같은 스크립트를 다른 인자로 다시 실행(OffHS.A.Y 와 FpBack.B 갱신).  -> Data/lyra_fp_gun_forward.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_gun_forward.json'
U = '/Script/ControlRig.RigUnit_'
nums = [float(a) for a in sys.argv[1:] if a.replace('.', '', 1).replace('-', '', 1).isdigit()]
FWD = nums[0] if nums else 4.0
R = {'forward_cm': FWD}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('OffHS', 'TpD', 'RlFpW', 'NotAds', 'ShW', 'ReloadSm', 'AllLeftBack', 'LBackV'): assert need in N, 'missing ' + need
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    R['before_A'] = [str(p.get_default_value()) for p in N['OffHS'].get_pins() if str(p.get_name()) == 'A']
    R['set_A'] = bool(c.set_pin_default_value('OffHS.A', '(X=-7.000000,Y=%.6f,Z=-10.000000)' % (10.0 + FWD), True, False))
    # 3인칭: 총의 절대 위치 = OffHS + TpD 이므로 허리 자세 TpD.A 의 Y 를 D 만큼 줄여 3인칭 위치는 그대로 둔다 (원래 TpD.A = (-0.8544, 6.0748, -14.5087))
    R['set_TpD_A'] = bool(c.set_pin_default_value('TpD.A', '(X=-0.854400,Y=%.6f,Z=-14.508700)' % (6.0748 - FWD), True, False))
    if 'AllLeftBack2' not in N:
        mk('MathFloatRemap', 'FpNotSh', SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        mk('MathFloatRemap', 'FpNotRl', SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        mk('MathFloatMul', 'FpBk1'); mk('MathFloatMul', 'FpBk2'); mk('MathFloatMul', 'FpBk3'); mk('MathFloatMul', 'FpBack'); mk('MathFloatAdd', 'AllLeftBack2')
        link('ShW.Result', 'FpNotSh.Value'); link('ReloadSm.Result', 'FpNotRl.Value')
        link('RlFpW.Result', 'FpBk1.A'); link('NotAds.Result', 'FpBk1.B'); link('FpBk1.Result', 'FpBk2.A'); link('FpNotSh.Result', 'FpBk2.B')
        link('FpBk2.Result', 'FpBk3.A'); link('FpNotRl.Result', 'FpBk3.B'); link('FpBk3.Result', 'FpBack.A')
        link('AllLeftBack.Result', 'AllLeftBack2.A'); link('FpBack.Result', 'AllLeftBack2.B')
        srcs = []
        for p in N['LBackV'].get_pins():
            if str(p.get_name()) == 'Y': srcs = [str(s.get_pin_path()) for s in p.get_linked_source_pins()]
        R['old_y_src'] = srcs
        for s in srcs:
            try: c.break_link(s, 'LBackV.Y')
            except Exception as e: L.append(['break', s, str(e)[:60]])
        link('AllLeftBack2.Result', 'LBackV.Y')
    R['set_B'] = bool(c.set_pin_default_value('FpBack.B', '%.4f' % (-FWD), True, False))
    R['links'] = L
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_GUN_FORWARD', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
