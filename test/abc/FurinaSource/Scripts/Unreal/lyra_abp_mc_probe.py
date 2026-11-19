"""Lyra 에디터(`py <파일>`): ABP_Furina 의 ModifyCurve 노드들의 핀/속성을 덤프 (PistolOn 곡선을 어떻게 추가할지 조사).  -> Data/lyra_abp_mc_probe.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_abp_mc_probe.json'
R = {}
def run():
    abp = unreal.load_asset('/Game/Furina/ABP_Furina'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(abp, 'AnimGraph')
    for n in ed.list_all_nodes():
        nm = n.get_name()
        if 'ModifyCurve' not in nm and 'ControlRig' not in nm: continue
        row = {'class': str(n.get_class().get_name()), 'pins': []}
        for p in n.list_all_pins():
            row['pins'].append([str(p.get_pin_name()), str(p.get_pin_value())[:60], [c.get_owning_node().get_name() + '.' + str(c.get_pin_name()) for c in p.list_connected_pins()][:3]])
        try:
            nd = n.get_editor_property('node'); row['node'] = str(nd)[:400]
            row['node_props'] = [str(x) for x in dir(nd) if not x.startswith('_')][:40]
        except Exception as e: row['node_err'] = str(e)[:120]
        R[nm] = row
    del ed, abp
try: run()
except Exception: R['error'] = traceback.format_exc()[-800:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_ABP_MC_PROBE', list(R)[:8], R.get('error', ''))
import gc; gc.collect()
