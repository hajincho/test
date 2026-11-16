"""Lyra 에디터(`py <파일> keep`): 푸리나 폰의 마우스 상하(InvertLookUp?) 로직 덤프: 'Get Look Rate' 함수 그래프, InvertLookUp? 를 쓰는 모든 노드와 그 위/아래 연결 -> Data/lyra_look_dump.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_look_dump.json'
R = {}
def node_info(n):
    pins = []
    for p in n.list_all_pins():
        con = [c.get_owning_node().get_name() + ' [' + str(c.get_owning_node().get_node_title()).replace('\n', ' ')[:28] + '].' + str(c.get_pin_name()) for c in p.list_connected_pins()]
        if con or p.get_pin_value(): pins.append([str(p.get_pin_name()), str(p.get_pin_value())[:60], con[:4]])
    return {'title': str(n.get_node_title()).replace('\n', ' '), 'pins': pins}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    R['graphs'] = [str(g) for g in unreal.BlueprintEditorLibrary.list_graph_names(bp)]
    R['vars_invert'] = [str(v) for v in unreal.BlueprintEditorLibrary.list_member_variable_names(bp) if 'nvert' in str(v) or 'Look' in str(v)]
    for gname in R['graphs']:
        if 'Look' in gname or 'Rate' in gname:
            ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, gname); R['graph:' + gname] = {n.get_name(): node_info(n) for n in ed.list_all_nodes()}
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); allnodes = {n.get_name(): n for n in ed.list_all_nodes()}
    want = set()
    for name, n in allnodes.items():
        t = str(n.get_node_title())
        if 'InvertLookUp' in t or name in ('K2Node_EnhancedInputAction_6', 'K2Node_MacroInstance_3', 'K2Node_MacroInstance_1'): want.add(name)
    # 위/아래 이웃 한 단계씩 포함
    extra = set()
    for name in list(want):
        for p in allnodes[name].list_all_pins():
            for c in p.list_connected_pins(): extra.add(c.get_owning_node().get_name())
    R['nodes'] = {n: node_info(allnodes[n]) for n in sorted(want | extra)}
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_LOOK_DUMP', R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
