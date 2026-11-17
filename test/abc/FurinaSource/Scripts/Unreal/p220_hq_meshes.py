"""P220 최고 품질 설정: Nanite 끄기(SM5 에서는 폴백 메시가 약 40~50% 삼각형만 사용 -> 뭉개짐), LOD0 100%, 풀 정밀도 UV/탄젠트, 텍스처 never-stream/LOD bias 0/Weapon 그룹."""
import unreal, json, traceback
EAL = unreal.EditorAssetLibrary
R = {'log': []}
try:
    sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for nm in ('SM_P220_Slide', 'SM_P220_Frame'):
        m = unreal.load_asset('/Game/Furina/P220/' + nm)
        ns = m.get_editor_property('nanite_settings'); ns.set_editor_property('enabled', False); sub.set_nanite_settings(m, ns)
        bs = sub.get_lod_build_settings(m, 0)
        bs.set_editor_property('use_full_precision_u_vs', True); bs.set_editor_property('recompute_normals', False); bs.set_editor_property('recompute_tangents', False)
        bs.set_editor_property('use_mikk_t_space', True); bs.set_editor_property('remove_degenerates', False); bs.set_editor_property('generate_lightmap_u_vs', False)
        sub.set_lod_build_settings(m, 0, bs)
        rs = sub.get_lod_reduction_settings(m, 0); rs.set_editor_property('percent_triangles', 1.0); rs.set_editor_property('percent_vertices', 1.0); sub.set_lod_reduction_settings(m, 0, rs)
        R['log'].append([nm, 'tris', m.get_num_triangles(0), 'verts', sub.get_number_verts(m, 0), 'nanite', m.get_editor_property('nanite_settings').get_editor_property('enabled'), 'saved', EAL.save_loaded_asset(m, False)])
    for tn in ('Albedo', 'Metallic', 'Normal', 'Roughness'):
        t = unreal.load_asset('/Game/Furina/P220/T_P220_' + tn)
        t.set_editor_property('never_stream', True); t.set_editor_property('lod_bias', 0); t.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WEAPON)
        try: t.set_editor_property('compression_quality', unreal.TextureCompressionQuality.TCQ_HIGHEST)
        except Exception: pass
        R['log'].append([tn, EAL.save_loaded_asset(t, False)])
except Exception: R['error'] = traceback.format_exc()[-900:]
print('P220_HQ', json.dumps(R, default=str, ensure_ascii=False))

