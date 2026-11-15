"""Editor: scans every graph of ThirdPersonCharacter_BP for nodes / pins that set or mention the skeletal mesh (pin values containing SK_Furina, titles with Skeletal Mesh / Skinned Asset) and the
SCS component list with their skinned assets -> Data/mesh_setter.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
def main():
    bp = unreal.load_asset(CH); R = {'hits': [], 'graphs': []}
    for g in [str(x) for x in unreal.BlueprintEditorLibrary.list_graph_names(bp)]:
        R['graphs'].append(g)
        try: ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, g)
        except Exception: continue
        if not ed: continue
        for n in ed.list_all_nodes():
            title = str(n.get_node_title()).replace('\n', ' ')
            hit = any(k in title.lower() for k in ('skeletal mesh', 'skinned', 'set mesh', '스켈레탈', '메시 설정'))
            vals = []
            for p in n.list_all_pins():
                v = p.get_pin_value()
                if v and ('SK_Furina' in v or 'SK_Saori' in v or 'Manny' in v): vals.append([str(p.get_pin_name()), v[:120]])
            if hit or vals: R['hits'].append(dict(graph=g, node=n.get_name(), title=title, vals=vals))
        del ed
    json.dump(R, open(D + r'\mesh_setter.json', 'w'), indent=1, ensure_ascii=False); print('MESH_SETTER', len(R['hits']))
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(D + r'\mesh_setter.json', 'w'))
