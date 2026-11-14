"""Probe: can Python list K2 nodes of the character EventGraph and reach their pins?"""
import unreal, json
def main():
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    R['graph'] = str(g)
    try:
        nodes = g.get_editor_property('nodes')
        R['n_nodes'] = len(nodes)
        fpv = [n for n in nodes if 'FPV_' in n.get_name()]
        R['fpv'] = [n.get_name() for n in fpv][:60]
        if fpv:
            n0 = [n for n in fpv if n.get_name().endswith('AirFast')][0]
            R['node_api'] = [m for m in dir(n0) if 'pin' in m.lower()]
        del nodes, fpv
    except Exception as e:
        R['err'] = repr(e)[:300]
    del g, bp
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\k2_probe.json', 'w'), indent=1)
    print('K2_PROBE_DONE')
main()
del main
