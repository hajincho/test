"""Lyra 에디터(`py <파일>`): SM_P220_Frame / SM_P220_Slide 를 FBX 로 내보낸다 (손가락 관통 검사용).  -> Data/p220_export/*.fbx"""
import unreal, os, json, traceback
OUTD = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\p220_export'
R = {}
try:
    os.makedirs(OUTD, exist_ok=True)
    tasks = []
    for nm in ('SM_P220_Frame', 'SM_P220_Slide'):
        a = unreal.load_asset('/Game/Furina/P220/' + nm)
        t = unreal.AssetExportTask(); t.set_editor_property('object', a); t.set_editor_property('filename', OUTD + '\\' + nm + '.fbx'); t.set_editor_property('automated', True); t.set_editor_property('replace_identical', True); t.set_editor_property('prompt', False)
        tasks.append(t)
    R['ok'] = bool(unreal.Exporter.run_asset_export_tasks(tasks))
    R['files'] = os.listdir(OUTD)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_export_p220_mesh.json', 'w'), indent=1); print('LYRA_EXPORT_P220', R.get('ok'), R.get('error', '')[-200:])
