"""Lyra 에디터: 푸리나 폰 EventGraph 에서 MappingContext 핀이 있는 노드(AddMappingContext)와 그 IMC 값, 실행 핀 연결(이벤트)을 조사.
+ LyraHeroComponent 의 DefaultInputMappings 구조체 접근 가능 여부 -> Data/lyra_find_imc.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_find_imc.json'
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); rows = []
    for n in ed.list_all_nodes():
        try:
            pin = n.find_input_pin('MappingContext')
            if pin.is_valid():
                row = {'node': n.get_name(), 'imc': str(pin.get_pin_value()) if hasattr(pin, 'get_pin_value') else '?'}
                try: row['prio'] = str(n.find_input_pin('Priority').get_pin_value())
                except Exception: pass
                ex = n.find_execute_pin()
                row['exec_from'] = [p.get_owning_node().get_name() for p in ex.list_connected_pins()] if ex.is_valid() else None
                rows.append(row)
        except Exception: pass
    R['nodes'] = rows
    # 구조체
    try:
        s = unreal.InputMappingContextAndPriority(); R['struct'] = [n for n in dir(s) if not n.startswith('_')][:20]
    except Exception as e: R['struct_err'] = str(e)[:150]
    try:
        s = unreal.InputMappingContextAndPriority; R['struct_cls'] = str(s)
    except Exception as e: R['struct_cls_err'] = str(e)[:150]
    cdo = unreal.get_default_object(unreal.LyraHeroComponent)
    try: R['default_input_mappings'] = str(cdo.get_editor_property('default_input_mappings'))[:400]
    except Exception as e: R['dim_err'] = str(e)[:150]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIND_IMC', R.get('error', 'ok')[-200:])
