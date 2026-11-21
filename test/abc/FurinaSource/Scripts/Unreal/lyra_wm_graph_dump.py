import unreal, json
R = {}
bp = unreal.load_asset('/Game/Furina/UI/WBP_FurinaWeaponMenu')
R['graphs'] = [str(g) for g in unreal.BlueprintEditorLibrary.list_graph_names(bp)]
for gname in ('OnKeyDown', 'OnMouseButtonDown', 'BP_GetDesiredFocusTarget'):
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, gname)
    if not ed: R[gname] = None; continue
    out = {}
    for n in ed.list_all_nodes():
        out[n.get_name()] = [str(n.get_class().get_name()), str(n.get_node_title()).replace('\n', ' ')[:60], [[str(p.get_pin_name()), str(p.get_pin_value())[:40], [c.get_owning_node().get_name() for c in p.list_connected_pins()]] for p in n.list_all_pins() if p.list_connected_pins() or str(p.get_pin_value()) not in ('', 'None')]]
    R[gname] = out
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_wm_graph_dump.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('WM_DUMP_OK')
