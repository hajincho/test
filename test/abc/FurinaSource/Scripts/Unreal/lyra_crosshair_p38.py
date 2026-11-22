"""에디터(편집 전용, PIE 아님, 2026-11-22): 십자선 복구 + P38 슬라이드 정위치 -> Saved/CrosshairP38.json("done": true)
 1) 십자선: lyra_fpvm_primary.hide_weapon_hud 가 독일 무기(1인칭 뷰모델) HUD 를 통째로 막아(HistoricalView_DrawOnlyLegacy 조건 = 참)
    조준경이 아닐 때는 아무것도 그리지 않았음 -> ScopeView_HasGlass 의 else(조준경 아님)를 LCH_HudDraw(영점 글자) -> K2Node_FPAH_IsAds(정조준이 아니면 십자선)로 연결.
    옛 M4 HUD(탄수 틀 등)는 그대로 숨김.
 2) P38: 원본 모델의 슬라이드가 3.31cm 후퇴한 상태였음(fpvm_lib.seat_p38_slide 로 Blender 에서 보정) -> SK_FPVM_P38 + 클립 13개 다시 가져오기,
    소켓 VM_Muzzle / VM_CaseFX 다시 계산, 캐릭터 BP 의 P38 정조준 상수(HistoryPrimary_ADSLocation/Rotation_P38) 갱신."""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib
import lyra_fpvm_optics, lyra_fpvm_animation_import, lyra_hist_fx
for _m in (lyra_fpvm_optics, lyra_fpvm_animation_import, lyra_hist_fx): importlib.reload(_m)   # 열린 에디터에서 이전 실행의 모듈(옛 정조준 json)이 남지 않게
from lyra_fpvm_optics import HUD, PAWN, Graph, wire, literal, view_transform
import lyra_hist_fx as H
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
ASSETS = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary


def crosshair():
    hud = unreal.load_asset(HUD); g = Graph(hud)
    glass = g.nodes['ScopeView_HasGlass']; zero = g.nodes['LCH_HudDraw']
    else_pin = glass.find_else_pin()
    if zero.find_execute_pin() not in list(else_pin.list_connected_pins()):
        else_pin.break_pin_links(); wire(else_pin, zero.find_execute_pin())
    nxt = [p.get_owning_node().get_name() for p in zero.find_then_pin().list_connected_pins()]
    assert nxt == ['K2Node_FPAH_IsAds'], nxt
    BEL.compile_blueprint(hud); assert hud.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert ASSETS.save_loaded_asset(hud, False)
    return {'glass_else': [p.get_owning_node().get_name() for p in else_pin.list_connected_pins()], 'zero_then': nxt}


def keep_sockets(mesh):
    out = []
    for i in range(mesh.num_sockets()):
        s = mesh.get_socket_by_index(i)
        out.append((str(s.get_editor_property('socket_name')), str(s.get_editor_property('bone_name')), s.get_editor_property('relative_location'), s.get_editor_property('relative_rotation'), s.get_editor_property('relative_scale')))
    return out


def restore_sockets(mesh, saved):
    SL = unreal.get_default_object(unreal.SystemLibrary); added = []
    for name, bone, loc, rot, scl in saved:
        if mesh.find_socket(name): continue
        s = unreal.SkeletalMeshSocket(outer=mesh); SL.call_method('SetNamePropertyByName', (s, 'SocketName', name)); mesh.add_socket(s, False)
        SL.call_method('SetNamePropertyByName', (s, 'BoneName', bone)); SL.call_method('SetVectorPropertyByName', (s, 'RelativeLocation', loc))
        SL.call_method('SetRotatorPropertyByName', (s, 'RelativeRotation', rot)); SL.call_method('SetVectorPropertyByName', (s, 'RelativeScale', scl)); added.append(name)
    mesh.modify(); assert ASSETS.save_loaded_asset(mesh, False)
    return added


def case_socket():
    """lyra_pistol_cases.sockets 와 같은 계산(P38 만)."""
    e = json.loads((ROOT / 'FurinaSource' / 'Data' / 'fpvm_pistol_ejection.json').read_text(encoding='utf-8'))['p38']
    SL = unreal.get_default_object(unreal.SystemLibrary); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mesh = unreal.load_asset('/Game/Furina/FPVM/P38/SK_FPVM_P38')
    a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); c = a.get_component_by_class(unreal.SkeletalMeshComponent)
    T = c.get_socket_transform('VM_Gun', unreal.RelativeTransformSpace.RTS_COMPONENT); eas.destroy_actor(a)
    p = unreal.Vector(*e['ue_cam_cm']); d = unreal.Vector(*e['ue_dir']); back = unreal.Vector(*e['ue_back'])
    sock = mesh.find_socket('VM_CaseFX')
    if not sock:
        sock = unreal.SkeletalMeshSocket(outer=mesh); SL.call_method('SetNamePropertyByName', (sock, 'SocketName', 'VM_CaseFX')); mesh.add_socket(sock, False)
    SL.call_method('SetNamePropertyByName', (sock, 'BoneName', 'VM_Gun'))
    SL.call_method('SetVectorPropertyByName', (sock, 'RelativeLocation', unreal.MathLibrary.inverse_transform_location(T, p)))
    SL.call_method('SetRotatorPropertyByName', (sock, 'RelativeRotation', unreal.MathLibrary.inverse_transform_rotation(T, unreal.MathLibrary.make_rot_from_xy(d, back))))
    mesh.modify(); assert ASSETS.save_loaded_asset(mesh, False)
    return [round(v, 2) for v in e['ue_cam_cm']]


def p38():
    mesh = unreal.load_asset('/Game/Furina/FPVM/P38/SK_FPVM_P38'); saved = keep_sockets(mesh); R['p38_sockets_before'] = [s[0] for s in saved]
    H.PISTOLS = ('p38',); out = {'clips': H.pistols()}
    out['restored'] = restore_sockets(unreal.load_asset('/Game/Furina/FPVM/P38/SK_FPVM_P38'), saved)
    H.MESHES = {'p38': H.MESHES['p38']}; out['muzzle'] = H.sockets(); out['case'] = case_socket()
    pawn = unreal.load_asset(PAWN); g = Graph(pawn); loc, rot = view_transform('p38')
    literal(g.nodes['HistoryPrimary_ADSLocation_P38'], 'FurinaVMAdsLoc', loc); literal(g.nodes['HistoryPrimary_ADSRotation_P38'], 'FurinaVMAdsRot', rot)
    BEL.compile_blueprint(pawn); assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert ASSETS.save_loaded_asset(pawn, False); out['ads'] = [loc, rot]
    m = unreal.load_asset('/Game/Furina/FPVM/P38/SK_FPVM_P38'); out['sockets_after'] = [str(m.get_socket_by_index(i).get_editor_property('socket_name')) for i in range(m.num_sockets())]
    return out


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try:
        for name, fn in (('crosshair', crosshair), ('p38', p38)):
            try: R[name] = fn()
            except Exception: R[name] = 'ERROR ' + traceback.format_exc()[-1500:]
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))


try: main()
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'CrosshairP38.json').write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
print('CROSSHAIR_P38', json.dumps(R, default=str, ensure_ascii=False)[:1500])
