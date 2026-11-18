"""Lyra 에디터(`py <파일>`): M4 머티리얼 4종의 BaseColor/Metallic/Roughness/Specular/Normal/AO 입력 그래프를 재귀로 덤프(노드 클래스, 상수/텍스처 이름) -> Data/lyra_m4_mat_dump.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_m4_mat_dump.json'
MEL = unreal.MaterialEditingLibrary
R = {}
PROPS = ('texture', 'const_a', 'const_b', 'constant', 'r', 'g', 'b', 'a', 'parameter_name', 'desc', 'min_default', 'max_default', 'default_value', 'sampler_type')
def desc(e):
    d = {'cls': e.get_class().get_name()}
    for p in PROPS:
        try:
            v = e.get_editor_property(p)
            if hasattr(v, 'get_name'): v = v.get_name()
            d[p] = str(v) if not isinstance(v, (int, float, bool, str)) else v
        except Exception: pass
    return d
def walk(mat, e, depth, seen):
    if e is None or depth > 8: return None
    node = desc(e); node['id'] = id(e) % 100000
    if node['id'] in seen: return {'ref': node['id']}
    seen.add(node['id']); ins = []
    try:
        for i in MEL.get_inputs_for_material_expression(mat, e): ins.append(walk(mat, i, depth + 1, seen))
    except Exception as ex: node['err'] = str(ex)[:80]
    node['in'] = ins
    return node
try:
    for name in ('M_Colt_Main', 'M_Colt_Furniture', 'M_Colt_Mag', 'M_Colt_Rear'):
        mat = unreal.load_asset('/Game/Furina/M4/' + name); row = {}
        for pn in ('MP_BASE_COLOR', 'MP_METALLIC', 'MP_ROUGHNESS', 'MP_SPECULAR', 'MP_AMBIENT_OCCLUSION'):
            try: e = MEL.get_material_property_input_node(mat, getattr(unreal.MaterialProperty, pn)); row[pn] = walk(mat, e, 0, set())
            except Exception as ex: row[pn] = 'err ' + str(ex)[:80]
        for p in ('shading_model', 'blend_mode', 'two_sided'):
            try: row[p] = str(mat.get_editor_property(p))
            except Exception: pass
        R[name] = row
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_MAT_DUMP', R.get('error', 'ok')[-120:])
