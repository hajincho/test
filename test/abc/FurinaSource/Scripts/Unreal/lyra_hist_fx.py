"""에디터(편집 전용, 2026-11-21): 권총 3자세 + 탄약 기반 총구 화염·연기·반동·화면 흔들림 + 조준경(아래 총 보이기, 렌즈 먼지·기스)
 A) 에셋
  A1 권총 P38/P08/PP 메시·애니 13개(fpvm_pistols2.py) 가져오기
  A2 1인칭 메시 11종에 소켓 VM_Muzzle(뼈 VM_Gun, +Y = 총열 앞, +Z = 위): Data/fpvm_muzzle.json, fpvm_<권총>_stances.json 의 총구 위치로
  A3 M_FPVM_Hidden(가림 재질), A4 조준경 렌즈 재질(접안부 테두리 + 먼지·기스), A5 BP_HistFlash(BP_M4Flash 복제, M4 소염기 꽃잎·별 끔)
  A6 연기: SM_HistSmokePuffs + M_HistSmoke(시간 기반 WPO·불투명도) + BP_HistSmoke(액터 크기로 농도·지속·크기를 받음)
 B) 캐릭터 BP(노드 접두사 HFX_)
  B0 변수: FurinaPAnims(문자열->AnimSequence), FurinaFXTable(문자열->벡터: 반동, 흔들림, 화염 크기), FurinaFXTable2(화염 길이비, 연기 농도, 연기 지속),
     FurinaPStance(정수 0 비조준 / 1 견착 / 2 정조준), FurinaScopeTubeHidden(불)
  B1 무기 바뀔 때 FurinaPStance = 0
  B2 권총 자세 상태(뷰모델 갱신 0.033초마다): 원하는 자세 = 정조준 ? 2 : 견착 ? 1 : 0, 바뀌면 전환 애니(T_xy) 재생 + Idle/Fire 를 그 자세 것으로
  B3 반동: 기존 반동 배율 × 무기 반동(표) × (권총 한손이면 1.5)
  B4 흔들림: 무기 배율, 정조준에서도 0.35배로 흔듦(전에는 정조준에서 안 흔듦)
  B5 1인칭 뷰모델이면 총구 효과를 VM_Muzzle 에서: BP_HistFlash(크기·길이), NS_MuzzleFlash(Global Scale 0.2×크기)
  B6 조준경: 뷰모델 전체 숨김 대신 조준경 몸통·유리 재질 슬롯만 가림(아래 총·손이 보임)
 -> Saved/HistFX.json("done": true)"""
import json, math, sys, traceback, uuid
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, STRINGS, PAWN, Graph, chain, wire, literal
from lyra_fpvm_animation_import import import_fbx, import_clip
ROOT = Path(unreal.Paths.project_dir()).resolve(); DATA = ROOT / 'FurinaSource' / 'Data'; R = {'steps': {}}
ASSETS = unreal.EditorAssetLibrary; EDIT = unreal.MaterialEditingLibrary; TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MAP = ENGINE + 'BlueprintMapLibrary:'; SYS = ENGINE + 'KismetSystemLibrary:'; GS = ENGINE + 'GameplayStatics:'
FX = '/Game/Furina/FX'
PISTOLS = ('p38', 'p08', 'pp')
PCLIPS = ('Idle', 'Fire', 'IdleS', 'FireS', 'IdleA', 'FireA', 'Reload', 'T_HS', 'T_SH', 'T_HA', 'T_AH', 'T_SA', 'T_AS')
MESHES = {'kar98k': ('Kar98k', 'Kar98k_Interior', 'kar98k'), 'kar98k_zf39': ('Kar98k', 'Kar98k_ZF39', 'kar98k'), 'kar98k_zf41': ('Kar98k', 'Kar98k_ZF41', 'kar98k'),
          'g43': ('G43', 'G43_Interior', 'g43'), 'g43_zf4': ('G43', 'G43_ZF4', 'g43'), 'p38': ('P38', 'P38', 'p38'), 'p08': ('P08', 'P08', 'p08'), 'pp': ('PP', 'PP', 'pp'),
          'mp40': ('MP40', 'MP40', 'mp40'), 'mp38': ('MP38', 'MP38', 'mp38'), 'stg44': ('STG44', 'STG44', 'stg44')}
TUBE_SLOTS = ('ZF39_Blued', 'ZF39_Glass', 'ZF41_Blued', 'ZF41_Glass', 'ZF4_Blued', 'ZF4_Glass')
MOUNT_SLOTS = ('Mount_K98_Blued', 'Mount_ZF41_Satin', 'Mount_ZF4_Phosphate')   # 뒤 고리가 렌즈 가운데를 흐리게 가려서 조준 중엔 함께 가림
LENS = {'ZF39': (4., .213, .026, .002, .013, 1.30), 'ZF41': (1.5, .165, .036, .0015, .010, 1.12), 'ZF4': (4., .207, .025, .0017, .011, 1.30)}


def step(name):
    def deco(fn):
        def run(*a):
            try: R['steps'][name] = fn(*a) or 'ok'
            except Exception: R['steps'][name] = 'ERROR ' + traceback.format_exc()[-1600:]; raise
            save()
            return R['steps'][name]
        return run
    return deco
def save(): (ROOT / 'Saved' / 'HistFX.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8')


# ------------------------------------------------------------------ A1
@step('A1_pistols')
def pistols():
    out = {}; rifle = unreal.load_asset('/Game/Furina/FPVM/Kar98k/SK_FPVM_Kar98k_Interior')
    for key in PISTOLS:
        name = key.upper(); folder = f'/Game/Furina/FPVM/{name}'; mesh_name = 'SK_FPVM_' + name
        import_fbx(mesh_name + '.fbx', folder, mesh_name, mesh=True, animations=False)
        mesh = unreal.load_asset(folder + '/' + mesh_name); skel = mesh.get_editor_property('skeleton')
        defaults = {str(s.material_slot_name): s.material_interface for s in rifle.materials}
        props = unreal.load_asset(f'/Game/Furina/Weapons/Germany/{key}/SM_DE_{key}')
        defaults.update({str(s.material_slot_name): s.material_interface for s in props.static_materials})
        mats = []
        for s in mesh.materials:
            m = defaults.get(str(s.material_slot_name))
            if m: s.material_interface = m
            mats.append(s)
        mesh.set_editor_property('materials', mats)
        clips = {c: import_clip(folder, skel, f'AS_FPVM_{name}_{c}') for c in PCLIPS}
        for a in (mesh, skel, *clips.values()): assert ASSETS.save_loaded_asset(a, False), a.get_name()
        out[key] = {c: round(a.get_play_length(), 3) for c, a in clips.items()}
    return out


# ------------------------------------------------------------------ A2
@step('A2_sockets')
def sockets():
    mz = json.loads((DATA / 'fpvm_muzzle.json').read_text(encoding='utf-8'))
    for k in PISTOLS: mz[k] = json.loads((DATA / f'fpvm_{k}_stances.json').read_text(encoding='utf-8'))['muzzle']
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); out = {}
    for key, (folder, name, src) in MESHES.items():
        mesh = unreal.load_asset(f'/Game/Furina/FPVM/{folder}/SK_FPVM_{name}'); m = mz[src]
        a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); c = a.get_component_by_class(unreal.SkeletalMeshComponent)
        T = c.get_socket_transform('VM_Gun', unreal.RelativeTransformSpace.RTS_COMPONENT)
        p = unreal.Vector(*m['ue_cam_cm']); fwd = unreal.Vector(*m['ue_fwd']); up = unreal.Vector(*m['ue_up'])
        loc = unreal.MathLibrary.inverse_transform_location(T, p)
        rot_cs = unreal.MathLibrary.make_rot_from_yz(fwd, up); rot = unreal.MathLibrary.inverse_transform_rotation(T, rot_cs)
        sock = mesh.find_socket('VM_Muzzle'); SL = unreal.get_default_object(unreal.SystemLibrary)   # 소켓 속성은 파이썬에서 읽기 전용 -> 이름으로 설정
        if not sock:
            sock = unreal.SkeletalMeshSocket(outer=mesh); SL.call_method('SetNamePropertyByName', (sock, 'SocketName', 'VM_Muzzle')); mesh.add_socket(sock, False)
        SL.call_method('SetNamePropertyByName', (sock, 'BoneName', 'VM_Gun')); SL.call_method('SetVectorPropertyByName', (sock, 'RelativeLocation', loc))
        SL.call_method('SetRotatorPropertyByName', (sock, 'RelativeRotation', rot))
        mesh.modify(); assert ASSETS.save_loaded_asset(mesh, False), name
        eas.destroy_actor(a)
        a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); c = a.get_component_by_class(unreal.SkeletalMeshComponent)
        chk = c.get_socket_transform('VM_Muzzle', unreal.RelativeTransformSpace.RTS_COMPONENT); eas.destroy_actor(a)
        out[key] = {'local': [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)], 'err_cm': round((chk.translation - p).length(), 3),
                    'fwd_dot': round(unreal.MathLibrary.get_right_vector(chk.rotation.rotator()).dot(fwd), 4)}
    return out


# ------------------------------------------------------------------ A3/A4 재질
def material(path, factory_name):
    folder, name = path.rsplit('/', 1)
    if ASSETS.does_asset_exist(path): m = unreal.load_asset(path); EDIT.delete_all_material_expressions(m); return m
    return TOOLS.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())

@step('A3_hidden')
def hidden():
    m = material(FX + '/M_FPVM_Hidden', '')
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED); m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    z = EDIT.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 0); z.set_editor_property('r', 0.0)
    assert EDIT.connect_material_property(z, '', unreal.MaterialProperty.MP_OPACITY_MASK)
    EDIT.recompile_material(m); assert ASSETS.save_loaded_asset(m, False)

LENS_CODE = r'''
float2 p = UV - 0.5;
float2 lens = float2(p.x * Viewport.x / Viewport.y, p.y);
float r = length(lens);
float pixel = 1.0 / Viewport.y;
float R = {radius};
float ringOut = R * {ring};
float fadeOut = ringOut + R * 0.32;
if (r > fadeOut) return Unfiltered;
if (r > R + pixel) {
    // 접안부 테두리(가까워서 흐릿한 검푸른 금속) -> 바깥은 원래 화면(아래 총·손)
    float t = saturate((r - R) / max(ringOut - R, 1e-4));
    float3 metal = float3(0.016, 0.017, 0.020) + 0.028 * saturate(-lens.y / max(r, 1e-4)) * (1.0 - t) + 0.010 * smoothstep(0.8, 1.0, t);
    float k = smoothstep(ringOut - R * 0.03, fadeOut, r);
    return lerp(metal, Unfiltered * lerp(0.45, 1.0, k), k);
}
float2 center = 0.5 + p / {power};
float2 spread = float2(1.0, 1.0) * (0.42 + 0.98 * smoothstep(0.0, R, r)) / Viewport;
float3 field = SceneTextureLookup(ViewportUVToSceneTextureUV(center, 14), 14, true).rgb;
float3 defocused = SceneTextureLookup(ViewportUVToSceneTextureUV(center + float2(spread.x, 0), 14), 14, true).rgb
                  + SceneTextureLookup(ViewportUVToSceneTextureUV(center - float2(spread.x, 0), 14), 14, true).rgb
                  + SceneTextureLookup(ViewportUVToSceneTextureUV(center + float2(0, spread.y), 14), 14, true).rgb
                  + SceneTextureLookup(ViewportUVToSceneTextureUV(center - float2(0, spread.y), 14), 14, true).rgb;
field = lerp(field, defocused * 0.25, 0.18);
// 렌즈 먼지(접안 렌즈 위 = 초점 밖이라 흐린 점, 대물 쪽 작은 점)와 기스(가는 직선 + 닦은 자국 호), 가장자리로 갈수록 많음
float2 q = lens / R; float rq = length(q); float pq = pixel / R;
float dust = 0.0;
[loop] for (int s = 0; s < 3; s++) {
    float cell = s == 0 ? 0.11 : (s == 1 ? 0.06 : 0.034);
    float2 g = floor(q / cell);
    [loop] for (int dx = -1; dx <= 1; dx++) {
        [loop] for (int dy = -1; dy <= 1; dy++) {
            float2 cc = g + float2(dx, dy) + s * 31.7 + {seed};
            float h1 = frac(sin(dot(cc, float2(127.1, 311.7))) * 43758.5453);
            float h2 = frac(sin(dot(cc, float2(269.5, 183.3))) * 43758.5453);
            float h3 = frac(sin(dot(cc, float2(419.2, 371.9))) * 43758.5453);
            float2 pos = (g + float2(dx, dy) + float2(h1, h2)) * cell;
            float w = smoothstep(0.45, 1.0, length(pos));
            if (h3 < 0.10 + 0.45 * w) {
                float size = cell * (0.05 + 0.10 * h1);
                float soft = s == 0 ? size * 1.6 : size * 0.5 + pq;
                float d = length(q - pos);
                dust = max(dust, (1.0 - smoothstep(size - soft, size + soft, d)) * (0.25 + 0.55 * h2));
            }
        }
    }
}
float scr = 0.0;
[loop] for (int i = 0; i < 12; i++) {
    float a = frac(sin(i * 12.9898 + 1.3 + {seed}) * 43758.5453);
    float b = frac(sin(i * 78.233 + 2.1 + {seed}) * 43758.5453);
    float c = frac(sin(i * 39.425 + 0.7 + {seed}) * 43758.5453);
    float ang = a * 6.2831853; float2 dir = float2(cos(ang), sin(ang));
    float2 ctr = float2(cos(b * 6.2831853), sin(b * 6.2831853)) * (0.30 + 0.62 * c);
    float2 dd = q - ctr; float along = dot(dd, dir); float across = abs(dot(dd, float2(-dir.y, dir.x)));
    float len = 0.06 + 0.30 * a;
    float wd = pq * (0.5 + 0.8 * c);
    float ln = (1.0 - smoothstep(wd * 0.5, wd * 1.5, across)) * (1.0 - smoothstep(len * 0.7, len, abs(along)));
    scr = max(scr, ln * (0.3 + 0.7 * b));
}
[loop] for (int j = 0; j < 5; j++) {
    float a = frac(sin(j * 93.989 + 4.1 + {seed}) * 43758.5453);
    float b = frac(sin(j * 17.231 + 9.7 + {seed}) * 43758.5453);
    float rad = 0.40 + 0.52 * a; float ang0 = b * 6.2831853; float ext = 0.25 + 0.55 * frac(a * 7.3);
    float ang = atan2(q.y, q.x); float da = abs(frac((ang - ang0) / 6.2831853 + 0.5) - 0.5) * 6.2831853;
    float ln = (1.0 - smoothstep(pq * 0.4, pq * 1.3, abs(rq - rad))) * (1.0 - smoothstep(ext * 0.8, ext, da));
    scr = max(scr, ln * 0.45);
}
float lum = dot(field, float3(0.3, 0.59, 0.11));
field = lerp(field, field * 0.45, saturate(dust * 0.75));
field += scr * (0.04 + 0.22 * lum);
field = lerp(field, lum * 1.05 + 0.02, 0.10 * smoothstep(0.55, 1.0, rq));
// 십자선(기존 고증 모양 그대로)
float2 cross = lens / (R * 2.0);
float arms = smoothstep({gap} - pixel, {gap} + pixel, abs(cross.x)) * (1.0 - smoothstep({line_width}, {line_width} + pixel, abs(cross.y)));
float width = {post_width} * saturate(cross.y / 0.065);
float post = smoothstep(0.0, pixel, cross.y) * (1.0 - smoothstep(width, width + pixel, abs(cross.x)));
field = lerp(field, float3(0.013, 0.014, 0.016), saturate(max(post, arms)));
float edge = smoothstep(R - 0.029, R, r);
field *= lerp(float3(1.0, 1.0, 1.0), float3(0.62, 0.68, 0.73), edge);
return field;
'''

@step('A4_lenses')
def lenses():
    out = {}
    for name, (power, radius, gap, lw, pw, ring) in LENS.items():
        path = f'/Game/Furina/FPVM/M_FPVM_LocalLens_{name}'
        m = unreal.load_asset(path); assert m, path
        EDIT.delete_all_material_expressions(m)
        screen = EDIT.create_material_expression(m, unreal.MaterialExpressionScreenPosition, -600, 0)
        size = EDIT.create_material_expression(m, unreal.MaterialExpressionViewSize, -600, 140)
        scene = EDIT.create_material_expression(m, unreal.MaterialExpressionSceneTexture, -600, 280); scene.set_editor_property('scene_texture_id', unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
        paint = EDIT.create_material_expression(m, unreal.MaterialExpressionCustom, -290, 0); paint.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        ins = []
        for pn in ('UV', 'Viewport', 'Unfiltered'):
            it = unreal.CustomInput(); it.set_editor_property('input_name', pn); ins.append(it)
        paint.set_editor_property('inputs', ins)
        code = LENS_CODE
        for k, v in dict(radius=radius, ring=ring, power=power, gap=gap, line_width=lw, post_width=pw, seed={'ZF39': 1.7, 'ZF41': 5.3, 'ZF4': 9.1}[name]).items():
            code = code.replace('{%s}' % k, repr(float(v)))
        paint.set_editor_property('code', code)
        for e, o, pn in ((screen, 'ViewportUV', 'UV'), (size, '', 'Viewport'), (scene, 'Color', 'Unfiltered')): assert EDIT.connect_material_expressions(e, o, paint, pn), pn
        assert EDIT.connect_material_property(paint, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        EDIT.recompile_material(m); assert ASSETS.save_loaded_asset(m, False); out[name] = 'ok'
    return out


# ------------------------------------------------------------------ A5 화염 액터
def subobjects(bp):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    return sub, lib, {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}

@step('A5_flash')
def flash():
    path = FX + '/BP_HistFlash'
    if not ASSETS.does_asset_exist(path): assert ASSETS.duplicate_asset('/Game/Furina/M4/BP_M4Flash', path)
    bp = unreal.load_asset(path); sub, lib, hs = subobjects(bp); off = []
    for nm in ('FlashPetalL', 'FlashPetalR', 'FlashPetalU', 'FlashPetalD', 'FlashStar'):   # M4 소염기(별 모양) 모양은 맨 총구인 독일 총에 없음
        c = lib.get_associated_object(lib.get_data(hs[nm])); c.set_editor_property('visible', False); c.set_editor_property('hidden_in_game', True); off.append(nm)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); assert ASSETS.save_loaded_asset(bp, False)
    return {'hidden': off}


# ------------------------------------------------------------------ A6 연기
SMOKE_WPO = r'''
float3 Fwd = normalize(TransformLocalVectorToWorld(Parameters, float3(0, 1, 0)));   // 총열 앞(액터 +Y)
float age = max(Age, 0.0); float a = saturate(age / max(Life, 0.1));   // Age: 액터(BP_HistSmoke)가 틱마다 넣는 경과 초(재질 시계와 BP 시계가 달라 직접 넘김)
float has = step(0.001, VC.r + VC.g + VC.b); float seed = lerp(0.5, VC.r, has); float ax = lerp(0.5, VC.g, has); float sz = lerp(0.8, VC.b, has);   // 정점색이 없으면 중간값
float grow = Size * sz * (1.2 + 3.5 * ax) * (1.0 + 4.0 * sqrt(a));
float dist = Size * (1.5 + 24.0 * ax) * (1.0 - exp(-5.0 * age));
float3 side = normalize(cross(Fwd, float3(0, 0, 1)) + float3(1e-4, 0, 0));
float3 drift = Fwd * dist + float3(0, 0, 1) * (3.0 * age + 2.5 * age * age) + side * (seed - 0.5) * 9.0 * a * Size;
return Rel * (grow - 1.0) + drift;
'''
SMOKE_OPA = r'''
float age = max(Age, 0.0); float a = saturate(age / max(Life, 0.1));   // Age: 액터(BP_HistSmoke)가 틱마다 넣는 경과 초(재질 시계와 BP 시계가 달라 직접 넘김)
float fadeIn = saturate(age / 0.05);
float fade = pow(1.0 - a, 1.7);
float edge = pow(saturate(abs(dot(normalize(N), normalize(V)))), 1.4);
float base = Density * (0.75 - 0.30 * saturate(VC.g));
return saturate(base * fade * fadeIn * edge * (0.55 + 0.45 * Noise));
'''

@step('A6_smoke')
def smoke():
    out = {}
    # 메시
    ui = unreal.FbxImportUI(); ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
    ui.static_mesh_import_data.set_editor_property('vertex_color_import_option', unreal.VertexColorImportOption.REPLACE)
    ui.static_mesh_import_data.set_editor_property('combine_meshes', True)
    t = unreal.AssetImportTask(); t.filename = str(ROOT / 'FurinaSource/FBX/FX/SM_HistSmokePuffs.fbx'); t.destination_path = FX; t.destination_name = 'SM_HistSmokePuffs'
    t.automated = True; t.replace_existing = True; t.options = ui; TOOLS.import_asset_tasks([t])
    mesh = unreal.load_asset(FX + '/SM_HistSmokePuffs'); assert mesh
    # 재질
    m = material(FX + '/M_HistSmoke', '')
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT); m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property('two_sided', False)
    def param(name, v, x, y):
        e = EDIT.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y); e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', v); return e
    spawn = param('Age', 0.0, -900, 0); life = param('Life', 2.5, -900, 80); dens = param('Density', 1.0, -900, 160); size = param('Size', 1.0, -900, 240)
    tm = EDIT.create_material_expression(m, unreal.MaterialExpressionTime, -900, 320)
    vc = EDIT.create_material_expression(m, unreal.MaterialExpressionVertexColor, -900, 400)
    wp = EDIT.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1200, 480)
    op = EDIT.create_material_expression(m, unreal.MaterialExpressionObjectPositionWS, -1200, 560)
    rel = EDIT.create_material_expression(m, unreal.MaterialExpressionSubtract, -950, 520)
    EDIT.connect_material_expressions(wp, '', rel, 'A'); EDIT.connect_material_expressions(op, '', rel, 'B')
    def custom(code, ins, otype, x, y):
        e = EDIT.create_material_expression(m, unreal.MaterialExpressionCustom, x, y); e.set_editor_property('output_type', otype)
        lst = []
        for nm in ins:
            it = unreal.CustomInput(); it.set_editor_property('input_name', nm); lst.append(it)
        e.set_editor_property('inputs', lst); e.set_editor_property('code', code); return e
    w = custom(SMOKE_WPO, ('Age', 'Life', 'Size', 'VC', 'Rel'), unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 300)
    for src, o, pn in ((spawn, '', 'Age'), (life, '', 'Life'), (size, '', 'Size'), (vc, '', 'VC'), (rel, '', 'Rel')): assert EDIT.connect_material_expressions(src, o, w, pn), pn
    assert EDIT.connect_material_property(w, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    nrm = EDIT.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -900, 760)
    cam = EDIT.create_material_expression(m, unreal.MaterialExpressionCameraVectorWS, -900, 840)
    nz = EDIT.create_material_expression(m, unreal.MaterialExpressionNoise, -900, 920)
    nz.set_editor_property('scale', 0.12); nz.set_editor_property('levels', 3); nz.set_editor_property('output_min', 0.0); nz.set_editor_property('output_max', 1.0)
    o = custom(SMOKE_OPA, ('Age', 'Life', 'Density', 'VC', 'N', 'V', 'Noise'), unreal.CustomMaterialOutputType.CMOT_FLOAT1, -500, 700)
    for src, ou, pn in ((spawn, '', 'Age'), (life, '', 'Life'), (dens, '', 'Density'), (vc, '', 'VC'), (nrm, '', 'N'), (cam, '', 'V'), (nz, '', 'Noise')): assert EDIT.connect_material_expressions(src, ou, o, pn), pn
    assert EDIT.connect_material_property(o, '', unreal.MaterialProperty.MP_OPACITY)
    col = EDIT.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -500, 100); col.set_editor_property('constant', unreal.LinearColor(0.80, 0.81, 0.84, 1))   # 무연 화약 연기: 옅은 회백색(2026-11-21: 0.34 는 밝은 하늘 앞에서 안 보였음)
    assert EDIT.connect_material_property(col, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    EDIT.recompile_material(m); assert ASSETS.save_loaded_asset(m, False)
    mesh.set_material(0, m); assert ASSETS.save_loaded_asset(mesh, False)
    # 액터
    path = FX + '/BP_HistSmoke'
    if not ASSETS.does_asset_exist(path):
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor); assert TOOLS.create_asset('BP_HistSmoke', FX, unreal.Blueprint, f)
    bp = unreal.load_asset(path); sub, lib, hs = subobjects(bp)
    if 'Puffs' not in hs:
        root = next(h for n, h in hs.items() if n not in ('None',) and lib.get_associated_object(lib.get_data(h)) and isinstance(lib.get_associated_object(lib.get_data(h)), unreal.SceneComponent)) if len(hs) > 1 else list(hs.values())[0]
        h, err = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.StaticMeshComponent, blueprint_context=bp)); assert not str(err), str(err)
        sub.rename_subobject(h, unreal.Text('Puffs')); sub, lib, hs = subobjects(bp)
    c = lib.get_associated_object(lib.get_data(hs['Puffs']))
    c.set_static_mesh(mesh); c.set_collision_profile_name('NoCollision'); c.set_editor_property('cast_shadow', False); c.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    c.set_editor_property('bounds_scale', 40.0)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'HS_Life' not in nodes:
        begin = ed.find_event_node('ReceiveBeginPlay') or unreal.BlueprintEditorLibrary.add_event_override(bp, 'ReceiveBeginPlay', unreal.IntPoint(0, 0)); assert begin
        def fn(name, path):
            n = ed.add_call_function_node(path); assert n, path; n.rename(name); return n
        sc = fn('HS_Scale', '/Script/Engine.Actor:GetActorScale3D'); br = fn('HS_Break', MATH + 'BreakVector')
        wire(sc.find_result_pin(), br.find_input_pin('InVec'))
        reset = fn('HS_Reset', '/Script/Engine.Actor:SetActorScale3D'); literal(reset, 'NewScale3D', '1,1,1')
        lifeN = fn('HS_Life', '/Script/Engine.Actor:SetLifeSpan'); wire(br.find_output_pin('Y'), lifeN.find_input_pin('InLifespan'))
        comp = ed.add_get_member_variable_node('Puffs', ''); mid = fn('HS_MID', '/Script/Engine.PrimitiveComponent:CreateDynamicMaterialInstance')
        wire(comp.find_output_pin('Puffs'), mid.find_self_pin()); literal(mid, 'ElementIndex', 0)
        now = fn('HS_Now', GS + 'GetTimeSeconds')
        sets = []
        for pname, src in (('Spawn', now.find_result_pin()), ('Density', br.find_output_pin('X')), ('Life', br.find_output_pin('Y')), ('Size', br.find_output_pin('Z'))):
            s = fn('HS_Set' + pname, '/Script/Engine.MaterialInstanceDynamic:SetScalarParameterValue'); wire(mid.find_result_pin(), s.find_self_pin())
            literal(s, 'ParameterName', pname); wire(src, s.find_input_pin('Value')); sets.append(s)
        tail = begin.find_then_pin()
        for n in [reset, lifeN, mid] + sets:
            wire(tail, n.find_execute_pin()); tail = n.find_then_pin()
        out['graph'] = 'added'
    api = unreal.BlueprintEditorLibrary; have = {str(n) for n in api.list_member_variable_names(bp)}
    if 'SmokeMID' not in have: assert api.add_member_variable(bp, 'SmokeMID', api.get_object_reference_type(unreal.MaterialInstanceDynamic))
    if 'SmokeAge' not in have: assert api.add_member_variable(bp, 'SmokeAge', api.get_basic_type_by_name('real'))
    api.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'HS_TickSet' not in nodes:
        mid = nodes['HS_MID']; t = mid.find_then_pin(); old_ = list(t.list_connected_pins()); t.break_pin_links()
        keep = ed.add_set_member_variable_node('SmokeMID'); keep.rename('HS_KeepMID'); wire(mid.find_result_pin(), keep.find_input_pin('SmokeMID')); wire(t, keep.find_execute_pin())
        for q in old_: wire(keep.find_then_pin(), q)
        tick = ed.find_event_node('ReceiveTick') or api.add_event_override(bp, 'ReceiveTick', unreal.IntPoint(0, 600)); assert tick
        add = ed.add_call_function_node(MATH + 'Add_DoubleDouble'); add.rename('HS_TickAdd')
        wire(ed.add_get_member_variable_node('SmokeAge', '').find_output_pin('SmokeAge'), add.find_input_pin('A')); wire(tick.find_output_pin('DeltaSeconds'), add.find_input_pin('B'))
        st_ = ed.add_set_member_variable_node('SmokeAge'); st_.rename('HS_TickSet'); wire(add.find_result_pin(), st_.find_input_pin('SmokeAge')); wire(tick.find_then_pin(), st_.find_execute_pin())
        sp_ = ed.add_call_function_node('/Script/Engine.MaterialInstanceDynamic:SetScalarParameterValue'); sp_.rename('HS_TickParam')
        wire(ed.add_get_member_variable_node('SmokeMID', '').find_output_pin('SmokeMID'), sp_.find_self_pin()); literal(sp_, 'ParameterName', 'Age')
        wire(st_.find_output_pin('Output_Get'), sp_.find_input_pin('Value')); wire(st_.find_then_pin(), sp_.find_execute_pin())
        out['tick'] = 'added'
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); out['status'] = str(bp.get_editor_property('status'))
    assert bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR; assert ASSETS.save_loaded_asset(bp, False)
    return out


# ------------------------------------------------------------------ B 캐릭터 BP
def map_type(value_cat, value_obj=None):
    t = unreal.EdGraphPinType()
    sub = f',TerminalSubCategoryObject="{value_obj}"' if value_obj else ''
    assert t.import_text(f'(PinCategory="string",PinValueType=(TerminalCategory="{value_cat}"{sub}),ContainerType=Map)'); return t

@step('B0_vars')
def variables(pawn):
    api = unreal.BlueprintEditorLibrary; have = {str(n) for n in api.list_member_variable_names(pawn)}
    want = {'FurinaPAnims': map_type('object', '/Script/Engine.AnimSequence'), 'FurinaFXTable': map_type('struct', '/Script/CoreUObject.Vector'),
            'FurinaFXTable2': map_type('struct', '/Script/CoreUObject.Vector'), 'FurinaPStance': api.get_basic_type_by_name('int'), 'FurinaScopeTubeHidden': api.get_basic_type_by_name('bool')}
    for k, t in want.items():
        if k not in have: assert api.add_member_variable(pawn, k, t), k
    api.compile_blueprint(pawn)
    cdo = unreal.get_default_object(pawn.generated_class())
    anims = unreal.Map(str, unreal.AnimSequence)
    for key in PISTOLS:
        n = key.upper()
        for c in PCLIPS: anims[f'{key}_{c}'] = unreal.load_asset(f'/Game/Furina/FPVM/{n}/AS_FPVM_{n}_{c}')
    fx = json.loads((DATA / 'hist_fx.json').read_text(encoding='utf-8'))['weapons']
    t1 = unreal.Map(str, unreal.Vector); t2 = unreal.Map(str, unreal.Vector)
    for k, v in fx.items():
        t1[k] = unreal.Vector(v['recoil'], v['shake'], v['flash']); t2[k] = unreal.Vector(v['flash_len'], v['smoke'], v['smoke_life'])
    cdo.set_editor_property('FurinaPAnims', anims); cdo.set_editor_property('FurinaFXTable', t1); cdo.set_editor_property('FurinaFXTable2', t2)
    return {'anims': len(anims), 'fx': len(t1), 'has_last_key': 'FurinaVMLastKey' in have}

def keyvar(pawn):
    have = {str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(pawn)}
    return 'FurinaVMLastKey' if 'FurinaVMLastKey' in have else 'FurinaPrimaryKey'

@step('B_graph')
def graph(pawn):
    g = Graph(pawn, 'HFX_'); out = {}
    if 'HFX_PStanceReset' in g.nodes: return 'already installed'
    KEY = keyvar(pawn); out['key_var'] = KEY
    val = lambda n: n.find_result_pin()
    def find(name, table, key): return g.call(name, MAP + 'Map_Find', TargetMap=g.get(table), Key=key)
    def concat(name, a, b): return val(g.call(name, STRINGS + 'Concat_StrStr', A=a, B=b))
    def AND(name, a, b): return val(g.call(name, MATH + 'BooleanAND', A=a, B=b))
    def NOT(name, a): return val(g.call(name, MATH + 'Not_PreBool', A=a))
    def active(name, comp): return val(g.call(name, ENGINE + 'ActorComponent:IsActive', target=g.get(comp)))
    def now(name): return val(g.call(name, GS + 'GetTimeSeconds'))
    def splice(src_then, nodes):   # src_then 뒤에 nodes(실행)를 끼움
        old = list(src_then.list_connected_pins()); src_then.break_pin_links(); tail = chain(src_then, nodes)
        for t in old: wire(tail, t)
        return old
    # B1 무기 바뀔 때 자세 0
    splice(g.locate('VW_S_7_').find_then_pin(), [g.store('PStanceReset', 'FurinaPStance', 0)])
    # B2 권총 자세 상태
    ads = active('AdsOn', 'FurinaADS'); sh = val(g.call('ShOn', MATH + 'BooleanOR', A=active('ShA', 'FurinaShoulder'), B=active('ShB', 'FurinaShoulderAuto')))
    want = val(g.call('Want', MATH + 'SelectInt', A=2, B=val(g.call('WantSh', MATH + 'SelectInt', A=1, B=0, bPickA=sh)), bPickA=ads))
    key = g.get(KEY); isP = find('IsPistolFind', 'FurinaPAnims', concat('IsPistolKey', key, '_IdleS')).find_output_pin('ReturnValue')
    adsset = next(n for nm, n in g.nodes.items() if nm.startswith('VM_AdsSet_')); thenp = adsset.find_then_pin(); cont = list(thenp.list_connected_pins()); thenp.break_pin_links()
    brP = g.branch('PistolBranch', isP); wire(thenp, brP.find_execute_pin())
    brRl = g.branch('PistolReloading', g.get('FurinaReloading')); wire(brP.find_then_pin(), brRl.find_execute_pin())
    def letter(name, i): return val(g.call(name, MATH + 'SelectString', A='A', B=val(g.call(name + 'S', MATH + 'SelectString', A='S', B='H', bPickA=val(g.call(name + 'Eq1', MATH + 'EqualEqual_IntInt', A=i, B=1)))), bPickA=val(g.call(name + 'Eq2', MATH + 'EqualEqual_IntInt', A=i, B=2))))
    def suffix(name, i): return val(g.call(name, MATH + 'SelectString', A='A', B=val(g.call(name + 'S', MATH + 'SelectString', A='S', B='', bPickA=val(g.call(name + 'Eq1', MATH + 'EqualEqual_IntInt', A=i, B=1)))), bPickA=val(g.call(name + 'Eq2', MATH + 'EqualEqual_IntInt', A=i, B=2))))
    # 재장전 중: 자세 0, 비조준 애니
    rl_nodes = [g.store('RlStance', 'FurinaPStance', 0),
                g.store('RlIdle', 'FurinaVMAnimIdle', find('RlIdleFind', 'FurinaPAnims', concat('RlIdleKey', g.get(KEY), '_Idle')).find_output_pin('Value')),
                g.store('RlFire', 'FurinaVMAnimFire', find('RlFireFind', 'FurinaPAnims', concat('RlFireKey', g.get(KEY), '_Fire')).find_output_pin('Value'))]
    tail_rl = chain(brRl.find_then_pin(), rl_nodes)
    differ = val(g.call('Differ', MATH + 'NotEqual_IntInt', A=want, B=g.get('FurinaPStance')))
    free = val(g.call('Free', MATH + 'Greater_DoubleDouble', A=now('NowP'), B=g.get('FurinaVMBusy')))
    brT = g.branch('NeedTransition', AND('DifferFree', differ, free)); wire(brRl.find_else_pin(), brT.find_execute_pin())
    cur = g.get('FurinaPStance')
    tkey = concat('TKey3', concat('TKey2', concat('TKey1', g.get(KEY), '_T_'), letter('FromL', cur)), letter('ToL', want))
    tfind = find('TFind', 'FurinaPAnims', tkey); tanim = tfind.find_output_pin('Value')
    play = g.call('PlayT', ENGINE + 'SkeletalMeshComponent:PlayAnimation', target=g.get('FurinaFPVM'), NewAnimToPlay=tanim, bLooping=False)
    try: tlen = val(g.call('TLen', ENGINE + 'AnimSequenceBase:GetPlayLength', target=tanim))
    except Exception: tlen = 0.25; out['tlen'] = 'fixed 0.25'
    busy = g.store('TBusy', 'FurinaVMBusy', val(g.call('TEnd', MATH + 'Add_DoubleDouble', A=now('NowT'), B=tlen)))
    idle0 = g.store('TIdleFlag', 'FurinaVMIdle', False)
    suf = suffix('Suf', want)
    setI = g.store('TIdle', 'FurinaVMAnimIdle', find('TIdleFind', 'FurinaPAnims', concat('TIdleKey', concat('TIdleK0', g.get(KEY), '_Idle'), suf)).find_output_pin('Value'))
    setF = g.store('TFire', 'FurinaVMAnimFire', find('TFireFind', 'FurinaPAnims', concat('TFireKey', concat('TFireK0', g.get(KEY), '_Fire'), suf)).find_output_pin('Value'))
    setS = g.store('TStance', 'FurinaPStance', want)
    tail_t = chain(brT.find_then_pin(), [play, busy, idle0, setI, setF, setS])
    for t in cont:
        for e in (brP.find_else_pin(), tail_rl, brT.find_else_pin(), tail_t): wire(e, t)
    out['pistol_cont'] = [t.get_owning_node().get_name() for t in cont]
    # 공통: 무기 표 조회(1인칭 뷰모델일 때만)
    vmon = g.get('FurinaVMOn')
    def fxrow(name, table):
        f = find(name + 'Find', table, g.get(KEY)); ok = AND(name + 'Ok', f.find_output_pin('ReturnValue'), g.get('FurinaVMOn'))
        b = g.call(name + 'Break', MATH + 'BreakVector', InVec=f.find_output_pin('Value')); return ok, b
    # B3 반동
    ok1, b1 = fxrow('Rec', 'FurinaFXTable')
    rs = val(g.call('RecScale', MATH + 'SelectFloat', A=b1.find_output_pin('X'), B=1.0, bPickA=ok1))
    pist = AND('RecPistol', find('RecPFind', 'FurinaPAnims', concat('RecPKey', g.get(KEY), '_IdleS')).find_output_pin('ReturnValue'), g.get('FurinaVMOn'))
    onehand = val(g.call('RecOneHand', MATH + 'SelectFloat', A=1.5, B=1.0, bPickA=AND('RecOneHandOn', pist, NOT('RecNotAds', active('RecAds', 'FurinaADS')))))
    mul = val(g.call('RecMul', MATH + 'Multiply_DoubleDouble', A=rs, B=onehand))
    gi = g.nodes['FPN_RecGainInit'].find_result_pin(); targets = list(gi.list_connected_pins()); gi.break_pin_links()
    m2 = val(g.call('RecApply', MATH + 'Multiply_DoubleDouble', A=gi, B=mul))
    for t in targets: wire(m2, t)
    out['recoil_targets'] = [t.get_owning_node().get_name() for t in targets]
    # B4 흔들림
    ok2, b2 = fxrow('Shk', 'FurinaFXTable')
    ss = val(g.call('ShkScale', MATH + 'SelectFloat', A=b2.find_output_pin('Y'), B=1.0, bPickA=ok2))
    wire(ss, g.nodes['FPN_ShkStart'].find_input_pin('Scale'))
    shk_br = g.nodes['FPN_ShkBr']; els = shk_br.find_else_pin(); after_else = list(els.list_connected_pins()); els.break_pin_links()
    shk_ads = g.call('ShkAds', ENGINE + 'PlayerCameraManager:StartCameraShake', target=g.nodes['K2Node_FPF_CamMgr'].find_result_pin(),
                     ShakeClass='/Game/Furina/CameraShakes/CS_FurinaShot.CS_FurinaShot_C', Scale=val(g.call('ShkAdsScale', MATH + 'Multiply_DoubleDouble', A=ss, B=0.35)))
    wire(els, shk_ads.find_execute_pin())
    # B5 총구 효과: 뷰모델이면 VM_Muzzle 에서
    flash_spawn = g.nodes['M4_FlashSpawn']; ins = list(flash_spawn.find_execute_pin().list_connected_pins())
    for p in ins: p.break_pin_links()
    brF = g.branch('FxBranch', vmon)
    for p in ins + [shk_ads.find_then_pin()]: wire(p, brF.find_execute_pin())
    wire(brF.find_else_pin(), flash_spawn.find_execute_pin())
    ok3, b3 = fxrow('Fx', 'FurinaFXTable'); ok4, b4 = fxrow('Fx2', 'FurinaFXTable2')
    fs = val(g.call('FlashSize', MATH + 'SelectFloat', A=b3.find_output_pin('Z'), B=0.6, bPickA=ok3))
    fl = val(g.call('FlashLen', MATH + 'SelectFloat', A=b4.find_output_pin('X'), B=0.8, bPickA=ok4))
    st = g.call('Muzzle', ENGINE + 'SceneComponent:GetSocketTransform', target=g.get('FurinaFPVM'), InSocketName='VM_Muzzle')
    bt = g.call('MuzzleBreak', MATH + 'BreakTransform', InTransform=st.find_result_pin())
    loc, rot = bt.find_output_pin('Location'), bt.find_output_pin('Rotation')
    fscale = val(g.call('FlashScaleV', MATH + 'MakeVector', X=fs, Y=val(g.call('FlashLenMul', MATH + 'Multiply_DoubleDouble', A=fs, B=fl)), Z=fs))
    fxf = val(g.call('FlashXf', MATH + 'MakeTransform', Location=loc, Rotation=rot, Scale=fscale))
    sp = g.call('FlashSpawn', GS + 'BeginDeferredActorSpawnFromClass', ActorClass=FX + '/BP_HistFlash.BP_HistFlash_C', SpawnTransform=fxf, CollisionHandlingOverride='AlwaysSpawn')
    fin = g.call('FlashFinish', GS + 'FinishSpawningActor', Actor=sp.find_result_pin(), SpawnTransform=fxf)
    ns_rot = val(g.call('NSRot', MATH + 'ComposeRotators', A='0,90,0', B=rot))
    ns = g.call('NSSpawn', '/Script/Niagara.NiagaraFunctionLibrary:SpawnSystemAtLocation', SystemTemplate='/Game/NiagaraExamples/FX_Weapons/MuzzleFlashes/NS_MuzzleFlash.NS_MuzzleFlash',
                Location=loc, Rotation=ns_rot)
    nsg = g.call('NSScale', '/Script/Niagara.NiagaraComponent:SetVariableFloat', target=ns.find_result_pin(), InVariableName='Global Scale', InValue=val(g.call('NSScaleV', MATH + 'Multiply_DoubleDouble', A=fs, B=0.2)))
    nsb = g.call('NSShell', '/Script/Niagara.NiagaraComponent:SetVariableBool', target=ns.find_result_pin(), InVariableName='Use Bullet Shell', InValue=False)
    tail = chain(brF.find_then_pin(), [sp, fin, ns, nsg, nsb])
    after_fns = list(g.nodes['FNS_SetUseShell'].find_then_pin().list_connected_pins())
    for t in after_fns: wire(tail, t)
    out['fx_after'] = [t.get_owning_node().get_name() for t in after_fns]; out['flash_in'] = [p.get_owning_node().get_name() for p in ins]
    # B6 조준경: 뷰모델은 보이게, 조준경 몸통·유리 슬롯만 가림
    hide = g.nodes['ScopeView_HideViewmodel']; nh = hide.find_input_pin('NewHidden'); src = list(nh.list_connected_pins())[0]; nh.break_pin_links(); literal(hide, 'NewHidden', False)
    chg = g.branch('TubeChanged', val(g.call('TubeNe', MATH + 'NotEqual_BoolBool', A=src, B=g.get('FurinaScopeTubeHidden'))))
    on = g.branch('TubeOn', src); wire(chg.find_then_pin(), on.find_execute_pin())
    hid = unreal.load_asset(FX + '/M_FPVM_Hidden')
    t_on = chain(on.find_then_pin(), [g.call('TubeHide_' + s, ENGINE + 'PrimitiveComponent:SetMaterialByName', target=g.get('FurinaFPVM'), MaterialSlotName=s, Material=hid) for s in TUBE_SLOTS])
    t_off = chain(on.find_else_pin(), [g.call('TubeShow_' + s, ENGINE + 'PrimitiveComponent:SetMaterialByName', target=g.get('FurinaFPVM'), MaterialSlotName=s) for s in TUBE_SLOTS])
    keep = g.store('TubeState', 'FurinaScopeTubeHidden', src); wire(t_on, keep.find_execute_pin()); wire(t_off, keep.find_execute_pin())
    hthen = hide.find_then_pin(); nxt = list(hthen.list_connected_pins()); hthen.break_pin_links(); wire(hthen, chg.find_execute_pin())
    for t in nxt: wire(keep.find_then_pin(), t); wire(chg.find_else_pin(), t)
    out['scope_next'] = [t.get_owning_node().get_name() for t in nxt]
    return out


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    if not ASSETS.does_directory_exist(FX): ASSETS.make_directory(FX)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try:
        skip = set(sys.argv[1].split('+')) if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') and sys.argv[1] != 'all' else set()
        if 'A1' not in skip: pistols()
        if 'A2' not in skip: sockets()
        hidden(); lenses(); flash(); smoke()
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
    pawn = unreal.load_asset(PAWN); variables(pawn); graph(pawn)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn); R['pawn_status'] = str(pawn.get_editor_property('status'))
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR, 'pawn compile error'
    R['pawn_saved'] = bool(ASSETS.save_loaded_asset(pawn, False))

if __name__ == '__main__':
    try: main()
    except Exception: R['error'] = traceback.format_exc()[-2000:]
    R['done'] = True; save(); print('HIST_FX', R.get('error', 'ok')[-300:])
