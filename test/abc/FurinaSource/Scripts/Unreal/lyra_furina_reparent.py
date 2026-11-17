"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 푸리나 폰 BP 의 부모를 ACharacter -> LyraCharacter 로 바꿔 체력/팀/ASC(PlayerState)/사망을 Lyra 방식으로 쓰게 한다.
 0) 백업: /Game/Furina/Backups/ThirdPersonCharacter_BP_PreLyraHero 로 복제(이미 있으면 건너뜀)
 1) reparent_blueprint -> LyraCharacter
 2) Lyra 가 만든 LyraCameraComponent 는 끈다(푸리나 자체 카메라를 쓰므로 뷰 타깃 충돌 방지)
 3) 컴파일, 오류 노드 목록, 컴포넌트 목록, 저장   -> Data/lyra_furina_reparent.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_furina_reparent.json'
R = {}
P = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
BAK = '/Game/Furina/Backups/ThirdPersonCharacter_BP_PreLyraHero'
EAL = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary
def comps(bp):
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary; out = {}
    for h in S.k2_gather_subobject_data_for_blueprint(bp):
        d = L.get_data(h); o = L.get_associated_object(d); out[str(L.get_variable_name(d))] = (o.get_class().get_name() if o else None, o)
    return out
try:
    if not EAL.does_asset_exist(BAK):
        EAL.make_directory('/Game/Furina/Backups'); R['backup'] = bool(EAL.duplicate_asset(P, BAK))
    else: R['backup'] = 'exists'
    bp = unreal.load_asset(P); R['parent_before'] = str(BEL.get_blueprint_parent_class(bp))
    R['before_components'] = {k: v[0] for k, v in comps(bp).items()}
    lc = unreal.find_object(None, '/Script/LyraGame.LyraCharacter'); assert lc, 'LyraCharacter class'
    if 'LyraCharacter' not in R['parent_before']:
        R['reparent'] = BEL.reparent_blueprint(bp, lc)
    R['parent_after'] = str(BEL.get_blueprint_parent_class(bp))
    cs = comps(bp); R['after_components'] = {k: v[0] for k, v in cs.items()}
    cam = cs.get('CameraComponent')
    if cam and cam[1] is not None and cam[0] == 'LyraCameraComponent':
        try: cam[1].set_editor_property('auto_activate', False); R['lyra_camera_off'] = True
        except Exception as e: R['lyra_camera_off'] = 'ERR ' + str(e)[:100]
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    R['error_nodes'] = [n.get_name() + ' | ' + str(n.get_node_title()).replace('\n', ' ') for n in ed.list_nodes_with_errors()][:40]
    R['saved'] = EAL.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FURINA_REPARENT', R.get('parent_after'), R.get('status'), R.get('saved'), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
