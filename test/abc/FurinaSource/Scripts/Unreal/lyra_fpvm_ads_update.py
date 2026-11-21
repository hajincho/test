"""에디터/헤드리스(편집 전용): 캐릭터 BP 의 정조준 변환 값(FurinaVMAdsLoc/Rot 상수)을 Data/fpvm_view_alignment.json 으로 갱신.
 소총 대기 자세(Kar98k x 32, G43 x 29)와 권총 높이(28, -6, -6.5)를 바꿔서 다시 계산한 값. 기관단총은 lyra_fpvm_smg_bp.py 가 넣음. -> Saved/FPVMAdsUpdate.json"""
import json, sys
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import PAWN, Graph, literal, view_transform, update_iron_sight_transforms
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
pawn = unreal.load_asset(PAWN)
update_iron_sight_transforms(pawn); R['rifles'] = 'kar98k,g43'
g = Graph(pawn)
for key, optic in (('kar98k_zf39', 'ZF39'), ('kar98k_zf41', 'ZF41'), ('g43_zf4', 'ZF4')):
    loc, rot = view_transform(key)
    literal(g.nodes['ScopeView_Loc_' + optic], 'FurinaVMAdsLoc', loc); literal(g.nodes['ScopeView_Rot_' + optic], 'FurinaVMAdsRot', rot); R[key] = [loc, rot]
for key in ('p38', 'p08', 'pp'):
    loc, rot = view_transform(key); n = key.upper()
    literal(g.nodes['HistoryPrimary_ADSLocation_' + n], 'FurinaVMAdsLoc', loc); literal(g.nodes['HistoryPrimary_ADSRotation_' + n], 'FurinaVMAdsRot', rot); R[key] = [loc, rot]
unreal.BlueprintEditorLibrary.compile_blueprint(pawn); assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(pawn, False))
(ROOT / 'Saved' / 'FPVMAdsUpdate.json').write_text(json.dumps(R, indent=1), encoding='utf-8'); print('FPVM_ADS_UPDATE', R['saved'])
