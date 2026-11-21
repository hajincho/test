"""에디터(편집 전용, 2026-11-21): 조준경 '화면 속 화면' + 총구 연기 끄기 + 권총 탄창 재장전 반영
 1) 조준경: 화면 전체 후처리 확대(LocalLens) 대신, 정조준 화면(시야 60°)은 그대로 두고 조준경 유리(ZF39/ZF41/ZF4_Glass 슬롯)에만
    별도 장면 캡처(FurinaScopeCapture, 시야 = 2·atan(tan30°/배율): 4배 16.4°, 1.5배 42.1°)를 화면 좌표로 붙임(RT_FurinaScope).
    조준경 몸통·받침은 보이게 둠(작게 보여도 됨: 눈-접안부 ZF39 15, ZF4 11, ZF41 30cm). 십자선·먼지·기스·가장자리 어둡게는 유리 재질에서.
    뷰모델은 캡처에서 빠짐(hidden_in_scene_capture). 캡처는 조준경 조준 중에만 매 프레임.
 2) 총구 연기(BP_HistSmoke) 생성을 끊음(사용자: 지금은 비활성화). 화염은 그대로.
 3) 권총 P38/P08/PP: 실제 탄창 부품을 뗀 메시 + 클립 13개 다시 가져오기, VM_Muzzle 소켓, 재장전 길이 2.5초, 재장전 중 뷰모델 앞 6·아래 2cm
 -> Saved/ScopePIP.json("done": true)"""
import json, math, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, PAWN, Graph, chain, wire, literal, view_transform
import lyra_hist_fx as H
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
ASSETS = unreal.EditorAssetLibrary; EDIT = unreal.MaterialEditingLibrary; TOOLS = unreal.AssetToolsHelpers.get_asset_tools(); SYS = ENGINE + 'KismetSystemLibrary:'
FX = '/Game/Furina/FX'; RT_PATH = {4.0: FX + '/RT_FurinaScope', 1.5: FX + '/RT_FurinaScope15'}   # 배율별 캡처(시야가 고정 속성이라 BP 에서 못 바꿔 둘로 나눔)
# 접안 렌즈 반지름(cm) / 눈-접안부 거리(cm) = K. ZF39 ·ZF4 는 de_scoped_build.json lens_disc_r, ZF41 은 접안부 관 안쪽 0.80cm(유리 원판, fpvm_receiver_interior.py)
OPTICS = {'ZF39': dict(K=1.638 / 15.0, power=4.0, gap=.026, line=.002, post=.013, seed=1.7),
          'ZF41': dict(K=0.80 / 30.0, power=1.5, gap=.036, line=.0015, post=.010, seed=5.3),
          'ZF4': dict(K=0.9 / 11.0, power=4.0, gap=.025, line=.0017, post=.011, seed=9.1)}
FOV = {p: 2 * math.degrees(math.atan(math.tan(math.radians(30)) / p)) for p in (4.0, 1.5)}

GLASS_CODE = r'''
float aspect = Viewport.x / Viewport.y;
float2 p = UV - 0.5;
float2 lens = float2(p.x * aspect, p.y);
float R = {K} * 0.5 * aspect / tan(radians(30.0));   // 접안 렌즈가 화면에서 차지하는 반지름(세로 높이 단위), 정조준 가로 시야 60°
float r = length(lens); float pixel = 1.0 / Viewport.y;
float2 q = lens / R; float rq = length(q); float pq = pixel / R;
float3 field = Col;
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
                dust = max(dust, (1.0 - smoothstep(size - soft, size + soft, length(q - pos))) * (0.25 + 0.55 * h2));
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
    float len = 0.06 + 0.30 * a; float wd = pq * (0.5 + 0.8 * c);
    scr = max(scr, (1.0 - smoothstep(wd * 0.5, wd * 1.5, across)) * (1.0 - smoothstep(len * 0.7, len, abs(along))) * (0.3 + 0.7 * b));
}
float lum = dot(field, float3(0.3, 0.59, 0.11));
field = lerp(field, field * 0.45, saturate(dust * 0.75));
field += scr * (0.04 + 0.22 * lum);
field = lerp(field, lum * 1.05 + 0.02, 0.10 * smoothstep(0.55, 1.0, rq));
float2 cross = lens / (R * 2.0);
float arms = smoothstep({gap} - pixel, {gap} + pixel, abs(cross.x)) * (1.0 - smoothstep({line}, {line} + pixel, abs(cross.y)));
float width = {post} * saturate(cross.y / 0.065);
float post = smoothstep(0.0, pixel, cross.y) * (1.0 - smoothstep(width, width + pixel, abs(cross.x)));
field = lerp(field, float3(0.013, 0.014, 0.016), saturate(max(post, arms)));
field *= lerp(1.0, 0.08, smoothstep(0.78, 1.02, rq));   // 눈 위치 가장자리 그늘(접안부 테두리 안쪽)
return field;
'''


def make_rt(power):
    path = RT_PATH[power]
    if ASSETS.does_asset_exist(path): return unreal.load_asset(path)
    rt = TOOLS.create_asset(path.rsplit('/', 1)[1], FX, unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
    rt.set_editor_property('size_x', 1280); rt.set_editor_property('size_y', 720)
    rt.set_editor_property('render_target_format', unreal.TextureRenderTargetFormat.RTF_RGBA16F)
    assert ASSETS.save_loaded_asset(rt, False); return rt


def glass_materials(rts):
    out = {}
    for name, o in OPTICS.items():
        path = f'{FX}/M_FPVM_ScopeGlass_{name}'
        m = unreal.load_asset(path) if ASSETS.does_asset_exist(path) else TOOLS.create_asset(f'M_FPVM_ScopeGlass_{name}', FX, unreal.Material, unreal.MaterialFactoryNew())
        EDIT.delete_all_material_expressions(m); m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
        m.set_editor_property('used_with_skeletal_mesh', True)
        m.set_editor_property('two_sided', True)   # 렌즈 면 일부가 눈 반대쪽을 향해(원본 ZF41) 한쪽만 그리면 고리처럼 비었음. 화면 좌표라 겹쳐도 같은 그림   # 뷰모델(스켈레탈 메시)에 런타임으로 넣으므로 필요(없으면 기본 격자 재질로 보였음)
        sp = EDIT.create_material_expression(m, unreal.MaterialExpressionScreenPosition, -800, 0)
        ts = EDIT.create_material_expression(m, unreal.MaterialExpressionTextureSample, -550, 0); ts.set_editor_property('texture', rts[o['power']])
        ts.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        assert EDIT.connect_material_expressions(sp, 'ViewportUV', ts, 'UVs')
        vs = EDIT.create_material_expression(m, unreal.MaterialExpressionViewSize, -800, 200)
        cu = EDIT.create_material_expression(m, unreal.MaterialExpressionCustom, -250, 0); cu.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        ins = []
        for pn in ('Col', 'UV', 'Viewport'):
            it = unreal.CustomInput(); it.set_editor_property('input_name', pn); ins.append(it)
        cu.set_editor_property('inputs', ins)
        code = GLASS_CODE
        for k, v in o.items(): code = code.replace('{%s}' % k, repr(float(v)))
        cu.set_editor_property('code', code)
        assert EDIT.connect_material_expressions(ts, 'RGB', cu, 'Col'); assert EDIT.connect_material_expressions(sp, 'ViewportUV', cu, 'UV'); assert EDIT.connect_material_expressions(vs, '', cu, 'Viewport')
        assert EDIT.connect_material_property(cu, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        EDIT.recompile_material(m); assert ASSETS.save_loaded_asset(m, False); out[name] = m
    return out


CAPS = {4.0: 'FurinaScopeCapture4', 1.5: 'FurinaScopeCapture15'}
def capture_component(pawn, rts):
    sub, lib, hs = H.subobjects(pawn)
    for power, name in CAPS.items():
        if name not in hs:
            h, err = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs['FPCamera'], new_class=unreal.SceneCaptureComponent2D, blueprint_context=pawn)); assert not str(err), str(err)
            sub.rename_subobject(h, unreal.Text(name)); sub, lib, hs = H.subobjects(pawn)
        c = lib.get_associated_object(lib.get_data(hs[name]))
        c.set_editor_property('texture_target', rts[power]); c.set_editor_property('capture_every_frame', False); c.set_editor_property('capture_on_movement', False)
        c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_HDR); c.set_editor_property('fov_angle', FOV[power])
    vm = lib.get_associated_object(lib.get_data(hs['FurinaFPVM'])); vm.set_editor_property('hidden_in_scene_capture', True)
    return {'fov': FOV}


def graph(pawn, glass):
    g = Graph(pawn, 'PIP_'); out = {}
    if 'PIP_GlassZF39' in g.nodes: return 'already installed'
    # 1) 화면 전체 후처리 렌즈 끄기
    for nm in ('LocalLens_ZF39_Weight', 'LocalLens_ZF41_Weight', 'LocalLens_ZF4_Weight'):
        if nm in g.nodes: literal(g.nodes[nm], 'A', 0.0); out.setdefault('lens_off', []).append(nm)
    # 2) 조준 중: 유리만 캡처 재질, 몸통·받침은 그대로 + 캡처 켜기/끄기·시야
    on = g.nodes['HFX_TubeOn']; t = on.find_then_pin(); t.break_pin_links()
    nodes = [g.call('Glass' + n, ENGINE + 'PrimitiveComponent:SetMaterialByName', target=g.get('FurinaFPVM'), MaterialSlotName=n + '_Glass', Material=glass[n]) for n in ('ZF39', 'ZF41', 'ZF4')]
    tail = chain(t, nodes); wire(tail, g.nodes['HFX_TubeState'].find_execute_pin())
    # 조준경 조준 중이면 매 프레임(Event Tick 흐름) 배율에 맞는 캡처 한 장
    setcam = g.nodes['ScopeView_SetCamera'].find_execute_pin(); srcs = list(setcam.list_connected_pins()); setcam.break_pin_links()
    can = g.nodes['ScopeView_CanDraw'].find_result_pin()
    brS = g.branch('Scoped', can)
    for p in srcs: wire(p, brS.find_execute_pin())
    two = g.call('Two', SYS + 'MakeLiteralDouble', Value=2.0).find_result_pin()
    hi = g.call('HighPower', MATH + 'Greater_DoubleDouble', A=g.get('FurinaScopeZoom'), B=two).find_result_pin()
    brP = g.branch('Power4', hi); wire(brS.find_then_pin(), brP.find_execute_pin())
    c4 = g.call('Capture4', ENGINE + 'SceneCaptureComponent2D:CaptureScene', target=g.get(CAPS[4.0])); c15 = g.call('Capture15', ENGINE + 'SceneCaptureComponent2D:CaptureScene', target=g.get(CAPS[1.5]))
    wire(brP.find_then_pin(), c4.find_execute_pin()); wire(brP.find_else_pin(), c15.find_execute_pin())
    for e in (c4.find_then_pin(), c15.find_then_pin(), brS.find_else_pin()): wire(e, setcam)
    out['capture_from'] = [p.get_owning_node().get_name() for p in srcs]
    # 3) 연기 끄기: 화염(NS) 다음 바로 원래 흐름으로
    ns = g.nodes['HFX_NSShell'].find_then_pin(); after = [p for p in g.nodes['HFX_SmokeFinish'].find_then_pin().list_connected_pins()]
    ns.break_pin_links()
    for p in after: wire(ns, p)
    out['smoke_bypass_to'] = [p.get_owning_node().get_name() for p in after]
    # 4) 권총 재장전 길이 2.5초
    for key in ('p38', 'p08', 'pp'):
        for nm, var in ((f'HistoryPrimary_ReloadTime_{key.upper()}', 'FurinaVMReloadLen'), (f'HistoryReload_Duration_{key}_0', 'FurinaVMReloadLen')):
            if nm in g.nodes: literal(g.nodes[nm], var, 2.5); out.setdefault('reload_len', []).append(nm)
    return out


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try: R['pistols'] = 'skip' if 'nopistol' in sys.argv else H.pistols()
    finally: unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
    R['sockets'] = H.sockets()
    rts = {p: make_rt(p) for p in (4.0, 1.5)}; glass = glass_materials(rts)
    pawn = unreal.load_asset(PAWN)
    R['capture'] = capture_component(pawn, rts)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
    R['graph'] = graph(pawn, glass)
    # 조준경 정조준 값(눈-접안부 거리 바꿈) + 권총 재장전 구도 오프셋
    g = Graph(pawn)
    for key, optic in (('kar98k_zf39', 'ZF39'), ('kar98k_zf41', 'ZF41'), ('g43_zf4', 'ZF4')):
        loc, rot = view_transform(key); literal(g.nodes['ScopeView_Loc_' + optic], 'FurinaVMAdsLoc', loc); literal(g.nodes['ScopeView_Rot_' + optic], 'FurinaVMAdsRot', rot); R.setdefault('ads', {})[key] = loc
    cdo = unreal.get_default_object(pawn.generated_class()); m = cdo.get_editor_property('FurinaRlOfs')
    for k in ('p38', 'p08', 'pp'): m[k] = unreal.Vector(6.0, 0.0, -2.0)
    cdo.set_editor_property('FurinaRlOfs', m)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn); R['status'] = str(pawn.get_editor_property('status'))
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    R['saved'] = bool(ASSETS.save_loaded_asset(pawn, False))

try: main()
except Exception: R['error'] = traceback.format_exc()[-2000:]
R['done'] = True; (ROOT / 'Saved' / 'ScopePIP.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8'); print('SCOPE_PIP', R.get('error', 'ok')[-300:])
