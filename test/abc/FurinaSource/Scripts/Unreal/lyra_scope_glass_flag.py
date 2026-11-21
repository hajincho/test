"""에디터: 조준경 유리 재질 다시 만들기(스켈레탈 메시 사용 표시) -> Saved/ScopeGlassFlag.json"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
R = {}
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location('pip_mod', str(Path(__file__).resolve().parent / 'lyra_scope_pip.py'))
    src = (Path(__file__).resolve().parent / 'lyra_scope_pip.py').read_text(encoding='utf-8').split('\ntry: main()')[0]
    ns = {'__name__': 'pip_mod', '__file__': str(Path(__file__).resolve().parent / 'lyra_scope_pip.py')}; exec(compile(src, 'lyra_scope_pip.py', 'exec'), ns)
    rts = {p: ns['make_rt'](p) for p in (4.0, 1.5)}; g = ns['glass_materials'](rts)
    R['mats'] = {k: bool(v.get_editor_property('used_with_skeletal_mesh')) for k, v in g.items()}
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (Path(unreal.Paths.project_dir()).resolve() / 'Saved' / 'ScopeGlassFlag.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
