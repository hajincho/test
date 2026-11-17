"""Lyra 에디터(`py <파일> keep`): 함수 오버라이드/그래프 API 도움말 -> Data/lyra_api_doc.json"""
import unreal, json, sys
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_api_doc.json'
R = {}
for cls, names in ((unreal.BlueprintEditorLibrary, ('add_function_override', 'add_event_override', 'list_functions', 'find_graph', 'list_graphs')),
                   (unreal.BlueprintGraphEditor, ('add_return_node', 'add_call_function_node', 'create_and_edit_function_graph', 'add_graph_input_parameter', 'add_graph_output_parameter', 'find_event_node', 'add_branch_node', 'get_graph'))):
    for n in names:
        try: R[cls.__name__ + '.' + n] = (getattr(cls, n).__doc__ or '')[:600]
        except Exception as e: R[cls.__name__ + '.' + n] = 'ERR ' + str(e)[:60]
try:
    gm = unreal.load_asset('/Game/B_LyraGameMode')
    R['gm_functions'] = [str(f)[:160] for f in unreal.BlueprintEditorLibrary.list_functions(gm)][:60] if hasattr(unreal.BlueprintEditorLibrary, 'list_functions') else None
except Exception as e: R['gm_functions'] = 'ERR ' + str(e)[:100]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('LYRA_API_DOC')
