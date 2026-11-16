"""Lyra 에디터(`py <파일> keep`): 발사 경로(FurinaRifleShot) 노드 덤프: 조준 추적 K2Node_FPF_Aim, 스폰 변환 K2Node_FPF_ShotXf 등 K2Node_FPF_* / FPN_Shot* / M4_* 노드 -> Data/lyra_shot_nodes_dump.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_shot_nodes_dump.json'
R = {}
def info(n):
    pins = []
    for p in n.list_all_pins():
        con = [c.get_owning_node().get_name() + '.' + str(c.get_pin_name()) for c in p.list_connected_pins()]
        if con or p.get_pin_value(): pins.append([str(p.get_pin_name()), str(p.get_pin_value())[:80], con[:3]])
    return {'title': str(n.get_node_title()).replace('\n', ' '), 'pins': pins}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    R['nodes'] = {n.get_name(): info(n) for n in ed.list_all_nodes() if n.get_name().startswith(('K2Node_FPF_', 'FPN_Shot', 'FPN_Sh', 'K2Node_FPA'))}
    R['count'] = len(R['nodes'])
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_SHOT_NODES', R.get('count'), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
