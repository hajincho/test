"""Lyra 에디터(`py <파일> [X Y Z]`): CR 1인칭 권총 왼손 지지 위치(PistGrip.B)에 재장전 곡선 PRX/PRY/PRZ(Furina_Pistol_Reload 가 가짐)를 더한다.
 노드: PRCx/PRCy/PRCz(GetCurveValue), PRVec(MakeVector), PistBAdd(Add: A=지지 위치, B=PRVec) -> PistGrip.B.   지지 위치 기본 (-0.1,-11.5,-12.8) (lyra_cr_pistol_grip.py 와 같은 값)
 곡선 PRX/PRY/PRZ 는 릭에 등록(GetCurveValue 는 등록된 곡선만 읽음).   -> Data/lyra_cr_pistol_reload.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_pistol_reload.json'
U = '/Script/ControlRig.RigUnit_'
nums = []
for a in sys.argv[1:]:
    try: nums.append(float(a))
    except ValueError: pass
T = nums[:3] if len(nums) >= 3 else [-0.1, -11.5, -12.8]
R = {'target': T}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); h = cr.get_hierarchy()
    have = [str(k.name) for k in h.get_all_keys(True) if k.type == unreal.RigElementType.CURVE]
    for n in ('PRX', 'PRY', 'PRZ'):
        if n not in have: cr.get_hierarchy_controller().add_curve(n, 0.0, False)
    del h
    c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes(); assert 'PistGrip' in N
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    if 'PistBAdd' not in N:
        for ax in 'xyz': mk('GetCurveValue', 'PRC' + ax, Curve='PR' + ax.upper())
        mk('MathVectorMake', 'PRVec'); mk('MathVectorAdd', 'PistBAdd')
        link('PRCx.Value', 'PRVec.X'); link('PRCy.Value', 'PRVec.Y'); link('PRCz.Value', 'PRVec.Z')
        link('PRVec.Result', 'PistBAdd.B'); link('PistBAdd.Result', 'PistGrip.B')
    R['set_A'] = bool(c.set_pin_default_value('PistBAdd.A', '(X=%.4f,Y=%.4f,Z=%.4f)' % tuple(T), True, False))
    R['links'] = L
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CR_PISTOL_RELOAD', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
