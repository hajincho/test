"""에디터(편집 전용, PIE 아님, 2026-11-22): 병과 캐릭터별 1인칭 팔 -> Saved/ClassFPArms.json("done": true)
 1인칭 무기 메시(FurinaFPVM)는 무기와 푸리나 팔이 한 메시. 팔을 캐릭터별로 바꾸려고:
 1) FBX/Classes/FPArms_<key>.fbx(Blender build_class_fp_arms.py: 캐릭터 팔·손을 1인칭 팔 뼈대 길이에 맞춤) -> /Game/Furina/Classes/<Key>/SK_FPArms_<Key>
    (스켈레톤 하나 공유: 처음 것 SK_FPArms_Skeleton), 재질 = 캐릭터 몸과 같은 MI_<Key>_MatNN
 2) 캐릭터 BP 에 컴포넌트 FurinaFPArmsChar(FurinaFPVM 의 자식, 주인만 보임, 그림자 없음) 추가
 3) FurinaLook<Key>: 팔 메시 교체 + SetLeaderPoseComponent(FurinaFPVM) -> 무기 메시의 팔 뼈를 그대로 따라감(뼈 이름 같음)
    FurinaLookFurina: 팔 메시 비움
 4) 시점 갱신(FurinaViewUpdate, 0.05초)마다: 외형이 푸리나가 아니면 무기 메시의 푸리나 팔 슬롯(Furina_SkinHair, Furina_Outfit)을 가림 재질로,
    푸리나면 원래대로. 팔 컴포넌트 보이기 = FurinaFPVM 보임 AND 외형 != 푸리나. (무기를 바꾸면 슬롯이 원래대로 돌아가서 매번 다시 씀)"""
import json, sys, time, traceback, uuid
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib, lyra_fpvm_optics; importlib.reload(lyra_fpvm_optics)
from lyra_fpvm_optics import ENGINE, MATH, PAWN, STRINGS, Graph, wire, chain
ROOT = Path(unreal.Paths.project_dir()).resolve(); FS = ROOT / 'FurinaSource'; R = {}
ASSETS = unreal.EditorAssetLibrary; TOOLS = unreal.AssetToolsHelpers.get_asset_tools(); BEL = unreal.BlueprintEditorLibrary
BASE = '/Game/Furina/Classes'; HIDDEN = '/Game/Furina/FX/M_FPVM_Hidden'
CLASSES = [('officer', 'Officer'), ('infantry', 'Infantry'), ('assault', 'Assault'), ('antitank', 'AntiTank'), ('heavy', 'Heavy'), ('sniper', 'Sniper'), ('armor', 'Armor')]
COMP = 'FurinaFPArmsChar'


def import_arms():
    out = {}; skel = None
    for key, Key in CLASSES:
        folder = f'{BASE}/{Key}'
        ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = True; ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
        ui.import_materials = False; ui.import_textures = False; ui.import_animations = False; ui.create_physics_asset = False
        ui.skeletal_mesh_import_data.set_editor_property('import_morph_targets', False)
        if skel: ui.skeleton = skel
        t = unreal.AssetImportTask(); t.filename = str(FS / 'FBX' / 'Classes' / f'FPArms_{key}.fbx'); t.destination_path = folder; t.destination_name = f'SK_FPArms_{Key}'
        t.automated = True; t.save = False; t.replace_existing = True; t.options = ui; TOOLS.import_asset_tasks([t])
        mesh = unreal.load_asset(f'{folder}/SK_FPArms_{Key}'); assert mesh, key
        if skel is None:
            skel = mesh.get_editor_property('skeleton')
            if skel.get_name() != 'SK_FPArms_Skeleton':
                assert ASSETS.rename_asset(skel.get_path_name().split('.')[0], f'{BASE}/SK_FPArms_Skeleton'); skel = unreal.load_asset(f'{BASE}/SK_FPArms_Skeleton')
        slots = list(mesh.materials); miss = []
        for s in slots:
            mi = unreal.load_asset(f'{folder}/Materials/MI_{Key}_{s.material_slot_name}')
            if mi: s.material_interface = mi
            else: miss.append(str(s.material_slot_name))
        mesh.set_editor_property('materials', slots); assert ASSETS.save_loaded_asset(mesh, False)
        out[key] = {'slots': len(slots), 'missing': miss, 'skeleton': mesh.get_editor_property('skeleton').get_name()}
    assert ASSETS.save_loaded_asset(skel, False)
    return out


def add_component(bp):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    if COMP not in handles:
        p = unreal.AddNewSubobjectParams(parent_handle=handles['FurinaFPVM'], new_class=unreal.SkeletalMeshComponent, blueprint_context=bp)
        h, fail = sub.add_new_subobject(p); assert not str(fail), str(fail)
        sub.rename_subobject(h, unreal.Text(COMP)); handles = {str(lib.get_variable_name(lib.get_data(x))): x for x in sub.k2_gather_subobject_data_for_blueprint(bp)}
    c = lib.get_object(lib.get_data(handles[COMP]))
    for k, v in (('only_owner_see', True), ('cast_shadow', False), ('visible', False), ('collision_enabled', unreal.CollisionEnabled.NO_COLLISION) if False else ('generate_overlap_events', False),
                 ('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)):
        c.set_editor_property(k, v)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property('use_bounds_from_leader_pose_component', True)   # 자기 휴식 자세 경계(카메라 뒤)로 잘려 안 보였음
    c.set_editor_property('skeletal_mesh_asset', unreal.load_asset(f'{BASE}/Infantry/SK_FPArms_Infantry'))
    return str(c.get_attach_parent().get_name()) if c.get_attach_parent() else 'FurinaFPVM(template)'


def wire_events(bp):
    g = Graph(bp, 'FPAC_'); out = {}
    if 'FPAC_Leader_Infantry' in g.nodes: return 'exists'
    for key, Key in CLASSES + [('furina', 'Furina')]:
        store = g.nodes['LOOK_Store_' + Key]; nxt = list(store.find_then_pin().list_connected_pins())
        setm = g.call('Set_' + Key, ENGINE + 'SkeletalMeshComponent:SetSkeletalMeshAsset', target=g.get(COMP),
                      NewMesh=unreal.load_asset(f'{BASE}/{Key}/SK_FPArms_{Key}') if Key != 'Furina' else '')
        nodes = [setm]
        if Key != 'Furina':
            lead = g.call('Leader_' + Key, ENGINE + 'SkinnedMeshComponent:SetLeaderPoseComponent', target=g.get(COMP), NewLeaderBoneComponent=g.get('FurinaFPVM'))
            nodes.append(lead)
        store.find_then_pin().break_pin_links(); tail = chain(store.find_then_pin(), nodes)
        # 팔 컴포넌트에도 시작 때 라이라가 만든 동적 재질이 남아 다른 캐릭터 팔에 덮어씀 -> 비우기
        num = g.call('Num_' + Key, ENGINE + 'PrimitiveComponent:GetNumMaterials', target=g.get(COMP))
        last = g.call('Last_' + Key, MATH + 'Subtract_IntInt', A=num.find_result_pin(), B=1)
        loop = g.editor.add_macro_node('/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForLoop'); loop.rename('FPAC_Loop_' + Key)
        loop.find_input_pin('FirstIndex').set_pin_value('0'); wire(last.find_result_pin(), loop.find_input_pin('LastIndex'))
        clr = g.call('Clear_' + Key, ENGINE + 'PrimitiveComponent:SetMaterial', target=g.get(COMP))
        wire(loop.find_output_pin('Index'), clr.find_input_pin('ElementIndex')); wire(loop.find_output_pin('LoopBody'), clr.find_execute_pin())
        wire(tail, loop.find_input_pin('execute')); tail = loop.find_output_pin('Completed')
        for p in nxt: wire(tail, p)
    # 시점 갱신마다: 푸리나 팔 슬롯 가림/복원 + 팔 컴포넌트 보이기
    ev = g.editor.find_event_node('FurinaViewUpdate'); old = list(ev.find_then_pin().list_connected_pins())
    notf = g.call('NotFurina', STRINGS + 'NotEqual_StrStr', A=g.get('FurinaLook'), B='furina').find_result_pin()
    br = g.branch('UseCharArms', notf)
    hid = unreal.load_asset(HIDDEN)
    hide = [g.call('Hide_' + s, ENGINE + 'PrimitiveComponent:SetMaterialByName', target=g.get('FurinaFPVM'), MaterialSlotName=s, Material=hid) for s in ('Furina_SkinHair', 'Furina_Outfit')]
    show = [g.call('Show_' + s, ENGINE + 'PrimitiveComponent:SetMaterialByName', target=g.get('FurinaFPVM'), MaterialSlotName=s) for s in ('Furina_SkinHair', 'Furina_Outfit')]
    vis = g.call('VMVisible', ENGINE + 'SceneComponent:IsVisible', target=g.get('FurinaFPVM')).find_result_pin()
    want = g.call('ArmsWant', MATH + 'BooleanAND', A=vis, B=notf).find_result_pin()
    setv = g.call('ArmsVis', ENGINE + 'SceneComponent:SetVisibility', target=g.get(COMP), bNewVisibility=want, bPropagateToChildren='false')
    ev.find_then_pin().break_pin_links(); wire(ev.find_then_pin(), setv.find_execute_pin()); wire(setv.find_then_pin(), br.find_execute_pin())
    t1 = chain(br.find_then_pin(), hide); t2 = chain(br.find_else_pin(), show)
    for p in old: wire(t1, p); wire(t2, p)
    out['view_update_next'] = [p.get_owning_node().get_name() for p in old]
    return out


def run():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try: R['import'] = import_arms()
    finally: unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
    bp = unreal.load_asset(PAWN); R['component'] = add_component(bp)
    BEL.compile_blueprint(bp)
    R['events'] = wire_events(bp)
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    assert ASSETS.save_loaded_asset(bp, False); R['status'] = str(st)


try: run()
except Exception: R['error'] = traceback.format_exc()[-1800:]
R['done'] = True; (ROOT / 'Saved' / 'ClassFPArms.json').write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
print('CLASS_FP_ARMS', json.dumps(R, default=str, ensure_ascii=False)[:2500])
