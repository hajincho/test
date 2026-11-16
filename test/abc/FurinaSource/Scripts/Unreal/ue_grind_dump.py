"""Editor: dumps the small graph 'Check Rail Below Feet' of Grind_Rail_Component_BP (node names + attributes) and the 'UsingRail?' set nodes of the EventGraph -> Data/grind_dump.json"""
import unreal, json, traceback
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP')
    for gn in ('Check Rail Below Feet', 'Check Objects Below Feet'):
        ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, gn); out = []
        for n in ed.list_all_nodes():
            row = [n.get_name()]
            for a in ('node_title', 'title', 'get_node_title', 'member_name', 'variable_name'):
                try:
                    v = getattr(n, a); row.append(a + '=' + str(v() if callable(v) else v)[:80])
                except Exception: pass
            out.append(row)
        R[gn] = out
    R['dir'] = [d for d in dir(ed.list_all_nodes()[0]) if not d.startswith('_')][:60]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\grind_dump.json', 'w'), indent=1); print('GRIND_DUMP', R.get('error', '')[-200:])
