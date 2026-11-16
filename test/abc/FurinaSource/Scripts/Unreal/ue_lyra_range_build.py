"""Editor: Data/lyra_range_actors.json (Lyra 에디터에서 추출)로 /Game/LyraRange/L_FiringRange 일반 레벨을 만든다.
StaticMeshActor(메시/재질/트랜스폼/라벨/폴더), TextRenderActor, 조명(해/스카이/안개), 바닥 받침을 생성. Lyra 전용 액터(스포너/점프대/텔레포트/PlayerStart)와 Landscape는 제외.
-> Data/lyra_range_build.json, 레벨 저장"""
import unreal, json, traceback, collections
SRC = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_range_actors.json'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_range_build.json'
LEVEL = '/Game/LyraRange/L_FiringRange'
R = {'skipped': collections.Counter(), 'spawned': collections.Counter(), 'missing_mesh': [], 'missing_mat': []}
try:
    data = json.load(open(SRC, encoding='utf-8'))['actors']
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL): R['existing_level'] = True
    R['new_level'] = les.new_level(LEVEL)
    for a in list(eas.get_all_level_actors()):
        if a.get_class().get_name() in ('StaticMeshActor',): eas.destroy_actor(a)
    cache = {}
    def load(p):
        if p not in cache: cache[p] = unreal.load_asset(p.split('.')[0]) if p else None
        return cache[p]
    for a in data:
        cn = a['cls']; loc = unreal.Vector(*a['loc']); rot = unreal.Rotator(pitch=a['rot'][0], yaw=a['rot'][1], roll=a['rot'][2]); sc = unreal.Vector(*a['scale'])
        if cn == 'StaticMeshActor':
            mesh = load(a['mesh'])
            if mesh is None: R['missing_mesh'].append(a['mesh']); continue
            act = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
            c = act.get_component_by_class(unreal.StaticMeshComponent); c.set_mobility(unreal.ComponentMobility.STATIC)
            c.set_static_mesh(mesh)
            for i, mp in enumerate(a['mats']):
                m = load(mp) if mp else None
                if mp and m is None: R['missing_mat'].append(mp)
                if m: c.set_material(i, m)
            act.set_actor_scale3d(sc); act.set_actor_label(a['label'])
            if a['folder'] and a['folder'] != 'None': act.set_folder_path(a['folder'])
            R['spawned'][cn] += 1
        elif cn == 'TextRenderActor':
            act = eas.spawn_actor_from_class(unreal.TextRenderActor, loc, rot); c = act.get_component_by_class(unreal.TextRenderComponent)
            c.set_text(a.get('text', '')); c.set_world_size(a.get('world_size', 100.0)); act.set_actor_scale3d(sc); act.set_actor_label(a['label']); R['spawned'][cn] += 1
        elif cn in ('DirectionalLight',):
            act = eas.spawn_actor_from_class(unreal.DirectionalLight, loc, rot); act.set_actor_label('Sun'); R['spawned'][cn] += 1
        elif cn == 'SkyAtmosphere':
            act = eas.spawn_actor_from_class(unreal.SkyAtmosphere, loc, rot); R['spawned'][cn] += 1
        elif cn == 'SkyLight':
            act = eas.spawn_actor_from_class(unreal.SkyLight, loc, rot)
            try: act.get_component_by_class(unreal.SkyLightComponent).set_editor_property('real_time_capture', True)
            except Exception as e: R['skylight_err'] = str(e)[:80]
            R['spawned'][cn] += 1
        elif cn == 'ExponentialHeightFog':
            act = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, loc, rot); R['spawned'][cn] += 1
        else: R['skipped'][cn] += 1
    # 낙하 방지 받침 (Landscape 대신): 가장 낮은 바닥 아래에 큰 판
    cube = unreal.load_asset('/Engine/BasicShapes/Cube'); mat = unreal.load_asset('/Engine/EngineMaterials/WorldGridMaterial')
    fl = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -160), unreal.Rotator()); c = fl.get_component_by_class(unreal.StaticMeshComponent)
    c.set_mobility(unreal.ComponentMobility.STATIC); c.set_static_mesh(cube); c.set_material(0, mat); fl.set_actor_scale3d(unreal.Vector(400, 400, 1)); fl.set_actor_label('FallCatchFloor')
    R['spawned']['FallCatchFloor'] += 1
    R['saved'] = les.save_current_level()
    R['actors_in_level'] = len(eas.get_all_level_actors())
except Exception: R['error'] = traceback.format_exc()
R['skipped'] = dict(R['skipped']); R['spawned'] = dict(R['spawned']); R['missing_mesh'] = sorted(set(R['missing_mesh'])); R['missing_mat'] = sorted(set(R['missing_mat']))
json.dump(R, open(OUT, 'w'), indent=1)
print('LYRA_RANGE_BUILD', R.get('spawned'), R.get('error', '')[-300:])
