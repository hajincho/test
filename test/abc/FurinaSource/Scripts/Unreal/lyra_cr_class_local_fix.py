"""에디터(편집 전용): lyra_cr_class_lengths.py 1) 보정 - 기준 자세 '로컬' 이동을 GetTransform(LocalSpace, 초기값)으로 읽으면 0 에 가깝게 나와 몸이 엉덩이로 접혔음.
 -> 부모·자식의 기준 자세 전역 변환으로 상대 변환(MakeRelative)을 계산해 SetTranslation(Local) 에 넣음. 부모는 Data/furina_bone_tree.json(푸리나 뼈대 계층). -> Saved/CRClassLocalFix.json"""
import json, traceback
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); FS = ROOT / 'FurinaSource'; R = {'fail': [], 'n': 0}
def run():
    tree = json.loads((FS / 'Data' / 'furina_bone_tree.json').read_text(encoding='utf-8'))['bones']
    parent = {n.replace(' ', '-'): (b['p'].replace(' ', '-') if b['p'] else None) for n, b in tree.items()}
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
    for k in [k for k in N if k.startswith('CL_I_')]:
        b = k[5:]; pa = parent.get(b)
        if not pa or 'CL_P_' + b in N: continue
        c.set_pin_default_value(k + '.Space', 'GlobalSpace', True, False)
        add('RigUnit_GetTransform', 'CL_P_' + b, -6300, -6000, Item=B(pa), Space='GlobalSpace', bInitial='True')
        add('RigUnit_MathTransformMakeRelative', 'CL_R_' + b, -5800, -6000)
        link(k + '.Transform', 'CL_R_%s.Global' % b); link('CL_P_%s.Transform' % b, 'CL_R_%s.Parent' % b)
        c.break_link(k + '.Transform.Translation', 'CL_S_%s.Value' % b); link('CL_R_%s.Local.Translation' % b, 'CL_S_%s.Value' % b)
        R['n'] += 1
    unreal.BlueprintEditorLibrary.compile_blueprint(cr); cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()[-1200:]
R['done'] = True; (ROOT / 'Saved' / 'CRClassLocalFix.json').write_text(json.dumps(R, indent=1), encoding='utf-8'); print('CR_LOCALFIX', R)
