"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 봇(B_Hero_ShooterMannequin) BeginPlay 에서 메시에 ABP_UnarmedAnimLayers 를 링크한다.
이유: Lyra 마네킹의 이동/대기 모션은 무기 인스턴스(B_WeaponInstance_Base)가 장착될 때 링크하는 애님 레이어에서 온다. 무기를 뺐더니 레이어가 없어 봇이 기본 포즈(A포즈)로 미끄러짐.
기존 Lyra 애니메이션(Unarmed 레이어) 재사용.   -> Data/lyra_bots_unarmed_layers.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_bots_unarmed_layers.json'
R = {}
P = '/ShooterCore/Game/B_Hero_ShooterMannequin'
LAYER = '/Game/Characters/Heroes/Mannequin/Animations/Locomotion/Unarmed/ABP_UnarmedAnimLayers.ABP_UnarmedAnimLayers_C'
PL = unreal.BlueprintGraphPinLibrary
try:
    bp = unreal.load_asset(P)
    unreal.EditorAssetLibrary.save_loaded_asset  # noqa
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    names = {n.get_name(): n for n in ed.list_all_nodes()}
    R['exists'] = 'BU_LinkUnarmed' in names
    if not R['exists']:
        ev = ed.find_event_node('ReceiveBeginPlay'); R['had_begin_play'] = bool(ev)
        if not ev: raise RuntimeError('no ReceiveBeginPlay')
        gm = None
        for how in ('member', 'name'):
            try:
                gm = ed.add_get_member_variable_node('Mesh') if how == 'member' else ed.create_node_from_name('Get Mesh')
            except Exception as e: R['gm_err_' + how] = str(e)[:150]
            if gm: R['gm_how'] = how; break
        if not gm: raise RuntimeError('no GetMesh node')
        gm.rename('BU_GetMesh')
        ln = ed.add_call_function_node('/Script/Engine.SkeletalMeshComponent:LinkAnimClassLayers'); ln.rename('BU_LinkUnarmed')
        ok = []
        ok.append(PL.try_create_connection((gm.find_output_pin('Mesh') if gm.find_output_pin('Mesh').is_valid() else gm.find_result_pin()), ln.find_self_pin()))
        p = ln.find_input_pin('InClass'); R['inclass_pin_valid'] = p.is_valid(); ok.append(p.set_pin_value(LAYER))
        old = list(ev.find_then_pin().list_connected_pins())
        ok.append(PL.try_create_connection(ev.find_then_pin(), ln.find_execute_pin()))
        for q in old: ok.append(PL.try_create_connection(ln.find_then_pin(), q))
        R['conn'] = [bool(x) for x in ok]; R['old_targets'] = [q.get_owning_node().get_name() for q in old]
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['error_nodes'] = [n.get_name() for n in ed.list_nodes_with_errors()][:10]
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_BOT_LAYERS', R.get('status'), R.get('saved'), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
