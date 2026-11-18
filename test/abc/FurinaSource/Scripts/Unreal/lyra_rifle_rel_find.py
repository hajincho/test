"""Lyra 에디터: 폰 BP 에서 FurinaRifle 의 손목 기준 상대 위치(-1.95, -10.60, -6.35 / 회전 -50.5)를 런타임에 다시 설정하는 노드를 찾는다
(BP 템플릿만 바꿨는데 PIE 에서 옛 값이 나와서) + 변수 기본값 중 그 값을 가진 것 -> Data/lyra_rifle_rel_find.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_rifle_rel_find.json'
R = {'hits': [], 'graphs': []}
KEYS = ('10.60', '10.6007', '-50.50', '50.506', '6.354', '1.9545')
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    names = []
    for g in ('EventGraph', 'ConstructionScript', 'UserConstructionScript'):
        names.append(g)
    try: names += [str(x) for x in unreal.BlueprintGraphEditor.list_graph_names(bp)]
    except Exception as e: R['list_err'] = str(e)[:100]
    seen = set()
    for gname in names:
        if gname in seen: continue
        seen.add(gname)
        try: ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, gname)
        except Exception: continue
        if ed is None: continue
        R['graphs'].append(gname)
        for n in ed.list_all_nodes():
            try: t = str(n.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace('\n', ' ')
            except Exception: t = ''
            pins = []
            try: pins = [[str(p.get_pin_name()), str(p.get_pin_value())] for p in n.list_all_pins()]
            except Exception: pass
            blob = t + ' ' + ' '.join(v for _, v in pins)
            if any(k in blob for k in KEYS) or ('Relative' in t and 'Set' in t) or ('Attach' in t):
                R['hits'].append({'graph': gname, 'node': n.get_name(), 'title': t[:80], 'pins': [pp for pp in pins if pp[1]][:12]})
    # 변수 기본값
    cdo = unreal.get_default_object(bp.generated_class())
    for prop in ('RifleRelLoc', 'RifleRelRot', 'GunInRW', 'RifleOffset'):
        try: R['cdo_' + prop] = str(cdo.get_editor_property(prop))
        except Exception: pass
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_RIFLE_REL_FIND', len(R['hits']), R.get('error', '')[-200:])
