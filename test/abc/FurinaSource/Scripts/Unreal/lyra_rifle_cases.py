"""에디터(편집 전용, 2026-11-23): Kar98k·G43 1인칭 탄피 배출(원래 1인칭 역사 무기 화면에서는 탄피를 아예 만들지 않았음: HistoricalView_EjectOnlyM4)
 단계(각 단계 뒤 저장, 다시 돌리면 끝난 단계는 건너뜀):
  mesh   : FBX/FX/SM_FPVM_792Case.fbx(fx_792case.py) -> /Game/Furina/FX/Rifle/SM_FPVM_792Case (MG42 탄 단위 황동·구리 재질, 상자 충돌)
  actor  : BP_FPVM_9mmCase 복제 -> BP_FPVM_792Case (소켓 +X 로 4m/s, 4초 뒤 사라짐)
  socket : VM_CaseFX 소켓(Data/fpvm_rifle_ejection.json: 위치, +X = 배출 방향, +Z = 총구 쪽 = 탄피 입) -> SK_FPVM_Kar98k(_Interior/_ZF39/_ZF41), SK_FPVM_G43(_Interior/_ZF4)
  pawn   : HistoricalView_EjectOnlyM4.then 뒤에 끼움: 키가 g43* 이면 바로, kar98k* 이면 0.5초 뒤(Fire 클립에서 볼트를 끝까지 당기는 0.40~0.52초) 탄피 생성
 -> Saved/RifleCases.json"""
import json, sys, time, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, STRINGS, PAWN, Graph, chain, wire, literal
ROOT = Path(unreal.Paths.project_dir()).resolve(); OUTP = ROOT / 'Saved' / 'RifleCases.json'
R = json.loads(OUTP.read_text(encoding='utf-8')) if OUTP.exists() else {}
ASSETS = unreal.EditorAssetLibrary; SL = unreal.get_default_object(unreal.SystemLibrary); TOK = '%x' % (int(time.time()) % 0xFFFFF)
FOLDER = '/Game/Furina/FX/Rifle'; MESH = FOLDER + '/SM_FPVM_792Case'; ACTOR = FOLDER + '/BP_FPVM_792Case'
SPEED = '400,0,0'; KAR_DELAY = 0.50
VARIANTS = {'kar98k': ['SK_FPVM_Kar98k', 'SK_FPVM_Kar98k_Interior', 'SK_FPVM_Kar98k_ZF39', 'SK_FPVM_Kar98k_ZF41'], 'g43': ['SK_FPVM_G43', 'SK_FPVM_G43_Interior', 'SK_FPVM_G43_ZF4']}
FOLD = {'kar98k': 'KAR98K', 'g43': 'G43'}


def save(a): assert ASSETS.save_loaded_asset(a, False), a.get_path_name()


def step_mesh():
    if not ASSETS.does_asset_exist(MESH):
        s = unreal.FbxImportUI(); s.import_materials = False; s.import_textures = False
        s.static_mesh_import_data.auto_generate_collision = False; s.static_mesh_import_data.combine_meshes = True
        t = unreal.AssetImportTask(); t.filename = str(ROOT / 'FurinaSource/FBX/FX/SM_FPVM_792Case.fbx'); t.destination_path = FOLDER; t.destination_name = 'SM_FPVM_792Case'
        t.options = s; t.automated = True; unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    m = unreal.load_asset(MESH); assert m, MESH
    mats = {'Case': unreal.load_asset('/Game/Furina/MG42/Materials/MI_MG42_CaseBrass'), 'Primer': unreal.load_asset('/Game/Furina/MG42/Materials/MI_MG42_PrimerCopper')}
    slots = []
    for i, sl in enumerate(m.static_materials):
        n = str(sl.material_slot_name); m.set_material(i, mats['Primer'] if 'Primer' in n else mats['Case']); slots.append(n)
    st = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not st.get_simple_collision_count(m): st.add_simple_collisions(m, unreal.ScriptingCollisionShapeType.BOX)
    try: m.set_editor_property('nanite_settings', unreal.MeshNaniteSettings(enabled=False))
    except Exception: pass
    b = m.get_bounds().box_extent; assert 2.5 < b.z < 3.2, b
    save(m); return {'slots': slots, 'half_len_cm': round(b.z, 3)}


def step_actor():
    if not ASSETS.does_asset_exist(ACTOR): assert ASSETS.duplicate_asset('/Game/Furina/FX/Pistol/BP_FPVM_9mmCase', ACTOR)
    bp = unreal.load_asset(ACTOR); sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary; ok = False
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        d = lib.get_data(h)
        if str(lib.get_variable_name(d)) == 'FXMesh':
            c = lib.get_associated_object(d); c.set_static_mesh(unreal.load_asset(MESH)); c.set_editor_property('override_materials', []); ok = True
    assert ok
    g = Graph(bp); literal(g.nodes['TFPCaseDirection'], 'Direction', SPEED)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); assert bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    unreal.get_default_object(bp.generated_class()).set_editor_property('initial_life_span', 4.0)
    save(bp); return {'speed': SPEED}


def put_socket(mesh, loc, rot):
    sock = mesh.find_socket('VM_CaseFX')
    if not sock:
        sock = unreal.SkeletalMeshSocket(outer=mesh); SL.call_method('SetNamePropertyByName', (sock, 'SocketName', 'VM_CaseFX')); mesh.add_socket(sock, False)
    SL.call_method('SetNamePropertyByName', (sock, 'BoneName', 'VM_Gun'))
    SL.call_method('SetVectorPropertyByName', (sock, 'RelativeLocation', loc)); SL.call_method('SetRotatorPropertyByName', (sock, 'RelativeRotation', rot))
    mesh.modify(); save(mesh)


def comp_xf(mesh, socket):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); c = a.get_component_by_class(unreal.SkeletalMeshComponent)
    T = c.get_socket_transform(socket, unreal.RelativeTransformSpace.RTS_COMPONENT); eas.destroy_actor(a); return T


def step_socket():
    ej = json.loads((ROOT / 'FurinaSource' / 'Data' / 'fpvm_rifle_ejection.json').read_text(encoding='utf-8')); out = {}
    for key, names in VARIANTS.items():
        e = ej[key]; base = unreal.load_asset(f'/Game/Furina/FPVM/{FOLD[key]}/{names[0]}'); T = comp_xf(base, 'VM_Gun')
        p = unreal.Vector(*e['ue_cam_cm']); d = unreal.Vector(*e['ue_dir']); f = unreal.Vector(*e['ue_fwd'])
        rot_cs = unreal.MathLibrary.make_rot_from_xz(d, f)
        loc = unreal.MathLibrary.inverse_transform_location(T, p); rot = unreal.MathLibrary.inverse_transform_rotation(T, rot_cs)
        for n in names:
            m = unreal.load_asset(f'/Game/Furina/FPVM/{FOLD[key]}/{n}')
            if not m: out[n] = 'missing'; continue
            put_socket(m, loc, rot); chk = comp_xf(m, 'VM_CaseFX')
            out[n] = {'err_cm': round((chk.translation - p).length(), 3), 'x_dot_dir': round(unreal.MathLibrary.get_forward_vector(chk.rotation.rotator()).dot(d), 3)}
    return out


def step_pawn():
    pawn = unreal.load_asset(PAWN); g = Graph(pawn, 'RifleCase%s_' % TOK)
    if any(n.startswith('RifleCase') and n.endswith('_IsG43') for n in g.nodes): return 'already'
    ev_name = 'FurinaRifleCaseLater'
    gate = g.nodes['HistoricalView_EjectOnlyM4']; then = gate.find_then_pin(); after = [p for p in then.list_connected_pins()]
    assert after, 'no continuation after HistoricalView_EjectOnlyM4'
    R['pawn_after'] = [p.get_owning_node().get_name() + '.' + str(p.get_pin_name()) for p in after]
    key = g.get('FurinaVMLastKey')
    def starts(name, prefix): return g.call(name, STRINGS + 'StartsWith', SourceString=key, InPrefix=prefix).find_result_pin()
    def spawn_chain(tag):
        vm = g.get('FurinaFPVM')
        loc = g.call(tag + 'Loc', ENGINE + 'SceneComponent:GetSocketLocation', target=vm, InSocketName='VM_CaseFX').find_result_pin()
        rot = g.call(tag + 'Rot', ENGINE + 'SceneComponent:GetSocketRotation', target=g.get('FurinaFPVM'), InSocketName='VM_CaseFX').find_result_pin()
        xf = g.call(tag + 'Xf', MATH + 'MakeTransform', Location=loc, Rotation=rot).find_result_pin()
        gs = ENGINE + 'GameplayStatics:'
        sp = g.call(tag + 'Spawn', gs + 'BeginDeferredActorSpawnFromClass', ActorClass=unreal.load_asset(ACTOR).generated_class(), SpawnTransform=xf, CollisionHandlingOverride='AlwaysSpawn')
        fin = g.call(tag + 'Finish', gs + 'FinishSpawningActor', Actor=sp.find_result_pin(), SpawnTransform=xf)
        return sp, fin
    is_g = g.branch('IsG43', starts('KeyG43', 'g43')); is_k = g.branch('IsKar98k', starts('KeyKar98k', 'kar98k'))
    then.break_pin_links()
    try:
        wire(then, is_g.find_execute_pin())
        gs_, gf = spawn_chain('G43'); wire(is_g.find_then_pin(), gs_.find_execute_pin()); wire(gs_.find_then_pin(), gf.find_execute_pin())
        wire(is_g.find_else_pin(), is_k.find_execute_pin())
        timer = g.call('KarTimer', ENGINE + 'KismetSystemLibrary:K2_SetTimer', FunctionName=ev_name, Time=KAR_DELAY, bLooping=False)
        wire(is_k.find_then_pin(), timer.find_execute_pin())
        outs = [gf.find_then_pin(), timer.find_then_pin(), is_k.find_else_pin()]
        for o in outs:
            for p in after: wire(o, p)
    except Exception:
        then.break_pin_links()
        for p in after: wire(then, p)   # 실패하면 원래 연결 복원
        raise
    ev = g.editor.add_custom_event_node(ev_name); ev.rename('RifleCase%s_Event' % TOK)
    ks, kf = spawn_chain('Kar'); wire(ev.find_then_pin(), ks.find_execute_pin()); wire(ks.find_then_pin(), kf.find_execute_pin())
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn); st = pawn.get_editor_property('status'); R['pawn_status'] = str(st)
    assert st != unreal.BlueprintStatus.BS_ERROR, [n.get_name() for n in g.editor.list_nodes_with_errors()] if hasattr(g.editor, 'list_nodes_with_errors') else st
    save(pawn); return 'installed'


try:
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE before editing assets'
    for name, fn in (('mesh', step_mesh), ('actor', step_actor), ('socket', step_socket), ('pawn', step_pawn)):
        if R.get(name + '_done'): continue
        R[name] = fn(); R[name + '_done'] = True; OUTP.write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
    R['done'] = True
except Exception:
    R['error'] = traceback.format_exc()[-1500:]
OUTP.write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8'); print('RIFLE_CASES', json.dumps(R, default=str, ensure_ascii=False)[-1500:])
