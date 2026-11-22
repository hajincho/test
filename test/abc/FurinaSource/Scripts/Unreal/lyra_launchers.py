"""에디터(편집 전용, PIE 아님, 2026-11-21): 판처파우스트(Pzf 60)·판처슈렉(RPzB 54) 1인칭 + 탄두 발사체 + 마우스 휠 영점 + 소총 영점 300/200 m
 Blender: Scripts/Blender/fpvm_launchers.py -- <panzerfaust|panzerschreck> export, fpvm_ads_calc.py -- all 먼저.
 A1 뷰모델·애니(Idle/IdleEmpty/Fire/Reload) 가져오기  A2 소켓 VM_Muzzle(관 앞 끝) / VM_Launch(발사 위치) / VM_Rear(관 뒤 끝, 후폭풍)
 A3 판처파우스트 탄두 발사체 메시  A4 발사체 BP 2개(BP_FurinaBullet 복제: 적중 피해 GAS 그대로 + 폭발 이펙트·소리 + 범위 피해 + 사라짐)
 A5 휠 입력 IA_FurinaZeroUp/Down(MouseScrollUp/Down)
 B  캐릭터 BP(노드 접두사 LCH_):
   B1 변수·표(FurinaZeroIdx, FurinaZeroLoc/Rot = 영점별 정조준 변환, FurinaZeroInfo = (발사각°, 영점 m, 0), FurinaLchAnims, 사격 효과 표에 두 화기)
   B2 무기 키 분기(기관단총 다음, 권총 앞): 메시·애니·정조준(가장 낮은 영점)·탄 1발, 장착 때 탄이 없으면 빈 대기 애니
   B3 사격: 대전차 화기면 소총탄 대신 발사체를 VM_Launch 에서, 방향 = 카메라 + 위로 발사각(정조준 = 고른 영점, 비조준 = 가장 낮은 영점),
      쏜 뒤 대기 애니 = 빈 것(탄두/로켓 없음), 뒤 끝 후폭풍 화염
   B4 재장전 분기: 재장전 애니 + 대기 애니를 탄 있는 것으로
   B5 휠 위/아래: 영점 칸 +-1(0..2) -> 정조준 변환 교체(정조준 보간이 부드럽게 관을 들어 올림)
   B6 소총 영점: 정조준 조준점 = 카메라 + 카메라 앞 x 영점 거리(뷰모델이면; 숨긴 3인칭 소총 기준이던 것), 저격총 300 m, 권총 25 m, 나머지 200 m
      거리 보정(탄 낙차 상쇄) 상한 200 m -> 400 m
 C  HUD: 대전차 화기면 'ZERO 60m' 표시
 -> Saved/Launchers.json("done": true)"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, STRINGS, PAWN, HUD, Graph, chain, wire, literal, view_transform
import lyra_fpvm_primary as P
from lyra_fpvm_animation_import import import_fbx, import_clip
from lyra_hist_fx import map_type, subobjects
ROOT = Path(unreal.Paths.project_dir()).resolve(); DATA = ROOT / 'FurinaSource' / 'Data'; R = {}
ASSETS = unreal.EditorAssetLibrary; TOOLS = unreal.AssetToolsHelpers.get_asset_tools(); API = unreal.BlueprintEditorLibrary
GS = ENGINE + 'GameplayStatics:'; SYSL = ENGINE + 'KismetSystemLibrary:'; MAP = ENGINE + 'BlueprintMapLibrary:'; GAS = '/Script/GameplayAbilities.'
LJ = json.loads((DATA / 'fpvm_launchers_ads.json').read_text(encoding='utf-8'))
W = {'panzerfaust': dict(name='PANZERFAUST', bp='BP_FurinaPzfWarhead', speed=4500.0, radius=7.0, dmg=300.0, splash=(250.0, 120.0),
                         mesh='/Game/Furina/FPVM/PANZERFAUST/SM_FPVM_PzfWarhead', trail=None, fx=(0.3, 1.6, 1.4), fx2=(0.6, 2.0, 4.0), rear=(2.2, 3.5)),
     'panzerschreck': dict(name='PANZERSCHRECK', bp='BP_FurinaPzsRocket', speed=11000.0, radius=4.4, dmg=300.0, splash=(250.0, 120.0),
                           mesh='/Game/Furina/Weapons/Germany/panzerschreck_rocket/SM_DE_panzerschreck_rocket', trail='/Game/Effects/Particles/Explosion/NS_Grenade_Trail.NS_Grenade_Trail',
                           fx=(0.2, 1.2, 1.2), fx2=(0.8, 2.5, 4.0), rear=(2.6, 4.5))}
SNIPERS = ('kar98k_zf39', 'kar98k_zf41', 'g43_zf4'); PISTOL_ZERO = ('p38', 'p08', 'pp')
EXPLO = '/Game/Effects/Particles/Explosion/NS_Grenade_Explosion.NS_Grenade_Explosion'; BOOM = '/Game/Audio/Sounds/Grenade/grenade_explode_body_01.grenade_explode_body_01'
def val(n): return n.find_result_pin()
def step(name):
    def deco(fn):
        def run(*a):
            try: R[name] = fn(*a)
            except Exception: R[name] = 'ERROR ' + traceback.format_exc()[-1800:]; raise
        return run
    return deco

# ------------------------------------------------------------------ A1
@step('A1_import')
def import_all():
    out = {}; rifle = unreal.load_asset('/Game/Furina/FPVM/Kar98k/SK_FPVM_Kar98k_Interior')
    for key, w in W.items():
        n = w['name']; folder = '/Game/Furina/FPVM/' + n; mesh_name = 'SK_FPVM_' + n
        import_fbx(mesh_name + '.fbx', folder, mesh_name, mesh=True, animations=False)
        mesh = unreal.load_asset(folder + '/' + mesh_name); skel = mesh.get_editor_property('skeleton')
        defaults = {str(s.material_slot_name): s.material_interface for s in rifle.materials}
        for src in [key] + (['panzerschreck_rocket'] if key == 'panzerschreck' else []):
            defaults.update({str(s.material_slot_name): s.material_interface for s in unreal.load_asset(f'/Game/Furina/Weapons/Germany/{src}/SM_DE_{src}').static_materials})
        mats = []; miss = []
        for slot in mesh.materials:
            m = defaults.get(str(slot.material_slot_name))
            if m: slot.material_interface = m
            else: miss.append(str(slot.material_slot_name))
            mats.append(slot)
        mesh.set_editor_property('materials', mats)
        clips = {c: import_clip(folder, skel, f'AS_FPVM_{n}_{c}') for c in ('Idle', 'IdleEmpty', 'Fire', 'Reload')}
        for a in (mesh, skel, *clips.values()): assert ASSETS.save_loaded_asset(a, False), a.get_name()
        out[key] = {'missing_slots': miss, **{c: round(a.get_play_length(), 3) for c, a in clips.items()}}
    return out

# ------------------------------------------------------------------ A2
@step('A2_sockets')
def sockets():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); SL = unreal.get_default_object(unreal.SystemLibrary); out = {}
    for key, w in W.items():
        mesh = unreal.load_asset(f"/Game/Furina/FPVM/{w['name']}/SK_FPVM_{w['name']}")
        a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); c = a.get_component_by_class(unreal.SkeletalMeshComponent)
        T = c.get_socket_transform('VM_Gun', unreal.RelativeTransformSpace.RTS_COMPONENT); eas.destroy_actor(a)
        for sname, m in LJ[key]['sockets'].items():
            p = unreal.Vector(*m['ue_cam_cm']); rot_cs = unreal.MathLibrary.make_rot_from_yz(unreal.Vector(*m['ue_fwd']), unreal.Vector(*m['ue_up']))
            sock = mesh.find_socket(sname)
            if not sock:
                sock = unreal.SkeletalMeshSocket(outer=mesh); SL.call_method('SetNamePropertyByName', (sock, 'SocketName', sname)); mesh.add_socket(sock, False)
            SL.call_method('SetNamePropertyByName', (sock, 'BoneName', 'VM_Gun'))
            SL.call_method('SetVectorPropertyByName', (sock, 'RelativeLocation', unreal.MathLibrary.inverse_transform_location(T, p)))
            SL.call_method('SetRotatorPropertyByName', (sock, 'RelativeRotation', unreal.MathLibrary.inverse_transform_rotation(T, rot_cs)))
        mesh.modify(); assert ASSETS.save_loaded_asset(mesh, False)
        a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); c = a.get_component_by_class(unreal.SkeletalMeshComponent)
        out[key] = {s: round((c.get_socket_transform(s, unreal.RelativeTransformSpace.RTS_COMPONENT).translation - unreal.Vector(*m['ue_cam_cm'])).length(), 3) for s, m in LJ[key]['sockets'].items()}
        eas.destroy_actor(a)
    return out

# ------------------------------------------------------------------ A3
@step('A3_warhead')
def warhead_mesh():
    ui = unreal.FbxImportUI(); ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False; ui.import_animations = False
    t = unreal.AssetImportTask(); t.filename = str(ROOT / 'FurinaSource/FBX/FPVM/SM_FPVM_PzfWarhead.fbx'); t.destination_path = '/Game/Furina/FPVM/PANZERFAUST'; t.destination_name = 'SM_FPVM_PzfWarhead'
    t.automated = True; t.replace_existing = True; t.options = ui; TOOLS.import_asset_tasks([t])
    m = unreal.load_asset(W['panzerfaust']['mesh']); mi = unreal.load_asset('/Game/Furina/Weapons/Germany/panzerfaust/MI_DE_panzerfaust_Material')
    for i in range(len(m.static_materials)): m.set_material(i, mi)
    assert ASSETS.save_loaded_asset(m, False); b = m.get_bounding_box(); return [[round(b.min.x, 1), round(b.min.y, 1), round(b.min.z, 1)], [round(b.max.x, 1), round(b.max.y, 1), round(b.max.z, 1)]]

# ------------------------------------------------------------------ A4
@step('A4_projectiles')
def projectiles():
    out = {}
    for key, w in W.items():
        path = '/Game/Furina/FP/' + w['bp']
        if not ASSETS.does_asset_exist(path): assert ASSETS.duplicate_asset('/Game/Furina/FP/BP_FurinaBullet', path)
        bp = unreal.load_asset(path); sub, lib, hs = subobjects(bp); comp = lambda n: lib.get_associated_object(lib.get_data(hs[n]))
        mesh = unreal.load_asset(w['mesh']); b = mesh.get_bounding_box()
        nose_pos_y = abs(b.max.y) < abs(b.min.y) if key == 'panzerfaust' else True   # 탄두: 짧은 쪽이 탄두 앞(꼬리대가 김). 로켓: SM_DE 규약(앞 = UE +Y)
        vis = comp('ProjectileVisual'); vis.set_static_mesh(mesh); vis.set_editor_property('relative_rotation', unreal.Rotator(0, 0, -90 if nose_pos_y else 90))
        vis.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1)); vis.set_editor_property('relative_location', unreal.Vector(0, 0, 0))
        tr = comp('Tracer'); tr.set_editor_property('visible', False); tr.set_editor_property('hidden_in_game', True)
        sph = comp('Bullet'); sph.set_editor_property('sphere_radius', w['radius'])
        pm = comp('Ballistics'); pm.set_editor_property('initial_speed', w['speed']); pm.set_editor_property('max_speed', w['speed'] * 1.2)
        pm.set_editor_property('projectile_gravity_scale', 1.0); pm.set_editor_property('should_bounce', False); pm.set_editor_property('rotation_follows_velocity', True)
        API.compile_blueprint(bp)
        cdo = unreal.get_default_object(bp.generated_class()); cdo.set_editor_property('FurinaDamage', w['dmg']); cdo.set_editor_property('initial_life_span', 12.0)
        g = Graph(bp, 'LCH_'); N = g.nodes
        if 'LCH_Boom' not in N:
            literal(N['K2Node_FPB_Kv'], 'B', 0.0)                                  # 공기 저항(소총탄용) 끔
            inst = N['K2Node_FPB_Inst']; ign = N['K2Node_FPB_Ignore'].find_input_pin('Actor'); ign.break_pin_links()   # 무시할 액터 = 주인(지연 생성은 Instigator 가 없음)
            wire(val(g.call('Owner', ENGINE + 'Actor:GetOwner')), ign)
            hit = N['K2Node_FPB_Hit']; hl = hit.find_output_pin('HitLocation'); t = hit.find_then_pin(); t.break_pin_links()
            boom = g.call('Boom', '/Script/Niagara.NiagaraFunctionLibrary:SpawnSystemAtLocation', SystemTemplate=EXPLO, Location=hl)
            snd = g.call('Sound', GS + 'PlaySoundAtLocation', Sound=BOOM, Location=hl)
            # 범위 피해: 모든 폰 중 반경 안(직격 대상은 직격 피해만, 아래 FHG 경로)
            allp = g.call('AllPawns', GS + 'GetAllActorsOfClass', ActorClass='/Script/Engine.Pawn')
            loop = g.editor.add_macro_node('/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop'); assert loop; loop.rename('LCH_Loop')
            wire(allp.find_output_pin('OutActors'), loop.find_input_pin('Array'))
            el = loop.find_output_pin('Array Element')
            dist = val(g.call('Dist', MATH + 'Vector_Distance', V1=hl, V2=val(g.call('ElLoc', ENGINE + 'Actor:K2_GetActorLocation', target=el))))
            near = val(g.call('Near', MATH + 'Less_DoubleDouble', A=dist, B=w['splash'][0]))
            notdirect = val(g.call('NotDirect', MATH + 'NotEqual_ObjectObject', A=el, B=hit.find_output_pin('Other')))
            asc = val(g.call('ASC', GAS + 'AbilitySystemBlueprintLibrary:GetAbilitySystemComponent', Actor=el))
            okasc = val(g.call('AscOk', SYSL + 'IsValid', Object=asc))
            cond = val(g.call('And2', MATH + 'BooleanAND', A=val(g.call('And1', MATH + 'BooleanAND', A=near, B=notdirect)), B=okasc))
            br = g.branch('InBlast', cond); wire(loop.find_output_pin('LoopBody'), br.find_execute_pin())
            ge = g.get('FurinaDamageEffect')
            ctx = g.call('Ctx', GAS + 'AbilitySystemComponent:MakeEffectContext', target=asc)
            spec = g.call('Spec', GAS + 'AbilitySystemComponent:MakeOutgoingSpec', target=asc, GameplayEffectClass=ge, Level=1.0, Context=val(ctx))
            setc = g.call('SetDmg', GAS + 'AbilitySystemBlueprintLibrary:AssignTagSetByCallerMagnitude', SpecHandle=val(spec), DataTag='(TagName="SetByCaller.Damage")', Magnitude=w['splash'][1])
            app = g.call('Apply', GAS + 'AbilitySystemComponent:BP_ApplyGameplayEffectSpecToSelf', target=asc, SpecHandle=val(setc))
            chain(br.find_then_pin(), [setc, app])
            wire(chain(t, [boom, snd, allp]), loop.find_input_pin('Exec'))
            wire(loop.find_output_pin('Completed'), N['FHG_Branch'].find_execute_pin())   # 직격(GAS) -> 사라짐
            kill = N['K2Node_FPB_Kill'].find_execute_pin(); wire(N['FHG_Apply'].find_then_pin(), kill)
            mark = N['K2Node_FPB_Mark']; me = mark.find_execute_pin(); [p.break_pin_links() for p in [me]]; wire(N['FHG_Branch'].find_else_pin(), kill)
            if w['trail']:   # 로켓: 연소 불꽃·연기 꼬리(로켓 모터는 관 밖 약 2 m 까지 탐 -> 짧게 붙임)
                begin = N['K2Node_FPB_Begin']; bt = begin.find_then_pin(); nxt = list(bt.list_connected_pins()); bt.break_pin_links()
                tr_ = g.call('Trail', '/Script/Niagara.NiagaraFunctionLibrary:SpawnSystemAttached', SystemTemplate=w['trail'], AttachToComponent=g.get('ProjectileVisual'), AttachPointName='None',
                             LocationType='KeepRelativeOffset', bAutoDestroy=True)
                wire(bt, tr_.find_execute_pin())
                for p in nxt: wire(tr_.find_then_pin(), p)
        API.compile_blueprint(bp); st = str(bp.get_editor_property('status')); assert bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR, st
        assert ASSETS.save_loaded_asset(bp, False); out[key] = {'status': st, 'nose_pos_y': nose_pos_y, 'bounds_y': [round(b.min.y, 1), round(b.max.y, 1)]}
    return out

# ------------------------------------------------------------------ A5
@step('A5_input')
def inputs():
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC'); out = []
    def key(n): k = unreal.Key(); k.set_editor_property('key_name', n); return k
    def listing(): return [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None) for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    for nm, k in (('IA_FurinaZeroUp', 'MouseScrollUp'), ('IA_FurinaZeroDown', 'MouseScrollDown')):
        p = '/Game/Furina/Input/' + nm
        ia = unreal.load_asset(p) if ASSETS.does_asset_exist(p) else TOOLS.create_asset(nm, '/Game/Furina/Input', unreal.InputAction, None)
        ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN); ia.set_editor_property('triggers', []); ASSETS.save_loaded_asset(ia, False)
        if (k, nm) not in listing(): imc.map_key(ia, key(k))
    ASSETS.save_loaded_asset(imc, False); return [m for m in listing() if 'Zero' in str(m[1]) or 'Wheel' in m[0]]

# ------------------------------------------------------------------ B
def tables(pawn):
    have = {str(n) for n in API.list_member_variable_names(pawn)}
    want = {'FurinaZeroIdx': API.get_basic_type_by_name('int'), 'FurinaZeroLoc': map_type('struct', '/Script/CoreUObject.Vector'),
            'FurinaZeroRot': map_type('struct', '/Script/CoreUObject.Rotator'), 'FurinaZeroInfo': map_type('struct', '/Script/CoreUObject.Vector'),
            'FurinaLchAnims': map_type('object', '/Script/Engine.AnimSequence')}
    for k, t in want.items():
        if k not in have: assert API.add_member_variable(pawn, k, t), k
    API.compile_blueprint(pawn); cdo = unreal.get_default_object(pawn.generated_class())
    zl = unreal.Map(str, unreal.Vector); zr = unreal.Map(str, unreal.Rotator); zi = unreal.Map(str, unreal.Vector); an = unreal.Map(str, unreal.AnimSequence)
    for key, w in W.items():
        for i in range(3):
            loc, rot = view_transform(f'{key}_{i}'); zl[f'{key}_{i}'] = unreal.Vector(*[float(c) for c in loc.split(',')]); zr[f'{key}_{i}'] = unreal.Rotator(*[0, 0, 0])
            p_, y_, r_ = [float(c) for c in rot.split(',')]; zr[f'{key}_{i}'] = unreal.Rotator(roll=r_, pitch=p_, yaw=y_)
            z = LJ[key]['zeros'][str(i)]; zi[f'{key}_{i}'] = unreal.Vector(z['elev_deg'], z['zero_m'], 0)
        for c in ('Idle', 'IdleEmpty'): an[f'{key}_{c}'] = unreal.load_asset(f"/Game/Furina/FPVM/{w['name']}/AS_FPVM_{w['name']}_{c}")
    for k in SNIPERS: zi[k] = unreal.Vector(0, 300, 0)
    for k in PISTOL_ZERO: zi[k] = unreal.Vector(0, 25, 0)
    cdo.set_editor_property('FurinaZeroLoc', zl); cdo.set_editor_property('FurinaZeroRot', zr); cdo.set_editor_property('FurinaZeroInfo', zi); cdo.set_editor_property('FurinaLchAnims', an)
    t1 = cdo.get_editor_property('FurinaFXTable'); t2 = cdo.get_editor_property('FurinaFXTable2')
    for key, w in W.items(): t1[key] = unreal.Vector(*w['fx']); t2[key] = unreal.Vector(*w['fx2'])
    cdo.set_editor_property('FurinaFXTable', t1); cdo.set_editor_property('FurinaFXTable2', t2)
    return {'zero_keys': len(zi), 'fx': len(t1)}

def is_launcher(g, name):   # 지금 무기가 대전차 화기인가 = FurinaZeroInfo 에 '<키>_0' 이 있음
    k = val(g.call(name + 'K', STRINGS + 'Concat_StrStr', A=g.get('FurinaGameWeaponId'), B='_0'))
    return g.call(name, MAP + 'Map_Find', TargetMap=g.get('FurinaZeroInfo'), Key=k).find_output_pin('ReturnValue')
def zero_key(g, name, idx_pin):
    k0 = val(g.call(name + 'K0', STRINGS + 'Concat_StrStr', A=g.get('FurinaGameWeaponId'), B='_'))
    return val(g.call(name + 'K1', STRINGS + 'Concat_StrStr', A=k0, B=val(g.call(name + 'Idx', STRINGS + 'Conv_IntToString', InInt=idx_pin))))
def lch_anim(g, name, suffix):
    k = val(g.call(name + 'K', STRINGS + 'Concat_StrStr', A=g.get('FurinaGameWeaponId'), B=suffix))
    return g.call(name, MAP + 'Map_Find', TargetMap=g.get('FurinaLchAnims'), Key=k).find_output_pin('Value')

def equip(g):
    vm = g.get('FurinaFPVM'); key = g.get('FurinaPrimaryKey'); update = g.locate('VM_Br_12_').find_execute_pin()
    stg = next(n for nm, n in g.nodes.items() if nm.startswith('SMG') and nm.endswith('_Is_STG44')); tail = stg.find_else_pin(); after = list(tail.list_connected_pins()); tail.break_pin_links()
    for key_, w in W.items():
        n = w['name']; folder = f'/Game/Furina/FPVM/{n}'; P.CLIP_SIZES[key_] = 1
        br = g.branch('Is_' + n, val(g.call('Key_' + n, STRINGS + 'EqualEqual_StrStr', A=key, B=key_))); wire(tail, br.find_execute_pin()); tail = br.find_else_pin()
        acts = [g.call('Equip_' + n, ENGINE + 'SkeletalMeshComponent:SetSkeletalMeshAsset', target=vm, NewMesh=unreal.load_asset(f'{folder}/SK_FPVM_{n}'))]
        acts += [g.call(f'ResetMaterial_{n}_{i}', ENGINE + 'PrimitiveComponent:SetMaterial', target=vm, ElementIndex=i) for i in range(10)]
        clips = {c: unreal.load_asset(f'{folder}/AS_FPVM_{n}_{c}') for c in ('Idle', 'Fire', 'Reload')}
        for c, a in clips.items(): acts.append(g.store(f'{c}_{n}', 'FurinaVMAnim' + c, a))
        loc, rot = view_transform(key_ + '_0')
        acts += [g.store('ADSLocation_' + n, 'FurinaVMAdsLoc', loc), g.store('ADSRotation_' + n, 'FurinaVMAdsRot', rot), g.store('Zero0_' + n, 'FurinaZeroIdx', 0),
                 g.store('FireTime_' + n, 'FurinaVMFireLen', round(clips['Fire'].get_play_length(), 3)), g.store('ReloadTime_' + n, 'FurinaVMReloadLen', round(clips['Reload'].get_play_length(), 3)),
                 g.store('Interval_' + n, 'FurinaFireInterval', 1.0), g.store('NoScope_' + n, 'FurinaScopeZoom', 1.), g.store('Valid_' + n, 'FurinaVMValid', True)]
        # 탄 수가 정해진 뒤: 빈 관/빈 발사관이면 빈 대기 애니
        has = val(g.call('Loaded_' + n, MATH + 'Greater_IntInt', A=g.get('FurinaAmmo'), B=P.constant(g, 'Zero_' + n, 0)))
        suf = val(g.call('IdleSuf_' + n, MATH + 'SelectString', A='_Idle', B='_IdleEmpty', bPickA=has))
        k = val(g.call('IdleKey_' + n, STRINGS + 'Concat_StrStr', A=g.get('FurinaGameWeaponId'), B=suf))
        fix = g.store('IdleByAmmo_' + n, 'FurinaVMAnimIdle', g.call('IdleFind_' + n, MAP + 'Map_Find', TargetMap=g.get('FurinaLchAnims'), Key=k).find_output_pin('Value'))
        wire(fix.find_then_pin(), update)
        P.weapon_ammo(g, chain(br.find_then_pin(), acts), key_, fix.find_execute_pin())
    for t in after: wire(tail, t)
    return [t.get_owning_node().get_name() for t in after]

def fire(g):
    aim = g.nodes['K2Node_FPF_Aim']; t = aim.find_then_pin(); after = list(t.list_connected_pins()); t.break_pin_links()
    br = g.branch('FireBranch', is_launcher(g, 'FireIsL')); wire(t, br.find_execute_pin())
    for p in after: wire(br.find_else_pin(), p)
    ads = val(g.call('FireAds', ENGINE + 'ActorComponent:IsActive', target=g.get('FurinaADS')))
    idx = val(g.call('FireIdx', MATH + 'SelectInt', A=g.get('FurinaZeroIdx'), B=0, bPickA=ads))       # 비조준 = 가장 낮은 영점
    info = g.call('FireInfo', MAP + 'Map_Find', TargetMap=g.get('FurinaZeroInfo'), Key=zero_key(g, 'FireZ', idx)).find_output_pin('Value')
    elev = g.call('FireElev', MATH + 'BreakVector', InVec=info).find_output_pin('X')
    camrot = val(g.call('FireCamRot', ENGINE + 'PlayerCameraManager:GetCameraRotation', target=val(g.nodes['K2Node_FPF_CamMgr'])))
    rot = val(g.call('FireRot', MATH + 'ComposeRotators', A=val(g.call('FirePitch', MATH + 'MakeRotator', Roll=0.0, Pitch=elev, Yaw=0.0)), B=camrot))
    loc = val(g.call('FireLoc', ENGINE + 'SceneComponent:GetSocketLocation', target=g.get('FurinaFPVM'), InSocketName='VM_Launch'))
    xf = val(g.call('FireXf', MATH + 'MakeTransform', Location=loc, Rotation=rot))
    isf = g.branch('FireIsPzf', val(g.call('FireKeyPzf', STRINGS + 'EqualEqual_StrStr', A=g.get('FurinaGameWeaponId'), B='panzerfaust'))); wire(br.find_then_pin(), isf.find_execute_pin())
    ends = []
    for lbl, pin in (('Pzf', isf.find_then_pin()), ('Pzs', isf.find_else_pin())):
        bpn = (W['panzerfaust'] if lbl == 'Pzf' else W['panzerschreck'])['bp']; cls = f'/Game/Furina/FP/{bpn}.{bpn}_C'
        sp = g.call('Spawn' + lbl, GS + 'BeginDeferredActorSpawnFromClass', ActorClass=cls, SpawnTransform=xf, CollisionHandlingOverride='AlwaysSpawn')
        wire(g.nodes['K2Node_FPF_Self'].find_output_pin('self'), sp.find_input_pin('Owner'))
        fin = g.call('Finish' + lbl, GS + 'FinishSpawningActor', Actor=val(sp), SpawnTransform=xf)
        wire(pin, sp.find_execute_pin()); wire(sp.find_then_pin(), fin.find_execute_pin()); ends.append(fin.find_then_pin())
    empty = g.store('IdleEmpty', 'FurinaVMAnimIdle', lch_anim(g, 'EmptyFind', '_IdleEmpty'))
    for e in ends: wire(e, empty.find_execute_pin())
    # 후폭풍: 관 뒤 끝 VM_Rear(+Y = 뒤) 에 큰 화염 + 나이아가라
    rt = g.call('Rear', ENGINE + 'SceneComponent:GetSocketTransform', target=g.get('FurinaFPVM'), InSocketName='VM_Rear')
    rb = g.call('RearBreak', MATH + 'BreakTransform', InTransform=val(rt))
    isf2 = val(g.call('RearIsPzf', STRINGS + 'EqualEqual_StrStr', A=g.get('FurinaGameWeaponId'), B='panzerfaust'))
    rs = val(g.call('RearSize', MATH + 'SelectFloat', A=W['panzerfaust']['rear'][0], B=W['panzerschreck']['rear'][0], bPickA=isf2))
    rl = val(g.call('RearLen', MATH + 'SelectFloat', A=W['panzerfaust']['rear'][1], B=W['panzerschreck']['rear'][1], bPickA=isf2))
    rxf = val(g.call('RearXf', MATH + 'MakeTransform', Location=rb.find_output_pin('Location'), Rotation=rb.find_output_pin('Rotation'), Scale=val(g.call('RearScale', MATH + 'MakeVector', X=rs, Y=rl, Z=rs))))
    rsp = g.call('RearFlash', GS + 'BeginDeferredActorSpawnFromClass', ActorClass='/Game/Furina/FX/BP_HistFlash.BP_HistFlash_C', SpawnTransform=rxf, CollisionHandlingOverride='AlwaysSpawn')
    rfin = g.call('RearFinish', GS + 'FinishSpawningActor', Actor=val(rsp), SpawnTransform=rxf)
    rns = g.call('RearNS', '/Script/Niagara.NiagaraFunctionLibrary:SpawnSystemAtLocation', SystemTemplate='/Game/NiagaraExamples/FX_Weapons/MuzzleFlashes/NS_MuzzleFlash.NS_MuzzleFlash',
                 Location=rb.find_output_pin('Location'), Rotation=val(g.call('RearNSRot', MATH + 'ComposeRotators', A='0,90,0', B=rb.find_output_pin('Rotation'))))
    rnsg = g.call('RearNSScale', '/Script/Niagara.NiagaraComponent:SetVariableFloat', target=val(rns), InVariableName='Global Scale', InValue=0.9)
    rnsb = g.call('RearNSShell', '/Script/Niagara.NiagaraComponent:SetVariableBool', target=val(rns), InVariableName='Use Bullet Shell', InValue=False)
    wire(chain(empty.find_then_pin(), [rsp, rfin, rns, rnsg, rnsb]), g.nodes['K2Node_FPF_Recoil'].find_execute_pin())
    return {'else_to': [p.get_owning_node().get_name() for p in after]}

def reload(g):
    tail = next(n for nm, n in g.nodes.items() if nm.startswith('SMG') and nm.endswith('_RlBranch_STG44')).find_else_pin()
    prepare = g.nodes['HistoryReload_PrepareProp'].find_execute_pin(); wid = g.get('FurinaGameWeaponId'); out = []
    for key_, w in W.items():
        n = w['name']; br = g.branch('RlBranch_' + n, val(g.call('ReloadKey_' + n, STRINGS + 'EqualEqual_StrStr', A=wid, B=key_))); wire(tail, br.find_execute_pin()); tail = br.find_else_pin()
        a = unreal.load_asset(f'/Game/Furina/FPVM/{n}/AS_FPVM_{n}_Reload')
        plan = [g.store('ReloadClip_' + n, 'FurinaVMAnimReload', a), g.store('ReloadLen_' + n, 'FurinaVMReloadLen', round(a.get_play_length(), 3)), g.store('ReloadLoose_' + n, 'FurinaLooseReload', False),
                g.store('ReloadIdle_' + n, 'FurinaVMAnimIdle', unreal.load_asset(f'/Game/Furina/FPVM/{n}/AS_FPVM_{n}_Idle'))]
        wire(chain(br.find_then_pin(), plan), prepare); out.append(n)
    return out

def wheel(g):
    out = {}
    for nm, d in (('IA_FurinaZeroUp', 1), ('IA_FurinaZeroDown', -1)):
        ev = g.editor.create_node_from_name('Input|EnhancedActionEvents|' + nm, unreal.Vector2D(-2400, 9000 + 300 * d), []); assert ev, nm; ev.rename('LCH_' + nm)
        tag = 'Up' if d > 0 else 'Dn'
        br = g.branch('Wheel' + tag, is_launcher(g, 'WheelIsL' + tag)); wire(ev.find_output_pin('Started'), br.find_execute_pin())
        nxt = val(g.call('WheelAdd' + tag, MATH + 'Add_IntInt', A=g.get('FurinaZeroIdx'), B=d))
        cl = val(g.call('WheelClamp' + tag, MATH + 'Clamp', Value=nxt, Min=0, Max=2))
        st = g.store('WheelSet' + tag, 'FurinaZeroIdx', cl)
        zk = zero_key(g, 'WheelKey' + tag, st.find_output_pin('Output_Get'))
        sl = g.store('WheelLoc' + tag, 'FurinaVMAdsLoc', g.call('WheelLocF' + tag, MAP + 'Map_Find', TargetMap=g.get('FurinaZeroLoc'), Key=zk).find_output_pin('Value'))
        sr = g.store('WheelRot' + tag, 'FurinaVMAdsRot', g.call('WheelRotF' + tag, MAP + 'Map_Find', TargetMap=g.get('FurinaZeroRot'), Key=zk).find_output_pin('Value'))
        chain(br.find_then_pin(), [st, sl, sr]); out[nm] = ev.get_name()
    return out

def rifle_zero(g):
    # 정조준 조준점: 뷰모델(1인칭 역사 무기)이면 카메라 위치 + 카메라 앞 x 영점(cm). 3인칭 M4 는 그대로(숨긴 소총 가늠자 기준)
    vmon = g.get('FurinaVMOn'); cam = val(g.nodes['K2Node_FPF_CamMgr'])
    camloc = val(g.call('ZCamLoc', ENGINE + 'PlayerCameraManager:GetCameraLocation', target=cam))
    camfwd = val(g.call('ZCamFwd', MATH + 'GetForwardVector', InRot=val(g.call('ZCamRot', ENGINE + 'PlayerCameraManager:GetCameraRotation', target=cam))))
    info = g.call('ZInfo', MAP + 'Map_Find', TargetMap=g.get('FurinaZeroInfo'), Key=g.get('FurinaVMLastKey'))
    zm = val(g.call('ZM', MATH + 'SelectFloat', A=g.call('ZBreak', MATH + 'BreakVector', InVec=info.find_output_pin('Value')).find_output_pin('Y'), B=200.0, bPickA=info.find_output_pin('ReturnValue')))
    zcm = val(g.call('ZCm', MATH + 'Multiply_DoubleDouble', A=zm, B=100.0))
    sp = g.nodes['FPN_SightPoint']; a = sp.find_input_pin('A'); old_a = list(a.list_connected_pins())[0]; a.break_pin_links()
    wire(val(g.call('ZRear', MATH + 'SelectVector', A=camloc, B=old_a, bPickA=vmon)), a)
    s50 = g.nodes['FPN_Sight50']; sa = s50.find_input_pin('A'); old_d = list(sa.list_connected_pins())[0]; sa.break_pin_links()
    wire(val(g.call('ZDir', MATH + 'SelectVector', A=camfwd, B=old_d, bPickA=vmon)), sa)
    sb = s50.find_input_pin('B'); sb.break_pin_links()
    m4 = val(g.call('ZDistM4', MATH + 'SelectFloat', A=zcm, B=5000.0, bPickA=vmon))   # M4(3인칭 무기) 는 예전 50 m 유지
    wire(val(g.call('ZDistV', MATH + 'MakeVector', X=m4, Y=m4, Z=m4)), sb)
    literal(g.nodes['FPN_AimDistClamp'], 'Max', 8.0)                                  # 거리 보정 상한 200 m -> 400 m(300 m 영점 낙차 보정)
    return {'zero_default_m': 200, 'snipers_m': 300, 'pistols_m': 25}

@step('B_pawn')
def pawn_graph():
    pawn = unreal.load_asset(PAWN); out = {'tables': tables(pawn)}
    g = Graph(pawn, 'LCH_')
    if 'LCH_FireBranch' in g.nodes: out['note'] = 'graph already installed'
    else:
        out['equip_after'] = equip(g); out['fire'] = fire(g); out['reload'] = reload(g); out['wheel'] = wheel(g); out['zero'] = rifle_zero(g)
    from lyra_launcher_input import install
    install(pawn)
    from lyra_launcher_rear_fx import install as install_rear_fx
    install_rear_fx(pawn)
    API.compile_blueprint(pawn); out['status'] = str(pawn.get_editor_property('status'))
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR, out['status']
    out['saved'] = bool(ASSETS.save_loaded_asset(pawn, False)); return out

@step('C_hud')
def hud():
    hb = unreal.load_asset(HUD); g = Graph(hb, 'LCH_')
    if 'LCH_HudDraw' in g.nodes: return 'already'
    cast = g.nodes['M4HUD_Cast']; pawn_pin = next(p for p in cast.list_output_pins() if str(p.get_pin_name()).startswith('As'))
    tgt = unreal.load_asset(PAWN).generated_class().get_path_name()
    def pget(var): n = g.editor.add_get_member_variable_node(var, tgt); assert n, var; wire(pawn_pin, n.find_self_pin()); return n.find_output_pin(var)
    k0 = val(g.call('HudK0', STRINGS + 'Concat_StrStr', A=pget('FurinaGameWeaponId'), B='_'))
    k = val(g.call('HudK1', STRINGS + 'Concat_StrStr', A=k0, B=val(g.call('HudIdx', STRINGS + 'Conv_IntToString', InInt=pget('FurinaZeroIdx')))))
    f = g.call('HudFind', MAP + 'Map_Find', TargetMap=pget('FurinaZeroInfo'), Key=k)
    m = val(g.call('HudM', MATH + 'FTrunc', A=g.call('HudBreak', MATH + 'BreakVector', InVec=f.find_output_pin('Value')).find_output_pin('Y')))
    s = val(g.call('HudS2', STRINGS + 'Concat_StrStr', A=val(g.call('HudS1', STRINGS + 'Concat_StrStr', A='ZERO ', B=val(g.call('HudMs', STRINGS + 'Conv_IntToString', InInt=m)))), B='m'))
    txt = val(g.call('HudText', MATH + 'SelectString', A=s, B='', bPickA=f.find_output_pin('ReturnValue')))
    mode = g.nodes['FM_DrawMode']
    draw = g.call('HudDraw', ENGINE + 'HUD:DrawText', Text=txt)
    for pin in ('TextColor', 'Font', 'ScreenX', 'Scale'):
        v = mode.find_input_pin(pin); con = v.list_connected_pins()
        if con: wire(con[0], draw.find_input_pin(pin))
        else: draw.find_input_pin(pin).set_pin_value(str(v.get_pin_value()))
    y = list(mode.find_input_pin('ScreenY').list_connected_pins())[0]
    yy = val(g.call('HudY', MATH + 'Subtract_DoubleDouble', A=y, B=val(g.call('HudYOff', MATH + 'Multiply_DoubleDouble', A=g.nodes['TFPHUD_Height'].find_result_pin(), B=0.30))))
    wire(yy, draw.find_input_pin('ScreenY'))
    t = mode.find_then_pin(); old = list(t.list_connected_pins()); t.break_pin_links(); wire(t, draw.find_execute_pin())
    for p in old: wire(draw.find_then_pin(), p)
    API.compile_blueprint(hb); assert hb.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR; assert ASSETS.save_loaded_asset(hb, False)
    return str(hb.get_editor_property('status'))

def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    only = [a for a in sys.argv[1:] if not a.endswith('.py')]
    steps = [('assets', [import_all, sockets, warhead_mesh, projectiles, inputs]), ('pawn', [pawn_graph]), ('hud', [hud])]
    try:
        for name, fns in steps:
            if only and only[0] not in ('all', 'bg') and name not in only[0].split('+'): continue
            for fn in fns:
                try: fn()
                except Exception: return
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
try: main()
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'Launchers.json').write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
