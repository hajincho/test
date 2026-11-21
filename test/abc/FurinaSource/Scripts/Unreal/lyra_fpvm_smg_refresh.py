"""에디터(편집 전용): MP40·MP38·StG44 1인칭 메시·애니 다시 가져오기 + 캐릭터 BP 의 기관단총 정조준 변환 값 갱신(2026-11-21 왼손 받침 위치 수정분).
 왼손: MP38/MP40 = 탄창 하우징, StG44 = 탄창 앞 총열 덮개. 총 위치가 바뀌어 정조준 값(Data/fpvm_view_alignment.json)도 다시 넣음. -> Saved/FPVMSmgRefresh.json("done": true)"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lyra_fpvm_reimport as RI
import lyra_hist_fx as H
from lyra_fpvm_optics import PAWN, Graph, literal, view_transform
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
def ads():
    pawn = unreal.load_asset(PAWN); g = Graph(pawn); out = {}
    for key in ('mp40', 'mp38', 'stg44'):
        loc, rot = view_transform(key); n = key.upper()
        nl = [v for k, v in g.nodes.items() if k.startswith('SMG') and k.endswith('_ADSLocation_' + n)]; nr = [v for k, v in g.nodes.items() if k.startswith('SMG') and k.endswith('_ADSRotation_' + n)]
        assert len(nl) == 1 and len(nr) == 1, (key, len(nl), len(nr))
        literal(nl[0], 'FurinaVMAdsLoc', loc); literal(nr[0], 'FurinaVMAdsRot', rot); out[key] = [loc, rot]
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn); assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    out['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(pawn, False)); return out
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
try:
    keys = [k for k in ('mp40', 'mp38', 'stg44') if len(sys.argv) < 2 or sys.argv[-1].endswith('.py') or k in sys.argv[-1].split('+')]
    for name, fn in (('smg', lambda: {k: RI.smg(k) for k in keys}), ('ads', ads), ('sockets', H.sockets)):   # 메시를 다시 가져오면 VM_Muzzle 소켓이 빠질 수 있어 다시
        try: R[name] = fn()
        except Exception: R[name] = 'ERROR ' + traceback.format_exc()[-1500:]
finally:
    unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
R['done'] = True
(ROOT / 'Saved' / 'FPVMSmgRefresh.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8'); print('FPVM_SMG_REFRESH', json.dumps(R, default=str)[:400])
