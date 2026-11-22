"""에디터(편집 전용): lyra_cr_class_lengths.py 의 2) 단계 - CR_FurinaSecondary 의 두 뼈 IK(LIK/RIK 다리, RRArmIK/RLArmIK 팔, Fg*IK 손가락) 길이를
 기준 자세(메시 초기값) 관절 거리로 연결(푸리나 고정값 대신) -> Saved/CRClassIKLen.json"""
import json, traceback
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {'fail': [], 'ik': []}
NAMES = ('LIK', 'RIK', 'RRArmIK', 'RLArmIK', 'FgIndexIK', 'FgMiddleIK', 'FgRingIK', 'FgLittleIK')
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    N = {str(n.get_node_path()): n for n in g.get_nodes()}
    S = lambda n: getattr(unreal, n).static_struct().get_path_name(); B = lambda n: '(Type=Bone,Name="%s")' % n
    def add(unit, name, x, y, **d):
        node = c.add_unit_node_from_struct_path(S(unit), 'Execute', unreal.Vector2D(x, y), name)
        if not node: R['fail'].append('add ' + name)
        for k, v in d.items():
            if not c.set_pin_default_value('%s.%s' % (name, k), v, True, False): R['fail'].append('def %s.%s' % (name, k))
    def link(a, b):
        if not c.add_link(a, b, False): R['fail'].append('link %s -> %s' % (a, b))
    for k in NAMES:
        if 'CL_%s_Ad' % k in N or k not in N: continue
        n = N[k]; pv = {}
        for p in n.get_pins():
            pv[str(p.get_name())] = p
        def item(pin):
            nm = [str(sp.get_default_value()) for sp in pin.get_sub_pins() if str(sp.get_name()) == 'Name']
            return nm[0] if nm else str(pin.get_default_value()).split('Name="')[1].split('"')[0]
        a, b, e = item(pv['ItemA']), item(pv['ItemB']), item(pv['EffectorItem'])
        for nm, (p, q) in (('A', (a, b)), ('B', (b, e))):
            gp, gq, dn = 'CL_%s_%sp' % (k, nm), 'CL_%s_%sq' % (k, nm), 'CL_%s_%sd' % (k, nm)
            add('RigUnit_GetTransform', gp, -7000, -6000, Item=B(p), Space='GlobalSpace', bInitial='True')
            add('RigUnit_GetTransform', gq, -7000, -5850, Item=B(q), Space='GlobalSpace', bInitial='True')
            add('RigUnit_MathVectorDistance', dn, -6700, -6000); link(gp + '.Transform.Translation', dn + '.A'); link(gq + '.Transform.Translation', dn + '.B')
            link(dn + '.Result', '%s.Item%sLength' % (k, nm))
        R['ik'].append([k, a, b, e])
    unreal.BlueprintEditorLibrary.compile_blueprint(cr); cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()[-1200:]
R['done'] = True; (ROOT / 'Saved' / 'CRClassIKLen.json').write_text(json.dumps(R, indent=1), encoding='utf-8'); print('CR_IKLEN', R)
