"""에디터(편집 전용): ABP_Furina 의 컨트롤 릭 노드 'Set Initial Transforms From Mesh'(set_ref_pose_from_skeleton) 켜기
 -> CR_FurinaSecondary 의 기준 자세(초기값)가 각 메시(병과 캐릭터) 기준 자세가 됨(푸리나 메시는 같은 값이라 변화 없음). -> Saved/ABPRefPose.json"""
import json, traceback
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
try:
    abp = unreal.load_asset('/Game/Furina/ABP_Furina')
    nodes = [o for o in unreal.ObjectIterator(unreal.Object) if o.get_outermost() == abp.get_outermost() and o.get_class().get_name() == 'AnimGraphNode_ControlRig']
    for o in nodes:
        nd = o.get_editor_property('node'); R[o.get_name() + '_before'] = nd.get_editor_property('set_ref_pose_from_skeleton')
        nd.set_editor_property('set_ref_pose_from_skeleton', True); o.set_editor_property('node', nd)
        R[o.get_name() + '_after'] = o.get_editor_property('node').get_editor_property('set_ref_pose_from_skeleton')
    unreal.BlueprintEditorLibrary.compile_blueprint(abp); R['status'] = str(abp.get_editor_property('status')); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(abp, False))
except Exception: R['error'] = traceback.format_exc()[-1000:]
R['done'] = True; (ROOT / 'Saved' / 'ABPRefPose.json').write_text(json.dumps(R, indent=1), encoding='utf-8'); print('ABP_REFPOSE', R)
