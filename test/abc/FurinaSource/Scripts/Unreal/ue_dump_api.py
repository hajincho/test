import unreal, json
R = {'ed': [n for n in dir(unreal.BlueprintGraphEditor) if not n.startswith('_')], 'node': [n for n in dir(unreal.BlueprintGraphNode) if not n.startswith('_')] if hasattr(unreal, 'BlueprintGraphNode') else None}
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\dump_api.json', 'w'), indent=1); print('DUMP_API')
