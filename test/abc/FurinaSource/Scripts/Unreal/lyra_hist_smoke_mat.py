"""에디터: 연기 재질·연기 액터만 다시(lyra_hist_fx.smoke) -> Saved/HistSmokeMat.json"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lyra_hist_fx as H
R = {}
try: R['smoke'] = H.smoke()
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (Path(unreal.Paths.project_dir()).resolve() / 'Saved' / 'HistSmokeMat.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8')
