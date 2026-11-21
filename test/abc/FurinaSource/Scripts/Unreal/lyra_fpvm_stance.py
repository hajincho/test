"""에디터(편집 전용, 2026-11-21): 긴 총 견착 + 대기 자세 뒤로 당기기 + 탄창 재장전 구도 + 저격용 G43 탄창 재장전
 1) 가져오기: MP40/MP38/StG44 Reload(아랫면이 보이게 든 새 자세), G43 ZF4 메시(탄창을 VM_Mag 뼈로 뗌) + AS_FPVM_G43_MagReload, VM_Muzzle 소켓 다시
 2) 캐릭터 BP(노드 접두사 STC_):
   - 정조준 가중치 목표 = 정조준 ? 1 : (견착 AND 권총 아님) ? 0.6 : 0   (긴 총 견착 = 개머리판을 어깨에 붙여 조준선 쪽으로 60% + 3cm 낮게)
   - 대기(비조준) 기준 위치: 긴 총은 4cm 뒤로(사용자: '총이 너무 내밀어졌다')
   - 탄창 쓰는 총(MP40/MP38/StG44/저격용 G43) 재장전 중: 뷰모델 전체를 앞 9cm·아래 3cm(팔이 짧아 총이 눈앞을 가리던 구도 보완, 아랫면이 보이게)
   - 저격용 G43(FurinaVMLastKey == g43_zf4): 클립·낱발 대신 탄창 교환(AS_FPVM_G43_MagReload, 3.2초, 한 번에 가득)
 -> Saved/FPVMStance.json("done": true)"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, STRINGS, PAWN, Graph, chain, wire, literal
from lyra_fpvm_animation_import import import_clip
from lyra_fpvm_receiver_import import import_viewmodel, receiver_material
import lyra_hist_fx as H
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
ASSETS = unreal.EditorAssetLibrary; MAP = ENGINE + 'BlueprintMapLibrary:'; GS = ENGINE + 'GameplayStatics:'
MAG_WEAPONS = {'mp40': (9.0, 0.0, -3.0), 'mp38': (9.0, 0.0, -3.0), 'stg44': (9.0, 0.0, -3.0), 'g43_zf4': (9.0, 0.0, -3.0)}
HIP_PULL = -4.0; SH_ALPHA = 0.6; SH_DIP = 3.0


def assets():
    out = {}
    for name in ('MP40', 'MP38', 'STG44'):
        folder = f'/Game/Furina/FPVM/{name}'; skel = unreal.load_asset(f'{folder}/SK_FPVM_{name}').get_editor_property('skeleton')
        a = import_clip(folder, skel, f'AS_FPVM_{name}_Reload'); assert ASSETS.save_loaded_asset(a, False); out[a.get_name()] = round(a.get_play_length(), 3)
    mesh, data = import_viewmodel(ROOT, 'G43', 'ZF4', receiver_material(), 'g43_zf4'); assert ASSETS.save_loaded_asset(mesh, False); out['zf4'] = data
    skel = unreal.load_asset('/Game/Furina/FPVM/G43/SK_FPVM_G43_Skeleton') or mesh.get_editor_property('skeleton')
    a = import_clip('/Game/Furina/FPVM/G43', skel, 'AS_FPVM_G43_MagReload'); assert ASSETS.save_loaded_asset(a, False); out['MagReload'] = round(a.get_play_length(), 3)
    for x in (skel,): ASSETS.save_loaded_asset(x, False)
    out['bones_zf4_has_mag'] = 'VM_Mag' in [str(b) for b in unreal.SkeletalMeshEditorSubsystem.get_bone_names(mesh)] if hasattr(unreal.SkeletalMeshEditorSubsystem, 'get_bone_names') else None
    return out


def graph(pawn):
    api = unreal.BlueprintEditorLibrary; have = {str(n) for n in api.list_member_variable_names(pawn)}
    if 'FurinaRlOfs' not in have: assert api.add_member_variable(pawn, 'FurinaRlOfs', H.map_type('struct', '/Script/CoreUObject.Vector'))
    if 'FurinaVMRlW' not in have: assert api.add_member_variable(pawn, 'FurinaVMRlW', api.get_basic_type_by_name('real'))
    api.compile_blueprint(pawn)
    m = unreal.Map(str, unreal.Vector)
    for k, v in MAG_WEAPONS.items(): m[k] = unreal.Vector(*v)
    unreal.get_default_object(pawn.generated_class()).set_editor_property('FurinaRlOfs', m)
    g = Graph(pawn, 'STC_'); out = {}
    if 'STC_ShTarget' in g.nodes: return 'already installed'
    val = lambda n: n.find_result_pin()
    def call(name, fn, **kw): return g.call(name, fn, **kw)
    def active(name, comp): return val(call(name, ENGINE + 'ActorComponent:IsActive', target=g.get(comp)))
    key = lambda: g.get('FurinaVMLastKey')
    pistol = call('IsPistolFind', MAP + 'Map_Find', TargetMap=g.get('FurinaPAnims'), Key=val(call('IsPistolKey', STRINGS + 'Concat_StrStr', A=key(), B='_IdleS'))).find_output_pin('ReturnValue')
    notp = val(call('NotPistol', MATH + 'Not_PreBool', A=pistol))
    sh = val(call('ShOn', MATH + 'BooleanOR', A=active('ShA', 'FurinaShoulder'), B=active('ShB', 'FurinaShoulderAuto')))
    sh_long = val(call('ShLong', MATH + 'BooleanAND', A=sh, B=notp))
    # 정조준 가중치 목표
    adsi = next(n for nm, n in g.nodes.items() if nm.startswith('VM_AdsI_')); tgt = adsi.find_input_pin('Target'); old_src = [p.get_owning_node().get_name() for p in tgt.list_connected_pins()]; tgt.break_pin_links()
    inner = val(call('ShTarget', MATH + 'SelectFloat', A=SH_ALPHA, B=0.0, bPickA=sh_long))
    wire(val(call('AdsTarget', MATH + 'SelectFloat', A=1.0, B=inner, bPickA=active('AdsOnS', 'FurinaADS'))), tgt); out['ads_target_was'] = old_src
    # 재장전 구도 가중치(탄창 총 + 재장전 중) -> FurinaVMRlW 를 0.033초마다 보간
    rf = call('RlFind', MAP + 'Map_Find', TargetMap=g.get('FurinaRlOfs'), Key=key())
    want = val(call('RlWant', MATH + 'BooleanAND', A=rf.find_output_pin('ReturnValue'), B=g.get('FurinaReloading')))
    wt = val(call('RlWT', MATH + 'SelectFloat', A=1.0, B=0.0, bPickA=want))
    wi = val(call('RlWI', MATH + 'FInterpTo', Current=g.get('FurinaVMRlW'), Target=wt, DeltaTime=0.033, InterpSpeed=7.0))
    store = g.store('RlW', 'FurinaVMRlW', wi)
    ads_set = next(n for nm, n in g.nodes.items() if nm.startswith('VM_AdsSet_')); t = ads_set.find_then_pin(); nxt = list(t.list_connected_pins()); t.break_pin_links()
    wire(t, store.find_execute_pin())
    for p in nxt: wire(store.find_then_pin(), p)
    # 대기 기준 위치(A) = 뒤로 당김(긴 총) + 재장전 구도 + 견착 때 조금 낮게(정조준 가중치 a 에 대해 4a(1-a), a=0.6 에서 0.96)
    a = g.get('FurinaVMAds')
    aa = val(call('DipAA', MATH + 'Multiply_DoubleDouble', A=a, B=g.get('FurinaVMAds')))
    dip = val(call('Dip', MATH + 'Multiply_DoubleDouble', A=val(call('DipA', MATH + 'Subtract_DoubleDouble', A=g.get('FurinaVMAds'), B=aa)), B=-4.0 * SH_DIP))   # a(1-a) = a - a*a
    dipz = val(call('DipZ', MATH + 'SelectFloat', A=dip, B=0.0, bPickA=notp))
    pull = val(call('Pull', MATH + 'SelectFloat', A=HIP_PULL, B=0.0, bPickA=notp))
    base = val(call('BaseV', MATH + 'MakeVector', X=pull, Y=0.0, Z=dipz))
    rlv = val(call('RlV', MATH + 'Multiply_VectorFloat', A=rf.find_output_pin('Value'), B=g.get('FurinaVMRlW')))
    loc = val(call('ALoc', MATH + 'Add_VectorVector', A=base, B=rlv))
    mA = next(n for nm, n in g.nodes.items() if nm.startswith('VM_AdsA_')); lp = mA.find_input_pin('Location'); lp.break_pin_links(); wire(loc, lp)
    # 저격용 G43 탄창 교환
    amount = g.nodes['HistoryReload_Amount']; at = amount.find_then_pin(); first = list(at.list_connected_pins()); at.break_pin_links()
    isz = val(call('IsZF4', STRINGS + 'EqualEqual_StrStr', A=key(), B='g43_zf4'))
    br = g.branch('MagG43', isz); wire(at, br.find_execute_pin())
    for p in first: wire(br.find_else_pin(), p)
    clip = unreal.load_asset('/Game/Furina/FPVM/G43/AS_FPVM_G43_MagReload')
    plan = [g.store('MagClip', 'FurinaVMAnimReload', clip), g.store('MagLen', 'FurinaVMReloadLen', clip.get_play_length()), g.store('MagLoose', 'FurinaLooseReload', False)]
    tail = chain(br.find_then_pin(), plan); wire(tail, g.nodes['HistoryReload_PrepareProp'].find_execute_pin())
    out['reload_first_was'] = [p.get_owning_node().get_name() for p in first]
    return out


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try: R['assets'] = assets()
    finally: unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
    R['sockets'] = H.sockets()
    pawn = unreal.load_asset(PAWN); R['graph'] = graph(pawn)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn); R['status'] = str(pawn.get_editor_property('status'))
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    R['saved'] = bool(ASSETS.save_loaded_asset(pawn, False))

try: main()
except Exception: R['error'] = traceback.format_exc()[-2000:]
R['done'] = True; (ROOT / 'Saved' / 'FPVMStance.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8'); print('FPVM_STANCE', R.get('error', 'ok')[-300:])
