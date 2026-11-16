"""Editor: World Partition 관련 Python API 이름 조회 -> Data/wp_api_probe.json"""
import unreal, json
names = [n for n in dir(unreal) if 'WorldPartition' in n or 'DataLayer' in n or 'ActorDesc' in n]
R = {'names': names}
for cls in ('WorldPartitionBlueprintLibrary', 'WorldPartitionEditorSubsystem', 'WorldPartitionSubsystem'):
    c = getattr(unreal, cls, None)
    if c: R[cls] = [m for m in dir(c) if not m.startswith('_')][:80]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\wp_api_probe.json', 'w'), indent=1)
print('WP_API', len(names))
