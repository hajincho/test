"""Editor: dumps M_Colt_Main/Furniture/Rear/Mag (expressions, texture refs, connected outputs) and the SK_M4A1 material slots -> Data/colt_mat_probe.json"""
import unreal, json, traceback
R = {}
try:
    for n in ('Main', 'Furniture', 'Rear', 'Mag'):
        m = unreal.load_asset('/Game/Furina/M4/M_Colt_' + n); ml = unreal.MaterialEditingLibrary
        ex = []
        for e in ml.get_material_expressions(m) if hasattr(ml, 'get_material_expressions') else []:
            row = [e.get_class().get_name()]
            try: row.append(e.get_editor_property('texture').get_name())
            except Exception: pass
            ex.append(row)
        conn = {}
        for p in (unreal.MaterialProperty.MP_BASE_COLOR, unreal.MaterialProperty.MP_METALLIC, unreal.MaterialProperty.MP_ROUGHNESS, unreal.MaterialProperty.MP_NORMAL, unreal.MaterialProperty.MP_AMBIENT_OCCLUSION):
            try: c = ml.get_material_property_input_node(m, p); conn[str(p).split('.')[-1]] = c.get_class().get_name() + ('/' + c.get_editor_property('texture').get_name() if hasattr(c, 'texture') and c.get_editor_property('texture') else '') if c else None
            except Exception as e: conn[str(p)] = 'ERR ' + str(e)[:50]
        R[n] = {'expr': ex, 'conn': conn, 'two_sided': m.get_editor_property('two_sided'), 'shading': str(m.get_editor_property('shading_model'))}
    sk = unreal.load_asset('/Game/Furina/M4/SK_M4A1'); R['slots'] = [(str(s.material_slot_name), s.material_interface.get_name() if s.material_interface else None) for s in sk.get_editor_property('materials')]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\colt_mat_probe.json', 'w'), indent=1); print('COLT_MAT', R.get('error', '')[-200:])
