"""에디터(편집 전용, 2026-11-21): 권총 탄피 배출을 고증대로 (다른 작업이 넣은 PistolCase_ 배출을 보정)
 - 소켓 VM_CaseFX: 실제 배출구 위치(Data/fpvm_pistol_ejection.json), 소켓 +X = 배출 방향
   P38 슬라이드 왼쪽 -> 왼쪽, P08 토글 -> 위(조금 오른쪽·뒤), PP 슬라이드 오른쪽 -> 오른쪽
 - 생성 회전: 카메라 회전(모든 권총이 오른쪽으로 튀었음) -> 소켓 회전
 - 탄피 액터(BP_FPVM_9mmCase, BP_FPVM_32Case) 초기 속도 = 소켓 +X 로 3.5m/s(권총 탄피 배출 속도 대략값)
 -> Saved/PistolCases.json("done": true)"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, PAWN, Graph, wire, literal
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
ASSETS = unreal.EditorAssetLibrary; SL = unreal.get_default_object(unreal.SystemLibrary)
SPEED = '350,0,0'

def sockets():
    ej = json.loads((ROOT / 'FurinaSource' / 'Data' / 'fpvm_pistol_ejection.json').read_text(encoding='utf-8'))
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); out = {}
    for key, e in ej.items():
        n = key.upper(); mesh = unreal.load_asset(f'/Game/Furina/FPVM/{n}/SK_FPVM_{n}')
        a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); c = a.get_component_by_class(unreal.SkeletalMeshComponent)
        T = c.get_socket_transform('VM_Gun', unreal.RelativeTransformSpace.RTS_COMPONENT); eas.destroy_actor(a)
        p = unreal.Vector(*e['ue_cam_cm']); d = unreal.Vector(*e['ue_dir']); back = unreal.Vector(*e['ue_back'])
        rot_cs = unreal.MathLibrary.make_rot_from_xy(d, back)
        sock = mesh.find_socket('VM_CaseFX')
        if not sock:
            sock = unreal.SkeletalMeshSocket(outer=mesh); SL.call_method('SetNamePropertyByName', (sock, 'SocketName', 'VM_CaseFX')); mesh.add_socket(sock, False)
        SL.call_method('SetNamePropertyByName', (sock, 'BoneName', 'VM_Gun'))
        SL.call_method('SetVectorPropertyByName', (sock, 'RelativeLocation', unreal.MathLibrary.inverse_transform_location(T, p)))
        SL.call_method('SetRotatorPropertyByName', (sock, 'RelativeRotation', unreal.MathLibrary.inverse_transform_rotation(T, rot_cs)))
        mesh.modify(); assert ASSETS.save_loaded_asset(mesh, False)
        a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); c = a.get_component_by_class(unreal.SkeletalMeshComponent)
        chk = c.get_socket_transform('VM_CaseFX', unreal.RelativeTransformSpace.RTS_COMPONENT); eas.destroy_actor(a)
        out[key] = {'err_cm': round((chk.translation - p).length(), 3), 'x_dot_dir': round(unreal.MathLibrary.get_forward_vector(chk.rotation.rotator()).dot(d), 3)}
    return out

def case_actors():
    out = {}
    for path in ('/Game/Furina/FX/Pistol/BP_FPVM_9mmCase', '/Game/Furina/FX/Pistol/BP_FPVM_32Case'):
        bp = unreal.load_asset(path); g = Graph(bp); literal(g.nodes['TFPCaseDirection'], 'Direction', SPEED)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); assert bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
        assert ASSETS.save_loaded_asset(bp, False); out[path.rsplit('/', 1)[1]] = SPEED
    return out

def pawn_graph():
    pawn = unreal.load_asset(PAWN); g = Graph(pawn, 'PistolCase_')
    xf = g.nodes['PistolCase_CaseTransform']; rp = xf.find_input_pin('Rotation'); was = [p.get_owning_node().get_name() for p in rp.list_connected_pins()]
    if 'PistolCase_SocketRotation' not in g.nodes:
        rp.break_pin_links()
        rot = g.call('SocketRotation', ENGINE + 'SceneComponent:GetSocketRotation', target=g.get('FurinaFPVM'), InSocketName='VM_CaseFX')
        wire(rot.find_result_pin(), rp)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn); assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert ASSETS.save_loaded_asset(pawn, False)
    return {'rotation_was': was}

try:
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    R['sockets'] = sockets(); R['actors'] = case_actors(); R['pawn'] = pawn_graph()
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'PistolCases.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8')
