"""Lyra 에디터: 앉기/걷기 속도 관련 노드(FPT_OwnSpd, WalkSpd, RunSpd, CapSpeed*, CrouchFlag*)의 핀 값/연결 + 이 노드들로 이어지는 실행 상위 노드 -> Data/lyra_crouch_speed_trace3.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_crouch_speed_trace3.json'
R = {}
NAMES = ('K2Node_FPT_AimB', 'K2Node_FPT_Aiming', 'K2Node_FPT_CapOn', 'K2Node_FPT_CapOff', 'K2Node_FPT_WasCap', 'K2Node_FPT_CrB', 'K2Node_FPT_Seq', 'K2Node_FPT_AdsOnT', 'K2Node_FPT_Sprint', 'K2Node_FPT_OwnSpeed', 'K2Node_FPT_ShWalk', 'K2Node_FPT_ShRun', 'FPN_ProneWalk', 'FPN_ProneRun', 'K2Node_VariableSet_FSprintOn', 'K2Node_VariableSet_FSprintOff')
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    for nm in NAMES:
        n = nodes.get(nm)
        if not n: R[nm] = 'missing'; continue
        row = {}
        try: row['title'] = str(n.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace('\n', ' ')
        except Exception: pass
        pins = []
        for p in n.list_all_pins():
            try: pins.append([str(p.get_pin_name()), str(p.get_pin_value())[:40], [c.get_owning_node().get_name() + '.' + str(c.get_pin_name()) for c in p.list_connected_pins()][:4]])
            except Exception as e: pins.append(['err', str(e)[:40]])
        row['pins'] = [x for x in pins if x[1] or x[2]]
        R[nm] = row
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CROUCH_TRACE3', R.get('error', 'ok')[-200:])
