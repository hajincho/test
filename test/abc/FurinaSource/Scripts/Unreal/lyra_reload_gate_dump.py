"""Lyra 에디터(`py <파일> keep`): 재장전 입력 경로 덤프. IA_FurinaReload -> M4_ReloadGate -> ... -> FurinaRequestReload 와 그 조건(잔탄/예비탄/재장전중)을 모든 관련 노드와 연결로 -> Data/lyra_reload_gate_dump.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_reload_gate_dump.json'
R = {}
def info(n):
    pins = []
    for p in n.list_all_pins():
        con = [c.get_owning_node().get_name() + '.' + str(c.get_pin_name()) for c in p.list_connected_pins()]
        if con or p.get_pin_value(): pins.append([str(p.get_pin_name()), str(p.get_pin_value())[:60], con[:4]])
    return {'title': str(n.get_node_title()).replace('\n', ' '), 'pins': pins}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); allnodes = {n.get_name(): n for n in ed.list_all_nodes()}
    R['graphs'] = [str(g) for g in unreal.BlueprintEditorLibrary.list_graph_names(bp)]
    seeds = [n for n in allnodes if n.startswith('M4_Reload') or n == 'K2Node_FP_ReloadIA' or 'Reload' in str(allnodes[n].get_node_title())]
    seen = set(); stack = list(seeds); depth = {s: 0 for s in seeds}
    while stack:
        n = stack.pop(0)
        if n in seen or depth[n] > 4: continue
        seen.add(n)
        for p in allnodes[n].list_all_pins():
            for c in p.list_connected_pins():
                m = c.get_owning_node().get_name()
                if m not in depth: depth[m] = depth[n] + 1
                if m not in seen: stack.append(m)
    R['nodes'] = {n: dict(info(allnodes[n]), depth=depth[n]) for n in sorted(seen, key=lambda x: depth[x])}
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_RELOAD_GATE', len(R.get('nodes', {})), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
