"""에디터(편집 전용): lyra_cr_class_lengths.py 1) 2차 보정 - 이 컨트롤 릭 계층은 Hips 에 100배 크기가 있어 기준 자세 '로컬' 이동이 1/100 로 나오고,
 재생 중 포즈는 크기 1 이라 몸이 엉덩이로 접혔음. 크기와 무관하게:
   자식 새 전역 위치 = 부모 지금 위치 + 부모 지금 회전 × (부모 기준 회전⁻¹ × (자식 기준 위치 - 부모 기준 위치))   (cm, 부모부터 차례로)
 -> SetTranslation(GlobalSpace). 부모·깊이는 Data/furina_bone_tree.json. -> Saved/CRClassGlobalFix.json"""
import json, traceback
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); FS = ROOT / 'FurinaSource'; R = {'fail': [], 'n': 0}
def run():
    tree = json.loads((FS / 'Data' / 'furina_bone_tree.json').read_text(encoding='utf-8'))['bones']
    parent = {n.replace(' ', '-'): (b['p'].replace(' ', '-') if b['p'] else None) for n, b in tree.items()}
    def depth(n):
        d = 0
        while parent.get(n): n = parent[n]; d += 1
        return d
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    N = {str(n.get_node_path()): n for n in g.get_nodes()}
    cr.set_auto_vm_recompile(False)   # 연결 하나마다 재컴파일하면 수백 번 -> 에디터가 멈춘 것처럼 오래 걸림
    S = lambda n: getattr(unreal, n).static_struct().get_path_name(); B = lambda n: '(Type=Bone,Name="%s")' % n
    def add(unit, name, x, y, **d):
        node = c.add_unit_node_from_struct_path(S(unit), 'Execute', unreal.Vector2D(x, y), name)
        if not node: R['fail'].append('add ' + name)
        for k, v in d.items():
            if not c.set_pin_default_value('%s.%s' % (name, k), v, True, False): R['fail'].append('def %s.%s' % (name, k))
    def link(a, b):
        if not c.add_link(a, b, False): R['fail'].append('link %s -> %s' % (a, b))
    body = [n.replace(' ', '-') for n in json.loads((FS / 'Data' / 'class_infantry_build.json').read_text(encoding='utf-8'))['body_bones'] if n != 'Hips']
    have = {k[5:] for k in N if k.startswith('CL_S_')}
    sets = [b for b in body if b in have]   # 원래(lengths) 순서: 부모가 앞, 손가락만 손목보다 앞(손목을 옮길 때 자식이 따라가 문제없음). 깊이순 재배열은 RigVM 순서 검사에 걸림
    # 실행 순서: HipsSet -> (깊이 순) -> 원래 첫 노드
    after = [str(t.get_pin_path()) for t in N['CL_S_' + [k[5:] for k in N if k.startswith('CL_S_')][-1]].find_pin('ExecutePin').get_linked_target_pins()] if False else None
    old_first = []
    for b in sets:
        for t in N['CL_S_' + b].find_pin('ExecutePin').get_linked_target_pins():
            if not str(t.get_pin_path()).startswith('CL_S_'): old_first.append(str(t.get_pin_path()))
        for p in list(N['CL_S_' + b].find_pin('ExecutePin').get_linked_source_pins()) + []:
            c.break_link(str(p.get_pin_path()), 'CL_S_%s.ExecutePin' % b)
        for t in list(N['CL_S_' + b].find_pin('ExecutePin').get_linked_target_pins()):
            c.break_link('CL_S_%s.ExecutePin' % b, str(t.get_pin_path()))
    for t in [str(t.get_pin_path()) for t in N['CL_HipsSet'].find_pin('ExecutePin').get_linked_target_pins()]:
        c.break_link('CL_HipsSet.ExecutePin', t)
    prev = 'CL_HipsSet'
    for b in sets:
        pa = parent[b]
        c.set_pin_default_value('CL_I_%s.Space' % b, 'GlobalSpace', True, False)
        if 'CL_D_' + b not in N: add('RigUnit_MathVectorSub', 'CL_D_' + b, -5500, -6000); link('CL_I_%s.Transform.Translation' % b, 'CL_D_%s.A' % b); link('CL_P_%s.Transform.Translation' % b, 'CL_D_%s.B' % b)
        if 'CL_Q_' + b in N: c.remove_nodes_by_name(['CL_Q_' + b, 'CL_U_' + b, 'CL_C_' + b, 'CL_V_' + b, 'CL_N_' + b], False)
        add('RigUnit_MathQuaternionInverse', 'CL_Q_' + b, -5400, -5900); link('CL_P_%s.Transform.Rotation' % b, 'CL_Q_%s.Value' % b)
        add('RigUnit_MathQuaternionRotateVector', 'CL_U_' + b, -5300, -6000); link('CL_Q_%s.Result' % b, 'CL_U_%s.Transform' % b); link('CL_D_%s.Result' % b, 'CL_U_%s.Vector' % b)
        add('RigUnit_GetTransform', 'CL_C_' + b, -5300, -5800, Item=B(pa), Space='GlobalSpace')
        add('RigUnit_MathQuaternionRotateVector', 'CL_V_' + b, -5100, -6000); link('CL_C_%s.Transform.Rotation' % b, 'CL_V_%s.Transform' % b); link('CL_U_%s.Result' % b, 'CL_V_%s.Vector' % b)
        add('RigUnit_MathVectorAdd', 'CL_N_' + b, -4900, -6000); link('CL_C_%s.Transform.Translation' % b, 'CL_N_%s.A' % b); link('CL_V_%s.Result' % b, 'CL_N_%s.B' % b)
        for sp in list(N['CL_S_' + b].find_pin('Value').get_linked_source_pins()): c.break_link(str(sp.get_pin_path()), 'CL_S_%s.Value' % b)
        c.set_pin_default_value('CL_S_%s.Space' % b, 'GlobalSpace', True, False)
        link('CL_N_%s.Result' % b, 'CL_S_%s.Value' % b)
        link('%s.ExecutePin' % prev, 'CL_S_%s.ExecutePin' % b); prev = 'CL_S_' + b; R['n'] += 1
    for t in (set(old_first) or {'LIK.ExecutePin'}): link('%s.ExecutePin' % prev, t)
    R['old_first'] = sorted(set(old_first)); R['order'] = sets[:8]
    cr.set_auto_vm_recompile(True); unreal.BlueprintEditorLibrary.compile_blueprint(cr); cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()[-1200:]
R['done'] = True; (ROOT / 'Saved' / 'CRClassGlobalFix.json').write_text(json.dumps(R, indent=1), encoding='utf-8'); print('CR_GLOBALFIX', R)
