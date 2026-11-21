"""헤드리스: UE 의 SK_FPVM_<키> 를 FBX 로 다시 내보내(UV 확인용) -> FurinaSource/FBX/FPVM/_check_<키>.fbx"""
import unreal, sys, json, traceback
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; KEY = ARGS[0] if ARGS else 'G43'; R = {}
KEY = 'G43' if KEY.startswith('g') or KEY == 'bg' else KEY
try:
    sm = unreal.load_asset('/Game/Furina/FPVM/%s/SK_FPVM_%s' % (KEY, KEY))
    t = unreal.AssetExportTask(); t.set_editor_property('object', sm); t.set_editor_property('filename', r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\FBX\FPVM\_check_%s.fbx' % KEY)
    t.set_editor_property('automated', True); t.set_editor_property('replace_identical', True); t.set_editor_property('prompt', False)
    R['ok'] = bool(unreal.Exporter.run_asset_export_task(t)); R['errors'] = [str(e) for e in t.get_editor_property('errors')]
    try: R['uv_channels'] = sm.get_editor_property('lod_info')[0].get_editor_property('build_settings').get_editor_property('src_lightmap_index') if False else None
    except Exception: pass
except Exception: R['error'] = traceback.format_exc()[-800:]
R['done'] = True; json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fpvm_export_check.json', 'w'), indent=1, default=str); print('EXPORT_CHECK', R)
