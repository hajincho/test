import unreal, json
R = {}
R['classes'] = [n for n in dir(unreal) if 'Widget' in n and ('Library' in n or 'Subsystem' in n or 'Editor' in n or 'Tree' in n)]
for cn in R['classes'] + ['WidgetBlueprint', 'BlueprintEditorLibrary', 'EditorUtilitySubsystem']:
    c = getattr(unreal, cn, None)
    if c: R[cn] = [m for m in dir(c) if not m.startswith('_') and ('widget' in m.lower() or 'tree' in m.lower() or 'add' in m.lower())][:60]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_umg_api_probe.json', 'w'), indent=1); print('UMG_API_OK')
