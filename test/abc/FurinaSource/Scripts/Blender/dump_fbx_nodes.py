"""Run inside Blender: dump FBX Model node local transforms + connections (raw FBX data)."""
import sys, json
from io_scene_fbx import parse_fbx
argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv
root, ver = parse_fbx.parse(src)

def find(el, name):
    for c in el.elems:
        if c.id == name: return c

def props(el):
    p70 = find(el, b'Properties70')
    d = {}
    if p70:
        for p in p70.elems:
            k = p.props[0].decode('utf-8', 'replace')
            d[k] = [v if not isinstance(v, bytes) else v.decode('utf-8', 'replace') for v in p.props[4:]]
    return d

objects = find(root, b'Objects')
conns = find(root, b'Connections')
models = {}
for el in objects.elems:
    if el.id == b'Model':
        uid = el.props[0]
        name = el.props[1].split(b'\x00\x01')[0].decode('utf-8', 'replace')
        typ = el.props[2].decode()
        models[uid] = dict(name=name, type=typ, props=props(el))
parent = {}
for c in conns.elems:
    if c.props[0] == b'OO' and c.props[1] in models:
        parent[c.props[1]] = c.props[2]
gs = find(root, b'GlobalSettings')
res = dict(globals=props(gs) if gs else {}, models=[
    dict(uid=u, name=m['name'], type=m['type'], parent=models[parent[u]]['name'] if parent.get(u) in models else None,
         T=m['props'].get('Lcl Translation'), R=m['props'].get('Lcl Rotation'), S=m['props'].get('Lcl Scaling'),
         Pre=m['props'].get('PreRotation'), Post=m['props'].get('PostRotation'), RotOrder=m['props'].get('RotationOrder'))
    for u, m in models.items()])
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('models', len(models))
