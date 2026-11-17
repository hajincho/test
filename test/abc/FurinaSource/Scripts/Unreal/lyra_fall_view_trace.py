"""Lyra 에디터: 푸리나 폰 EventGraph 에서 시점 전환(FurinaFPWanted / FPCamera / ViewTP / 카메라 활성)과 낙하(Falling/Landed/MovementMode/Fall/Velocity) 관련 노드를 찾아
핀 값/연결을 출력 -> Data/lyra_fall_view_trace.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fall_view_trace.json'
R = {}
KEYS = ('k2node_fpvh', 'k2node_fp_', 'k2node_fpv_', 'fpwanted', 'fall', 'land', 'movementmode', 'mode', 'airborne', 'inair', 'velocity', 'wanted', 'fpcam', 'viewtoggle', 'viewfp', 'fpview', 'setactive', 'activate')
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); rows = []
    for n in ed.list_all_nodes():
        nm = n.get_name()
        if any(k in nm.lower() for k in KEYS):
            row = {'node': nm, 'cls': n.get_class().get_name()}
            try: row['pins'] = [[str(p.get_pin_name()), str(p.get_pin_value())[:60], [c.get_owning_node().get_name() for c in p.list_connected_pins()][:3]] for p in n.list_all_pins() if str(p.get_pin_value()) or p.list_connected_pins()][:8]
            except Exception as e: row['err'] = str(e)[:60]
            rows.append(row)
    R['nodes'] = rows[:200]; R['count'] = len(rows)
    # 이벤트 노드 이름 전체
    R['events'] = [n.get_name() for n in ed.list_all_nodes() if n.get_class().get_name() in ('K2Node_Event', 'K2Node_CustomEvent', 'K2Node_EnhancedInputActionEvent', 'K2Node_ComponentBoundEvent')][:60]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FALL_VIEW', R.get('count'), R.get('error', '')[-200:])
