"""Lyra 에디터(`py <파일> [dY]`, 기본 9.5): 1인칭 권총일 때 오른손(손목) 목표를 권총 손잡이 쪽으로 앞당긴다.
 원인(PIE 측정 lyra_pistol_grip_probe_g7.json): 프레임 경계 Y -8.5~10.8(소총 컴포넌트 기준)인데 오른손 손가락 끝이 Y -7~-13 -> 손잡이 뒤 3~5 cm 에서 떨어져 있었다(FBX 의 손 위치는 FBX 프레임 기준이라 P220 모델과 어긋남).
 RRHOff.Vector(손목 목표, 총 기준) = Lerp(소총값 (-3.719,-10.781,-5.149), 권총값 (같은 X,Z; Y + dY), PistW).   노드: PistRV.   -> Data/lyra_cr_pistol_rhand.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_pistol_rhand.json'
U = '/Script/ControlRig.RigUnit_'
nums = []
for a in sys.argv[1:]:
    try: nums.append(float(a))
    except ValueError: pass
DY = nums[0] if nums else 9.5
R = {'dY': DY}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('RRHOff', 'PistW'): assert need in N, 'missing ' + need
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    if 'PistRV' not in N:
        c.add_unit_node_from_struct_path(U + 'MathVectorLerp', 'Execute', unreal.Vector2D(0, 0), 'PistRV')
        c.set_pin_default_value('PistRV.A', '(X=-3.719000,Y=-10.781000,Z=-5.149000)', True, False)
        link('PistW.Result', 'PistRV.T'); link('PistRV.Result', 'RRHOff.Vector')
    R['set_B'] = bool(c.set_pin_default_value('PistRV.B', '(X=-3.719000,Y=%.6f,Z=-5.149000)' % (-10.781 + DY), True, False))
    R['links'] = L
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CR_PISTOL_RHAND', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
