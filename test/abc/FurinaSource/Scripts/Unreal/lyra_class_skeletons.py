"""에디터(편집 전용, PIE 아님, 2026-11-22): 병과 캐릭터마다 자기 뼈대 -> Saved/ClassSkeletons.json("done": true)
 문제: 7종을 모두 SK_Furina_Skeleton 하나에 묶고 몸 뼈 이동 리타깃을 'Skeleton' 으로 뒀는데, 이 모드는 메시가 아니라 뼈대 에셋(푸리나)의 뼈 길이를 씀.
   -> 클레(125cm)·케이아(184cm) 등의 다리가 푸리나 길이로 늘어나거나 줄고, 엉덩이 높이(AnimationScaled)만 캐릭터 비율이라 무릎이 굽고 발이 바닥에 묻힘.
 수정: FBX/Classes/<key>_cm.fbx 를 뼈대 지정 없이 /Game/Furina/Classes/<Key>/SKM_<Key> 로 가져와 자기 뼈대(SKM_<Key>_Skeleton, 기준 자세 = 그 캐릭터)를 만들고
   - 이 뼈대에 SK_Furina_Skeleton 을 호환 뼈대로 추가(푸리나 애니메이션·ABP_Furina·컨트롤 릭을 그대로 씀, 뼈 이름으로 연결)
   - 이 뼈대의 몸·손가락 뼈 이동 리타깃 = Skeleton(= 이 캐릭터 길이), Hips = AnimationScaled
   - 재질은 예전 SK_Class_<Key> 슬롯 그대로, 캐릭터 BP 의 LOOK_Set_<Key>(외형 이벤트)·FurinaMesh 기본 메시를 새 메시로, 예전 SK_Class_<Key> 삭제.
 SK_Furina_Skeleton 의 몸 뼈 모드는 Animation 으로 되돌림(푸리나 본인은 원래 설정)."""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib, lyra_fpvm_optics; importlib.reload(lyra_fpvm_optics)
from lyra_fpvm_optics import PAWN, Graph, literal
ROOT = Path(unreal.Paths.project_dir()).resolve(); FS = ROOT / 'FurinaSource'; R = {}
ASSETS = unreal.EditorAssetLibrary; TOOLS = unreal.AssetToolsHelpers.get_asset_tools(); BEL = unreal.BlueprintEditorLibrary
BASE = '/Game/Furina/Classes'; FUR = '/Game/Furina/SK_Furina_Skeleton'
CLASSES = [('officer', 'Officer'), ('infantry', 'Infantry'), ('assault', 'Assault'), ('antitank', 'AntiTank'), ('heavy', 'Heavy'), ('sniper', 'Sniper'), ('armor', 'Armor')]
M = unreal.BoneTranslationRetargetingMode


def body_bones():
    d = json.loads((FS / 'Data' / 'class_infantry_build.json').read_text(encoding='utf-8'))
    return {n.replace(' ', '-') for n in d['body_bones']}


def set_modes(skel, body, hips, other):
    skel.modify(); names = [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(unreal.AnimPoseExtensions.get_reference_pose(skel))]
    tree = skel.get_editor_property('bone_tree'); n = 0
    for i, nm in enumerate(names):
        want = hips if nm == 'Hips' else (other if nm in body else None)
        if want is None: continue
        node = tree[i]
        if node.get_editor_property('translation_retargeting_mode') != want: node.set_editor_property('translation_retargeting_mode', want); tree[i] = node; n += 1
    assert ASSETS.save_loaded_asset(skel, False); return n


def import_class(key, Key, body):
    folder = f'{BASE}/{Key}'; old = unreal.load_asset(f'{folder}/SK_Class_{Key}')
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = True; ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    ui.import_materials = False; ui.import_textures = False; ui.import_animations = False; ui.create_physics_asset = False
    ui.skeletal_mesh_import_data.set_editor_property('import_morph_targets', False)
    t = unreal.AssetImportTask(); t.filename = str(FS / 'FBX' / 'Classes' / f'{key}_cm.fbx'); t.destination_path = folder; t.destination_name = f'SKM_{Key}'
    t.automated = True; t.save = False; t.replace_existing = True; t.options = ui; TOOLS.import_asset_tasks([t])
    mesh = unreal.load_asset(f'{folder}/SKM_{Key}'); assert mesh, key
    skel = mesh.get_editor_property('skeleton'); assert skel and skel.get_path_name().split('.')[0] != FUR, skel.get_path_name()
    # 재질: 예전 메시 슬롯 그대로
    src = {str(s.material_slot_name): s.material_interface for s in old.materials} if old else {}
    slots = list(mesh.materials)
    for s in slots:
        mi = src.get(str(s.material_slot_name)) or unreal.load_asset(f'{folder}/Materials/MI_{Key}_{s.material_slot_name}')
        if mi: s.material_interface = mi
    mesh.set_editor_property('materials', slots)
    skel.add_compatible_skeleton(unreal.load_asset(FUR))
    n = set_modes(skel, body, M.ANIMATION_SCALED, M.SKELETON)
    assert ASSETS.save_loaded_asset(mesh, False); assert ASSETS.save_loaded_asset(skel, False)
    return {'mesh': mesh.get_path_name(), 'skeleton': skel.get_name(), 'modes_changed': n, 'compatible': [str(x) for x in skel.get_editor_property('compatible_skeletons')]}


def pawn():
    bp = unreal.load_asset(PAWN); g = Graph(bp, 'LOOK_'); out = {}
    for key, Key in CLASSES:
        literal(g.nodes['LOOK_Set_' + Key], 'NewMesh', unreal.load_asset(f'{BASE}/{Key}/SKM_{Key}')); out[Key] = True
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    comp = next(lib.get_object(lib.get_data(h)) for h in sub.k2_gather_subobject_data_for_blueprint(bp) if str(lib.get_variable_name(lib.get_data(h))) == 'FurinaMesh')
    comp.set_editor_property('skeletal_mesh_asset', unreal.load_asset(f'{BASE}/Infantry/SKM_Infantry'))
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    assert ASSETS.save_loaded_asset(bp, False); out['status'] = str(st); return out


def cleanup():
    out = {}
    for key, Key in CLASSES:
        p = f'{BASE}/{Key}/SK_Class_{Key}'
        if ASSETS.does_asset_exist(p):
            ar = unreal.AssetRegistryHelpers.get_asset_registry(); o = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
            refs = [str(x) for x in ar.get_referencers(p, o)]
            out[Key] = ASSETS.delete_asset(p) if not refs else ('kept, refs: %s' % refs[:3])
    return out


def run():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    body = body_bones()
    try: R['import'] = {key: import_class(key, Key, body) for key, Key in CLASSES}
    finally: unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
    R['furina_modes_restored'] = set_modes(unreal.load_asset(FUR), body, M.ANIMATION, M.ANIMATION)
    R['pawn'] = pawn()
    R['cleanup'] = cleanup()


if __name__ == '__main__':
  try: run()
  except Exception: R['error'] = traceback.format_exc()[-1800:]
  R['done'] = True; (ROOT / 'Saved' / 'ClassSkeletons.json').write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
  print('CLASS_SKEL', json.dumps(R, default=str, ensure_ascii=False)[:2500])
