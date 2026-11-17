"""Lyra 에디터: 푸리나 폰 EventGraph 의 탄창 관련 노드(FMG_*, M4Mag*, 'Mag' 포함) 핀 값/연결 -> Data/lyra_mag_nodes.json
+ FurinaMag 컴포넌트 상대 위치/회전/부착 소켓, FurinaRifle 의 소켓 목록"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_mag_nodes.json'
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); rows = []
    for n in ed.list_all_nodes():
        nm = n.get_name()
        if nm.startswith(('FMG_', 'K2Node_FMG')) or 'MagDrop' in nm or 'MagHand' in nm:
            row = {'node': nm, 'cls': n.get_class().get_name()}
            try: row['title'] = str(n.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace('\n', ' ')[:70]
            except Exception: pass
            try: row['pins'] = [[str(p.get_pin_name()), str(p.get_pin_value())[:70], [c.get_owning_node().get_name() for c in p.list_connected_pins()][:3]] for p in n.list_all_pins() if str(p.get_pin_value()) or p.list_connected_pins()][:10]
            except Exception as e: row['err'] = str(e)[:60]
            rows.append(row)
    R['nodes'] = rows; R['count'] = len(rows)
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary; comps = {}
    for h in S.k2_gather_subobject_data_for_blueprint(bp):
        o = L.get_associated_object(L.get_data(h)); nm = str(L.get_variable_name(L.get_data(h)))
        if nm in ('FurinaMag', 'FurinaRifle', 'FurinaMesh') and o is not None:
            t = {'class': o.get_class().get_name()}
            for a in ('relative_location', 'relative_rotation', 'relative_scale3d', 'attach_socket_name'):
                try: t[a] = str(o.get_editor_property(a))
                except Exception: pass
            comps[nm] = t
    R['comps'] = comps
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_MAG_NODES', R.get('count'), R.get('error', '')[-200:])
