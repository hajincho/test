"""Lyra 에디터(`py <파일> [이벤트이름]`): ThirdPersonCharacter_BP 의 커스텀 이벤트(기본 FurinaRifleShot)에서 시작하는 실행 체인(최대 120노드)을 노드 이름/클래스/연결로 덤프. 핀 값이 필요하면 `pins` 인자 추가
 -> Data/lyra_graph_dump_<이벤트>.json"""
import unreal, json, sys, traceback
EVN = [a for a in sys.argv[1:] if not a.endswith('.py') and a != 'pins']
EVN = EVN[-1] if EVN else 'FurinaRifleShot'
PINS = 'pins' in sys.argv
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data' + '\\lyra_graph_dump_%s.json' % EVN
R = {'ev_name': EVN}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = ed.list_all_nodes(); R['n'] = len(nodes)
    ev = ed.find_event_node(EVN); R['ev'] = ev.get_name() if ev else None
    chain = []; seen = set(); cur = [ev] if ev else []
    for _ in range(120):
        if not cur: break
        nxt = []
        for n in cur:
            if n.get_name() in seen: continue
            seen.add(n.get_name()); row = {'node': n.get_name(), 'cls': n.get_class().get_name()}
            for pn in ('then', 'else', 'Completed', 'Loop Body', 'Success', 'Failure'):
                try:
                    p = n.find_output_pin(pn)
                    if p and p.is_valid():
                        cs = p.list_connected_pins(); row[pn] = [c.get_owning_node().get_name() for c in cs]; nxt += [c.get_owning_node() for c in cs]
                except Exception: pass
            chain.append(row)
        cur = nxt
    R['chain'] = chain
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_GRAPH_DUMP', EVN, R.get('n'), R.get('error', '')[-200:])

for _n in ('bp', 'ed', 'allnodes', 'nodes', 'ev', 'chain', 'cur', 'nxt', 'n', 'p', 'pins', 'queue', 'row'):   # 블루프린트/노드 래퍼를 전역에 남기면 다음 GC 에서 에디터가 죽는다
    globals().pop(_n, None)
import gc; gc.collect()
