import unreal, json
R = {}
for n in ('add_component_bound_event_node', 'create_node_from_name', 'list_available_nodes', 'add_custom_event_node', 'add_call_function_node'):
    R[n] = getattr(unreal.BlueprintGraphEditor, n).__doc__
w = unreal.Button()
R['btn_props'] = [p for p in ('is_variable', 'b_is_variable') if True]
for pn in ('is_variable',):
    try: w.set_editor_property(pn, True); R['set_' + pn] = 'ok'
    except Exception as e: R['set_' + pn] = str(e)[:150]
pass
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_umg_api_probe3.json', 'w'), indent=1); print('P3OK')
