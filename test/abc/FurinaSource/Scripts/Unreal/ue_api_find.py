"""Writes Data/api_find.json: names in unreal.* classes matching the substrings in argv (class.attr)."""
import unreal, sys, json
keys = [k.lower() for k in sys.argv[1:]] or ['vertex']
R = {}
for cn in ('SkeletalMeshComponent', 'SkinnedMeshComponent', 'SkeletalMesh', 'SkeletalMeshEditorSubsystem', 'SkeletalMeshLibrary', 'MeshComponent', 'PrimitiveComponent'):
    c = getattr(unreal, cn, None)
    if c: R[cn] = [a for a in dir(c) if any(k in a.lower() for k in keys)]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\api_find.json', 'w'), indent=1); print('API_FIND', sum(len(v) for v in R.values()))
