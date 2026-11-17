"""Lyra 에디터: B_Hero_Explorer / B_Hero_ShooterMannequin / B_Hero_Default 가 Unarmed 애님 레이어를 어떻게 거는지(노드/함수) 조사 -> Data/lyra_unarmed_probe.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_unarmed_probe.json'
R = {}
def dump(path):
    out = {}
    bp = unreal.load_asset(path)
    try: out['graphs'] = [str(g) for g in unreal.BlueprintGraphEditor.list_graph_names(bp)]
    except Exception as e: out['graphs_err'] = str(e)[:80]
    for gname in ('EventGraph',):
        try:
            ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, gname); rows = []
            for n in ed.list_all_nodes():
                nm = n.get_name()
                try: t = str(n.get_node_title(unreal.NodeTitleType.LIST_VIEW)) if hasattr(n, 'get_node_title') else ''
                except Exception: t = ''
                rows.append(nm + ' | ' + t)
            out[gname] = rows[:60]
        except Exception as e: out[gname + '_err'] = str(e)[:100]
    return out
try:
    for p in ('/ShooterExplorer/Blueprint/B_Hero_Explorer', '/ShooterCore/Game/B_Hero_ShooterMannequin', '/Game/Characters/Heroes/B_Hero_Default'):
        try: R[p] = dump(p)
        except Exception as e: R[p] = 'err ' + str(e)[:150]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_UNARMED_PROBE', R.get('error', 'ok')[-200:])
