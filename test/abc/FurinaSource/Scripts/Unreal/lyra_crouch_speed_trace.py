"""Lyra 에디터: 푸리나 폰(현재)과 Lyra 이전 백업 EventGraph 에서 MaxWalkSpeedCrouched / MaxWalkSpeed 를 설정하는 노드와 그 입력 연결 -> Data/lyra_crouch_speed_trace.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_crouch_speed_trace.json'
R = {}
def info(n):
    row = {'node': n.get_name(), 'cls': n.get_class().get_name()}
    try: row['title'] = str(n.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace('\n', ' ')
    except Exception: pass
    return row
try:
    for k, p in {'now': '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP', 'backup': '/Game/Furina/Backups/ThirdPersonCharacter_BP_PreLyraHero'}.items():
        bp = unreal.load_asset(p); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); rows = []
        for n in ed.list_all_nodes():
            hit = False
            for pn in ('MaxWalkSpeedCrouched', 'MaxWalkSpeed', 'Max Walk Speed Crouched', 'Max Walk Speed'):
                try:
                    pin = n.find_input_pin(pn)
                    if pin and pin.is_valid(): hit = pn; break
                except Exception: pass
            if hit or 'Spd' in n.get_name() or 'Crouch' in n.get_name():
                r = info(n); r['pin'] = hit
                if hit:
                    pin = n.find_input_pin(hit); r['from'] = [(c.get_owning_node().get_name()) for c in pin.list_connected_pins()]
                    r['exec_from'] = [c.get_owning_node().get_name() for c in n.find_execute_pin().list_connected_pins()] if n.find_execute_pin().is_valid() else None
                rows.append(r)
        R[k] = rows
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CROUCH_TRACE', {k: len(v) for k, v in R.items() if isinstance(v, list)}, R.get('error', '')[-200:])
