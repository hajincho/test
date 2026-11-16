"""Editor: L_FiringRange_WP 월드 파티션 액터 전체 로드 후 클래스 집계/바닥 높이 -> Data/lyra_range_load.json"""
import unreal, json, traceback, collections
R = {}
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    R['world'] = world.get_path_name()
    lib = unreal.WorldPartitionBlueprintLibrary
    box = lib.get_editor_world_bounds()
    R['box'] = str(box)
    descs = lib.get_intersecting_actor_descs(box)
    if descs is None: descs = lib.get_actor_descs()
    R['desc_type'] = str(type(descs))
    if isinstance(descs, tuple): descs = [x for x in descs if x is not None and not isinstance(x, bool)][0]
    R['desc_count'] = len(descs)
    guids = []
    cls = collections.Counter()
    for d in descs:
        guids.append(d.guid)
        cls[str(d.native_class) + ' | ' + str(d.class_)] += 1
    R['guid_count'] = len(guids); R['desc_classes'] = dict(cls.most_common(15))
    if guids:
        lib.load_actors(guids)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    acts = eas.get_all_level_actors()
    R['loaded_count'] = len(acts)
    c = collections.Counter(a.get_class().get_name() for a in acts); R['classes'] = dict(c.most_common(30))
    tops = []; mn = [1e9] * 3; mx = [-1e9] * 3
    for a in acts:
        if a.get_class().get_name() == 'StaticMeshActor':
            o, e = a.get_actor_bounds(False)
            tops.append(round(o.z + e.z))
            for i, v in enumerate((o.x, o.y, o.z)): mn[i] = min(mn[i], v - (e.x, e.y, e.z)[i]); mx[i] = max(mx[i], v + (e.x, e.y, e.z)[i])
    R['bounds_min'] = [round(v) for v in mn]; R['bounds_max'] = [round(v) for v in mx]
    R['top_hist'] = dict(collections.Counter(tops).most_common(12))
    ps = []
    for a in acts:
        if 'PlayerStart' in a.get_class().get_name():
            l = a.get_actor_location(); ps.append([round(l.x), round(l.y), round(l.z), round(a.get_actor_rotation().yaw)])
    R['player_starts'] = ps
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_range_load.json', 'w'), indent=1, default=str)
print('LYRA_RANGE_LOAD', R.get('error', 'ok')[-300:])
