"""Lyra 에디터: 소총/탄창 머티리얼 점검 — SK_M4A1 / SM_M4Mag 슬롯 머티리얼, 푸리나 폰의 FurinaRifle / FurinaMag 컴포넌트 재질 덮어쓰기, 각 머티리얼이 쓰는 텍스처(없는 텍스처/기본 텍스처 여부) -> Data/lyra_m4_material_check.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_m4_material_check.json'
R = {}
MEL = unreal.MaterialEditingLibrary
def mat_info(m):
    out = {'name': m.get_path_name() if m else None}
    if not m: return out
    out['class'] = m.get_class().get_name()
    try:
        base = m.get_base_material() if hasattr(m, 'get_base_material') else m; out['base'] = base.get_path_name() if base else None
    except Exception: pass
    try: tex = MEL.get_used_textures(m); out['textures'] = [[t.get_path_name(), t.get_class().get_name(), getattr(t, 'blueprint_get_size_x', lambda: None)() if hasattr(t, 'blueprint_get_size_x') else None] for t in tex]
    except Exception as e: out['tex_err'] = str(e)[:80]
    try:
        if isinstance(m, unreal.MaterialInstanceConstant):
            out['tex_params'] = {str(p.parameter_info.name): (p.parameter_value.get_path_name() if p.parameter_value else None) for p in m.get_editor_property('texture_parameter_values')}
            out['scalar'] = {str(p.parameter_info.name): p.parameter_value for p in m.get_editor_property('scalar_parameter_values')}
            out['vector'] = {str(p.parameter_info.name): str(p.parameter_value) for p in m.get_editor_property('vector_parameter_values')}
    except Exception as e: out['mic_err'] = str(e)[:80]
    return out
try:
    for p in ('/Game/Furina/M4/SK_M4A1', '/Game/Furina/M4/SM_M4Mag'):
        a = unreal.load_asset(p); mats = []
        try:
            for s in (a.get_editor_property('materials') if isinstance(a, unreal.SkeletalMesh) else a.get_editor_property('static_materials')):
                mi = s.get_editor_property('material_interface'); mats.append([str(s.get_editor_property('material_slot_name')), mat_info(mi)])
        except Exception as e: mats.append(['err', str(e)[:100]])
        R[p] = mats
    pawn = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary; R['pawn_comps'] = {}
    for h in S.k2_gather_subobject_data_for_blueprint(pawn):
        o = L.get_associated_object(L.get_data(h)); nm = str(L.get_variable_name(L.get_data(h)))
        if nm in ('FurinaMag', 'FurinaRifle', 'FurinaPistolFrame', 'FurinaPistolSlide') and o is not None:
            try: R['pawn_comps'][nm] = [str(x.get_path_name()) if x else None for x in o.get_materials()]
            except Exception as e: R['pawn_comps'][nm] = 'err ' + str(e)[:80]
    for p in ('/Game/Furina/M4/BP_M4MagDrop',):
        try:
            bp = unreal.load_asset(p); cdo = unreal.get_default_object(bp.generated_class())
            R[p] = [str(m.get_path_name()) if m else None for m in cdo.get_components_by_class(unreal.StaticMeshComponent)[0].get_materials()]
        except Exception as e: R[p] = 'err ' + str(e)[:100]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_M4_MAT', R.get('error', 'ok')[-200:])
