"""Lyra 에디터: M4/Colt 텍스처 설정 점검(원본 해상도, 최대 크기, LOD 바이어스, 스트리밍, 압축, sRGB, 밉 설정) -> Data/lyra_m4_tex_check.json"""
import unreal, json, traceback, glob
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_m4_tex_check.json'
R = {'tex': {}}
try:
    names = ['T_Colt_%s_%s' % (g, m) for g in ('Main', 'Furniture', 'Rear', 'Mag') for m in ('BaseColor', 'Normal', 'Metallic', 'Roughness', 'AO')]
    R['listed'] = [x for x in unreal.EditorAssetLibrary.list_assets('/Game/Furina/M4') if 'Colt' in x][:6]
    for nm in names:
        a = unreal.load_asset('/Game/Furina/M4/' + nm)
        if a is None: R['tex'][nm] = 'missing'; continue
        row = {}
        for n in ('max_texture_size', 'lod_bias', 'never_stream', 'srgb', 'compression_settings', 'mip_gen_settings', 'lod_group', 'power_of_two_mode', 'filter', 'virtual_texture_streaming', 'compression_no_alpha', 'texture_group'):
            try: row[n] = str(a.get_editor_property(n))
            except Exception: pass
        try: row['size'] = [a.blueprint_get_size_x(), a.blueprint_get_size_y()]
        except Exception: pass
        try: row['source_size'] = [a.get_editor_property('source_size_x') if hasattr(a, 'get_editor_property') else None]
        except Exception: pass
        R['tex'][a.get_name()] = row
    cv = {}
    for c in ('r.Streaming.PoolSize', 'r.Streaming.MipBias', 'r.Streaming.Boost', 'r.Streaming.LimitPoolSizeToVRAM', 'r.Streaming.UseFixedPoolSize', 'r.Streaming.FullyLoadUsedTextures', 'r.MaxAnisotropy', 'r.Streaming.MaxEffectiveScreenSize', 'r.TextureStreaming', 'r.VT.MaxAnisotropy', 'r.ViewDistanceScale', 'sg.TextureQuality', 'r.Streaming.PoolSize.Percent'):
        try: cv[c] = unreal.SystemLibrary.get_console_variable_float_value(c)
        except Exception as e: cv[c] = 'n/a'
    R['cvars'] = cv
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_M4_TEX', len(R['tex']), R.get('error', '')[-200:])
