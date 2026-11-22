"""읽기 전용(2026-11-21): 대전차 화기 추가 전 조사 -> Saved/LauncherDump.json
 IMC 키 매핑, BP_FurinaBullet 구성/그래프, 폭발 이펙트 후보, 폰 그래프의 사격·재장전·FMG·HFX 연결, 마우스 휠 노드 이름"""
import json, re, traceback
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
def pins(n):
    out = []
    for p in list(n.list_input_pins()) + list(n.list_output_pins()):
        c = [q.get_owning_node().get_name() + '.' + str(q.get_pin_name()) for q in p.list_connected_pins()]
        v = str(p.get_pin_value())[:70]
        if c or v not in ('', 'None'): out.append([str(p.get_pin_name()), v, c[:5]])
    return out
try:
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    R['imc'] = [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None) for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
except Exception: R['imc_err'] = traceback.format_exc()[-400:]
try:
    bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary; comps = []
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        o = lib.get_associated_object(lib.get_data(h)); d = {'name': str(lib.get_variable_name(lib.get_data(h))), 'class': o.get_class().get_name() if o else None}
        if isinstance(o, unreal.PrimitiveComponent):
            d['coll_profile'] = str(o.get_collision_profile_name()); d['coll'] = str(o.get_collision_enabled())
        if isinstance(o, unreal.SphereComponent): d['radius'] = o.get_editor_property('sphere_radius')
        if isinstance(o, unreal.StaticMeshComponent) and o.static_mesh: d['mesh'] = o.static_mesh.get_path_name()
        if isinstance(o, unreal.ProjectileMovementComponent):
            for k in ('initial_speed', 'max_speed', 'projectile_gravity_scale', 'rotation_follows_velocity', 'should_bounce'): d[k] = o.get_editor_property(k)
        comps.append(d)
    R['bullet_comps'] = comps
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    R['bullet_graph'] = {n.get_name(): pins(n) for n in ed.list_all_nodes()}
    R['bullet_vars'] = [str(v) for v in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]
except Exception: R['bullet_err'] = traceback.format_exc()[-600:]
try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry(); hits = []
    for cls in ('NiagaraSystem', 'ParticleSystem', 'SoundWave', 'SoundCue', 'MetaSoundSource'):
        for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Niagara' if cls == 'NiagaraSystem' else ('/Script/MetasoundEngine' if cls == 'MetaSoundSource' else '/Script/Engine'), cls)):
            nm = str(a.asset_name)
            if re.search(r'explo|blast|grenade|rocket|impact|boom|smoke', nm, re.I): hits.append([cls, str(a.package_name)])
    R['fx'] = hits[:120]
except Exception: R['fx_err'] = traceback.format_exc()[-400:]
try:
    pawn = unreal.load_asset(PAWN); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(pawn, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    pat = re.compile(r'^(FMG_|HFX_Fx|HFX_Flash|HFX_NS|K2Node_FPF_(Recoil|ShotXf|ShotRot|ShotLoc|Lift|Dir0|DirZ|CamLoc|End|Self)|FSG_|HistoryReload_(Choose|Prepare|Amount|Has)|VM_Br_12|VM_Play|VM_Ready|STC_MagG43|SMG.*_(RlBranch_STG44|Is_STG44)|HistoryPrimary_(SingleShot|Is_PP))')
    R['pawn'] = {k: pins(n) for k, n in N.items() if pat.search(k)}
    R['pawn_vars'] = sorted(str(v) for v in unreal.BlueprintEditorLibrary.list_member_variable_names(pawn) if str(v).startswith('Furina'))
    R['wheel_actions'] = [s for s in ed.list_available_nodes([]) if re.search(r'wheel|scroll|휠', s, re.I)][:30]
    R['input_actions'] = [s for s in ed.list_available_nodes([]) if 'EnhancedActionEvents' in s][:60]
except Exception: R['pawn_err'] = traceback.format_exc()[-600:]
try:
    pawn = unreal.load_asset(PAWN); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(pawn, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    zoom = [k for k, n in N.items() if 'CameraZoom' in str(n.get_editor_property('input_action')) ] if False else []
    R['zoom_nodes'] = {}
    for k, n in N.items():
        if n.get_class().get_name() == 'K2Node_EnhancedInputAction':
            ia = None
            try: ia = n.get_editor_property('input_action')
            except Exception: pass
            if ia and 'Zoom' in ia.get_name():
                R['zoom_nodes'][k] = pins(n)
                for p in n.list_output_pins():
                    for q in p.list_connected_pins():
                        m = q.get_owning_node(); R['zoom_nodes'][m.get_name()] = pins(m)
    hud = unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD'); he = unreal.BlueprintGraphEditor.get_graph_editor_by_name(hud, 'EventGraph')
    R['hud'] = {n.get_name(): pins(n) for n in he.list_all_nodes() if n.get_name().startswith(('FM_', 'M4HUD_Draw', 'TFPHUD_'))}
except Exception: R['z_err'] = traceback.format_exc()[-600:]
R['done'] = True; (ROOT / 'Saved' / 'LauncherDump.json').write_text(json.dumps(R, indent=1, ensure_ascii=False, default=str), encoding='utf-8')
