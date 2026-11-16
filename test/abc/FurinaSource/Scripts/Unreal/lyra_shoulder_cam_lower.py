"""Lyra 에디터(`py <파일> keep`, PIE 중지 후): 견착(Shoulder) 카메라 높이를 낮춘다. K2Node_FPT_TgtZ (SelectFloat) 의 견착 쪽 값 30 -> 20 (cm, CameraBoom.TargetOffset Z).
먼저 노드와 이웃을 덤프해 어느 핀이 견착 값인지 확인하고, 값이 30 인 핀만 바꾼다. -> Data/lyra_shoulder_cam_lower.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_shoulder_cam_lower.json'
R = {}
NEW = '20.000000'
def info(n):
    pins = []
    for p in n.list_all_pins():
        con = [c.get_owning_node().get_name() + ' [' + str(c.get_owning_node().get_node_title()).replace('\n', ' ')[:30] + '].' + str(c.get_pin_name()) for c in p.list_connected_pins()]
        pins.append([str(p.get_pin_name()), str(p.get_pin_value())[:40], con[:3]])
    return {'title': str(n.get_node_title()).replace('\n', ' '), 'pins': pins}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    n = nodes['K2Node_FPT_TgtZ']; R['before'] = info(n)
    for p in n.list_all_pins():
        if str(p.get_pin_name()) in ('A', 'B') and str(p.get_pin_value()).startswith('30'):
            R['changed_pin'] = str(p.get_pin_name()); p.set_pin_value(NEW)
    R['after'] = info(n)
    # 이 값을 쓰는 아래쪽 노드(이름에 TgtZ/Target/Offset)도 참고용으로
    R['neighbors'] = {m: info(nodes[m]) for m in {c.split(' ')[0] for pp in R['before']['pins'] for c in pp[2]} if m in nodes}
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_SHOULDER_CAM', R.get('changed_pin'), R.get('saved'), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
