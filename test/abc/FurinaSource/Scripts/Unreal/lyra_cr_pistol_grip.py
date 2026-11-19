"""Lyra 에디터(`py <파일> [X Y Z]`): 1인칭 권총 양손 파지 - 왼손(받치는 손) 목표를 권총 손잡이 아래/앞으로 옮긴다 (3인칭은 권총일 때 CR Alpha 0 이라 영향 없음).
 곡선 PistolOn(ABP 가 FurinaPistolOn 활성이면 1) x 1인칭 가중치 RlFpW  ->  PistW.
 PistGrip = Lerp(LHandOff3, 권총 지지 위치(소총 컴포넌트 기준 X왼쪽·Y앞·Z위 cm), PistW)  -> LHandOff3 를 쓰던 곳(RgFrz.A, RgOut.A 등)으로 연결.
 기본 지지 위치 = FBX(Armpist.fbx) 에서 계산한 (-0.1, -18.8, -12.8).  값을 바꾸려면 같은 스크립트를 인자만 바꿔 다시 실행 (PistGrip.B 갱신).   -> Data/lyra_cr_pistol_grip.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_pistol_grip.json'
U = '/Script/ControlRig.RigUnit_'
nums = []
for a in sys.argv[1:]:
    try: nums.append(float(a))
    except ValueError: pass
T = nums[:3] if len(nums) >= 3 else [-0.1, -18.8, -12.8]
R = {'target': T}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('LHandOff3', 'RlFpW'): assert need in N, 'missing ' + need
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    if 'PistGrip' not in N:
        mk('GetCurveValue', 'PistC', Curve='PistolOn'); mk('MathFloatMul', 'PistW'); mk('MathVectorLerp', 'PistGrip')
        link('PistC.Value', 'PistW.A'); link('RlFpW.Result', 'PistW.B')
        dst = []
        for p in N['LHandOff3'].get_pins():
            if str(p.get_name()) == 'Result': dst = [str(s.get_pin_path()) for s in p.get_linked_target_pins()]
        R['old_dst'] = dst
        link('LHandOff3.Result', 'PistGrip.A'); link('PistW.Result', 'PistGrip.T')
        for d in dst:
            try: c.break_link('LHandOff3.Result', d)
            except Exception as e: L.append(['break', d, str(e)[:60]])
            link('PistGrip.Result', d)
    R['set_B'] = bool(c.set_pin_default_value('PistGrip.B', '(X=%.4f,Y=%.4f,Z=%.4f)' % tuple(T), True, False))
    R['links'] = L
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CR_PISTOL_GRIP', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
