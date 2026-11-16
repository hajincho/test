"""Editor: /ShooterMaps/Maps/L_FiringRange_WP 로드 확인, 액터 클래스 집계, 바닥 후보 높이 -> Data/lyra_range_probe.json"""
import unreal, json, traceback, collections
R = {}
try:
    R['plugin_mounted'] = unreal.EditorAssetLibrary.does_directory_exist('/ShooterMaps/Maps')
    R['map_exists'] = unreal.EditorAssetLibrary.does_asset_exist('/ShooterMaps/Maps/L_FiringRange_WP')
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ok = les.load_level('/ShooterMaps/Maps/L_FiringRange_WP')
    R['loaded'] = ok
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    acts = eas.get_all_level_actors()
    R['count'] = len(acts)
    c = collections.Counter(a.get_class().get_name() for a in acts); R['classes'] = dict(c.most_common(30))
    # StaticMeshActor 박스 상단 높이 통계
    tops = []; mn = [1e9] * 3; mx = [-1e9] * 3
    for a in acts:
        if a.get_class().get_name() == 'StaticMeshActor':
            o, e = a.get_actor_bounds(False)
            tops.append(round(o.z + e.z));
            for i, v in enumerate((o.x, o.y, o.z)): mn[i] = min(mn[i], v - (e.x, e.y, e.z)[i]); mx[i] = max(mx[i], v + (e.x, e.y, e.z)[i])
    R['bounds_min'] = [round(v) for v in mn]; R['bounds_max'] = [round(v) for v in mx]
    R['top_hist'] = dict(collections.Counter(tops).most_common(12))
    R['world'] = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_range_probe.json', 'w'), indent=1)
print('LYRA_RANGE_PROBE', R.get('error', 'ok')[-300:])
