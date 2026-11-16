"""LYRA 에디터에서 실행: L_FiringRange_WP 전체 액터를 로드해 JSON으로 내보냄 -> abc/FurinaSource/Data/lyra_range_actors.json
실행: UnrealEditor.exe LyraStarterGame.uproject -ExecutePythonScript="<이 파일>" -nullrhi -unattended -nosplash"""
import unreal, json, traceback, collections
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_range_actors.json'
R = {'actors': []}
try:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    R['loaded'] = les.load_level('/ShooterMaps/Maps/L_FiringRange_WP')
    lib = unreal.WorldPartitionBlueprintLibrary
    descs = lib.get_actor_descs()
    R['desc_count'] = len(descs) if descs else None
    if descs:
        lib.load_actors([d.guid for d in descs])
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    acts = eas.get_all_level_actors()
    R['count'] = len(acts)
    for a in acts:
        cn = a.get_class().get_name()
        t = a.get_actor_transform()
        row = {'cls': cn, 'path_cls': a.get_class().get_path_name(), 'label': a.get_actor_label(), 'folder': str(a.get_folder_path()),
               'loc': [t.translation.x, t.translation.y, t.translation.z],
               'rot': [t.rotation.rotator().pitch, t.rotation.rotator().yaw, t.rotation.rotator().roll],
               'scale': [t.scale3d.x, t.scale3d.y, t.scale3d.z]}
        if cn == 'StaticMeshActor':
            c = a.get_component_by_class(unreal.StaticMeshComponent)
            row['mesh'] = c.static_mesh.get_path_name() if c.static_mesh else None
            row['mats'] = [m.get_path_name() if m else None for m in c.get_materials()]
            row['mobility'] = str(c.mobility)
            row['collision'] = str(c.get_collision_profile_name())
        elif cn == 'TextRenderActor':
            c = a.get_component_by_class(unreal.TextRenderComponent)
            row['text'] = str(c.text); row['world_size'] = c.world_size
        elif cn == 'BlockingVolume':
            o, e = a.get_actor_bounds(False); row['extent'] = [e.x, e.y, e.z]
        R['actors'].append(row)
    R['classes'] = dict(collections.Counter(a['cls'] for a in R['actors']).most_common(30))
except Exception:
    R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
print('LYRA_EXPORT done', R.get('count'), R.get('error', '')[-300:])
unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
