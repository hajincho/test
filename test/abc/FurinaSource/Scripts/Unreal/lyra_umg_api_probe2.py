import unreal, json
R = {}
f = unreal.WidgetBlueprintFactory()
R['factory'] = [m for m in dir(f) if not m.startswith('_')]
for pn in ('root_widget_class', 'parent_class', 'blueprint_type'):
    try: R[pn] = str(f.get_editor_property(pn))
    except Exception as e: R[pn] = 'ERR ' + str(e)[:100]
wt = unreal.WidgetTree()
for pn in ('root_widget', 'RootWidget'):
    try: wt.set_editor_property(pn, unreal.CanvasPanel()); R['set_' + pn] = 'ok'
    except Exception as e: R['set_' + pn] = 'ERR ' + str(e)[:120]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_umg_api_probe2.json', 'w'), indent=1); print('UMG_API2_OK')
