"""LYRA 에디터(헤드리스): 푸리나 폰 BP 이벤트 그래프에서 입력 관련 노드(Mapping/Possess/Controller/Input/EnhancedInput)와 연결을 덤프 -> FurinaSource/Data/lyra_input_dump.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_input_dump.json'
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    R['graphs'] = [str(g) for g in unreal.BlueprintEditorLibrary.list_graph_names(bp)]
    KEYS = ('mapping', 'possess', 'controller', 'enhancedinput', 'localplayer', 'local player', 'subsystem', 'beginplay', 'begin play', 'input')
    out = {}
    for gname in ('EventGraph',):
        ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, gname)
        for n in ed.list_all_nodes():
            t = str(n.get_node_title()).replace('\n', ' ')
            if any(k in t.lower() for k in KEYS):
                pins = []
                for p in n.list_all_pins():
                    pins.append([str(p.get_pin_name()), p.get_pin_value(), [c.get_owning_node().get_name() + '.' + str(c.get_pin_name()) for c in p.list_connected_pins()]])
                out[n.get_name()] = {'title': t, 'pins': pins}
    R['nodes'] = out
    R['ctor_flags'] = {}
    d = unreal.get_default_object(bp.generated_class())
    for p in ('auto_possess_player', 'auto_possess_ai', 'auto_receive_input'):
        try: R['ctor_flags'][p] = str(d.get_editor_property(p))
        except Exception as e: R['ctor_flags'][p] = 'ERR ' + str(e)[:60]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_INPUT_DUMP', R.get('error', 'ok')[-200:])
unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
