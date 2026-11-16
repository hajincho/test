"""Editor: WorldPartitionBlueprintLibrary 함수 도움말 조회 -> Data/wp_doc_probe.json"""
import unreal, json
lib = unreal.WorldPartitionBlueprintLibrary
R = {n: (getattr(lib, n).__doc__ or '')[:700] for n in ('get_actor_descs', 'load_actors', 'get_intersecting_actor_descs', 'get_editor_world_bounds', 'pin_actors', 'get_actor_descs_for_actors')}
R['ActorDesc_members'] = [m for m in dir(unreal.ActorDesc) if not m.startswith('_')]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\wp_doc_probe.json', 'w'), indent=1)
print('WP_DOC')
