"""Editor: searches every graph of the bundle's Grind_Rail_Component_BP and Platformer_Component_BP for nodes whose title / pin names mention the keywords (default UsingZipline, Zipline Up, ZiplineAnimation,
Vertical) and lists graph, node name, title and connected node names -> Data/zip_graph_search.json. usage: py ue_zip_graph_search.py [keyword ...]"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
KEYS = [k.lower() for k in sys.argv[1:]] or ['usingzipline', 'zipline up', 'ziplineanimation', 'vertical', 'upsidedown', 'jumptozipline']
PATHS = ['/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP', '/Game/3DPlatformerGameBundle/Blueprints/Components/Platformer_Component_BP']
def main():
    R = {}
    for p in PATHS:
        a = unreal.load_asset(p); hits = []
        for g in [str(x) for x in unreal.BlueprintEditorLibrary.list_graph_names(a)]:
            try: ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(a, g)
            except Exception: continue
            if not ed: continue
            for n in ed.list_all_nodes():
                title = str(n.get_node_title()); text = (title + ' ' + n.get_name()).lower()
                pins = [str(x.get_pin_name()) for x in n.list_all_pins()]
                if any(k in text or any(k in q.lower() for q in pins) for k in KEYS):
                    exec_in = []
                    for x in n.list_all_pins():
                        if str(x.get_pin_name()) == 'execute': exec_in = [c.get_owning_node().get_name() + ':' + str(c.get_pin_name()) for c in x.list_connected_pins()]
                    hits.append(dict(graph=g, node=n.get_name(), title=title.replace('\n', ' '), exec_from=exec_in, pins=[q for q in pins if any(k in q.lower() for k in KEYS)]))
            del ed
        R[p] = hits[:150]
    json.dump(R, open(D + r'\zip_graph_search.json', 'w'), indent=1, ensure_ascii=False); print('ZIP_GRAPH', {k: len(v) for k, v in R.items()})
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(D + r'\zip_graph_search.json', 'w'))
