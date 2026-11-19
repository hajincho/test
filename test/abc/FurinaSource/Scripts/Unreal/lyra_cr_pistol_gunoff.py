"""Lyra 에디터(`py <파일> [X Y Z]`): 1인칭 권총 위치 오프셋 - 소총 기준으로 맞춰진 허리/견착 총 위치(OffHS)에 권총일 때만(PistW) 눈 기준 오프셋(X왼쪽·Y앞·Z위 cm)을 더한다.
 소총 위치에서는 권총 손잡이/두 손이 화면 아래 밖으로 나가므로 위/가운데로 올린다.   노드: PistGOff(Scale: 오프셋 x PistW), PistGAdd(Add) -> OffHS.Result 를 쓰던 곳으로.
 값 변경: 같은 스크립트를 다른 인자로 다시 실행 (PistGOff.Value 갱신).   -> Data/lyra_cr_pistol_gunoff.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_pistol_gunoff.json'
U = '/Script/ControlRig.RigUnit_'
nums = []
for a in sys.argv[1:]:
    try: nums.append(float(a))
    except ValueError: pass
T = nums[:3] if len(nums) >= 3 else [4.0, 0.0, 7.0]
R = {'offset': T}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('OffHS', 'PistW'): assert need in N, 'missing ' + need
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    if 'PistGAdd' not in N:
        mk('MathVectorScale', 'PistGOff'); mk('MathVectorAdd', 'PistGAdd')
        link('PistW.Result', 'PistGOff.Factor')
        dst = []
        for p in N['OffHS'].get_pins():
            if str(p.get_name()) == 'Result': dst = [str(s.get_pin_path()) for s in p.get_linked_target_pins()]
        R['old_dst'] = dst
        link('OffHS.Result', 'PistGAdd.A'); link('PistGOff.Result', 'PistGAdd.B')
        for d in dst:
            try: c.break_link('OffHS.Result', d)
            except Exception as e: L.append(['break', d, str(e)[:60]])
            link('PistGAdd.Result', d)
    R['set'] = bool(c.set_pin_default_value('PistGOff.Value', '(X=%.4f,Y=%.4f,Z=%.4f)' % tuple(T), True, False))
    R['links'] = L
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CR_PISTOL_GUNOFF', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
