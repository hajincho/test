"""헤드리스: ThirdPersonCharacter_BP 이벤트 그래프에서 타이머 관련 노드(SetTimer/ClearTimer/Pause/K2_*Timer*)와 FMG_*/FPA_* 노드의 핀 연결을 덤프 -> Data/lyra_bp_timer_dump.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
R = {'nodes': {}}
def run():
    bp = unreal.load_asset(PAWN)
    for gname in ('EventGraph',):
        ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, gname)
        for n in ed.list_all_nodes():
            nm = n.get_name(); title = ''
            try: title = str(n.get_node_title())
            except Exception: pass
            if not (nm.startswith('FMG_') or nm.startswith('FPA_') or 'Timer' in title or 'Timer' in nm or 'FurinaMagUpdate' in title):
                continue
            pins = []
            for p in n.list_all_pins() if hasattr(n, 'list_all_pins') else []:
                try:
                    pins.append([str(p.get_pin_name()), str(p.get_pin_value()) if hasattr(p, 'get_pin_value') else '', [q.get_owning_node().get_name() + '.' + str(q.get_pin_name()) for q in p.list_connected_pins()]])
                except Exception as e: pins.append(['err', str(e)[:60]])
            R['nodes'][nm] = {'title': title, 'pins': pins}
        del ed
    del bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-1200:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_bp_timer_dump.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('LYRA_BP_TIMER_DUMP', len(R['nodes']), R.get('error', ''))
import gc; gc.collect()
