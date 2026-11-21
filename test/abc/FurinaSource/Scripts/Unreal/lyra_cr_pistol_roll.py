"""Lyra 에디터(`py <파일>`): 1인칭 권총 - 오른손(과 손에 붙은 소총 컴포넌트)을 총 기준으로 굴려/옮겨 손가락이 권총 손잡이를 뚫지 않게 한다.
 Blender 최적화(Scripts/Blender/pistol_hand_penetration_roll.py -> Data/pistol_roll_constants.json)가 구한 '총을 손에 대해 움직이는 자세'를 반대로 손(=소총 컴포넌트)에 적용하고,
 프레임(FurinaPistolFrame) 상대 변환은 같은 값만큼 BP 에서 보정해 총의 보이는 위치/각도는 그대로 둔다 (lyra_pistol_fp_roll_bp.py).
 CR 변경:  PistQw = Slerp(항등, Q, PistW);  GRotP = GRotR x PistQw;  RRHOff.Transform / RRHRot.A <- GRotP;   PistRV.B = Vec_pist (손목 위치 보정, 총 기준)
 왼손은 GRotR 그대로 (총 프레임 기준 위치 불변).   -> Data/lyra_cr_pistol_roll.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
U = '/Script/ControlRig.RigUnit_'
K = json.load(open(D + r'\pistol_roll_constants.json')); R = {'const': K}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('GRotR', 'RRHOff', 'RRHRot', 'PistW', 'PistRV'): assert need in N, 'missing ' + need
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    q = K['q_Q']
    if 'GRotP' not in N:
        for nm, typ in (('PistQw', 'MathQuaternionSlerp'), ('GRotP', 'MathQuaternionMul')):
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
        link('PistW.Result', 'PistQw.T'); link('GRotR.Result', 'GRotP.A'); link('PistQw.Result', 'GRotP.B')
        for dst in ('RRHOff.Transform', 'RRHRot.A'):
            try: c.break_link('GRotR.Result', dst)
            except Exception as e: L.append(['break', dst, str(e)[:60]])
            link('GRotP.Result', dst)
    R['set_B'] = bool(c.set_pin_default_value('PistQw.B', '(X=%.8f,Y=%.8f,Z=%.8f,W=%.8f)' % tuple(q), True, False))
    R['set_A'] = bool(c.set_pin_default_value('PistQw.A', '(X=0.0,Y=0.0,Z=0.0,W=1.0)', True, False))
    v = K['Vec_pist']; R['set_vec'] = bool(c.set_pin_default_value('PistRV.B', '(X=%.6f,Y=%.6f,Z=%.6f)' % tuple(v), True, False))
    R['links'] = L
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\lyra_cr_pistol_roll.json', 'w'), indent=1, default=str); print('LYRA_CR_PISTOL_ROLL', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
