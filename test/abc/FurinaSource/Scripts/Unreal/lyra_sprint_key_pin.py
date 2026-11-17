"""Lyra 에디터: 푸리나 폰 K2Node_FPT_Sprint(IsInputKeyDown)의 Key 핀 전체 값과 FPT_FreeSpd 핀 -> Data/lyra_sprint_key_pin_backup.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_sprint_key_pin_backup.json'
R = {}
try:
    bp = unreal.load_asset('/Game/Furina/Backups/ThirdPersonCharacter_BP_PreLyraHero')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    for nm in ('K2Node_FPT_Sprint', 'K2Node_FPT_FreeSpd', 'K2Node_FPT_PCT'):
        n = nodes.get(nm); R[nm] = [[str(p.get_pin_name()), str(p.get_pin_value()), [c.get_owning_node().get_name() for c in p.list_connected_pins()]] for p in n.list_all_pins()] if n else 'missing'
    R['fsprint_event'] = [[str(p.get_pin_name()), str(p.get_pin_value())[:80], [c.get_owning_node().get_name() for c in p.list_connected_pins()]] for p in nodes['K2Node_EnhancedInputAction_FSprint'].list_all_pins()]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_SPRINT_KEY', R.get('error', 'ok')[-200:])
