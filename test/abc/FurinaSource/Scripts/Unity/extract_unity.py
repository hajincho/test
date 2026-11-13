"""Extract the 'Furina Player' subtree from a Unity scene YAML into JSON."""
import json, re, sys, os

scene, root_name, out = sys.argv[1], sys.argv[2], sys.argv[3]
assets = sys.argv[4]

text = open(scene, encoding='utf-8').read()
docs = re.split(r'^--- !u!(\d+) &(-?\d+)(?: stripped)?\s*$', text, flags=re.M)
objs = {}
for i in range(1, len(docs) - 2, 3):
    cls, fid, body = int(docs[i]), docs[i + 1], docs[i + 2]
    objs[fid] = (cls, body)

def field(body, name):
    m = re.search(r'^\s+' + re.escape(name) + r': (.*)$', body, re.M)
    return m.group(1).strip() if m else None

def vec(s):
    return {k: float(v) for k, v in re.findall(r'(\w+): (-?[\d.eE+-]+)', s or '')}

def ref(s):
    m = re.search(r'fileID: (-?\d+)', s or '')
    return m.group(1) if m else None

def uname(s):
    s = s.strip()
    if s.startswith('"'):
        return json.loads(s)
    return s

# GameObjects
go = {}
for fid, (cls, body) in objs.items():
    if cls == 1:
        name = uname(field(body, 'm_Name') or '')
        comps = re.findall(r'component: \{fileID: (-?\d+)\}', body)
        go[fid] = dict(name=name, comps=comps, active=field(body, 'm_IsActive'))

root_go = [f for f, g in go.items() if g['name'] == root_name]
assert len(root_go) == 1, root_go
# transforms
tr = {}
for fid, (cls, body) in objs.items():
    if cls in (4, 224):
        tr[fid] = dict(go=ref(field(body, 'm_GameObject')), father=ref(field(body, 'm_Father')),
                       children=re.findall(r'- \{fileID: (-?\d+)\}', body.split('m_Children:')[1].split('m_Father')[0]) if 'm_Children:' in body else [],
                       lp=vec(field(body, 'm_LocalPosition')), lr=vec(field(body, 'm_LocalRotation')),
                       ls=vec(field(body, 'm_LocalScale')))
root_tr = [c for c in go[root_go[0]]['comps'] if c in tr][0]

# guid -> script path
guid_map = {}
for dp, dn, fn in os.walk(assets):
    for f in fn:
        if f.endswith('.cs.meta'):
            m = re.search(r'guid: (\w+)', open(os.path.join(dp, f), encoding='utf-8', errors='ignore').read())
            if m: guid_map[m.group(1)] = f[:-8]

nodes, order = {}, []
def walk(t, path):
    g = go[tr[t]['go']]
    p = path + '/' + g['name'] if path else g['name']
    nodes[t] = dict(name=g['name'], path=p, parent=tr[t]['father'], lp=tr[t]['lp'], lr=tr[t]['lr'], ls=tr[t]['ls'], active=g['active'], comps=[])
    order.append(t)
    for c in g['comps']:
        if c == t or c not in objs: continue
        cls, body = objs[c]
        info = dict(cls=cls, fid=c)
        if cls == 114:
            gm = re.search(r'm_Script: \{fileID: 11500000, guid: (\w+)', body)
            info['script'] = guid_map.get(gm.group(1), gm.group(1)) if gm else None
            info['body'] = body
        elif cls == 137:
            info['mesh'] = field(body, 'm_Mesh')
            info['bones'] = re.findall(r'- \{fileID: (-?\d+)\}', body.split('m_Bones:')[1].split('m_BlendShapeWeights')[0]) if 'm_Bones:' in body else []
            info['rootBone'] = ref(field(body, 'm_RootBone'))
            info['materials'] = re.findall(r'guid: (\w+)', body.split('m_Materials:')[1].split('m_StaticBatchInfo')[0])
            info['enabled'] = field(body, 'm_Enabled')
        nodes[t]['comps'].append(info)
    for ch in tr[t]['children']:
        if ch in tr: walk(ch, p)
walk(root_tr, '')
json.dump(dict(root=root_tr, order=order, nodes=nodes), open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('nodes', len(nodes))
for t in order:
    for c in nodes[t]['comps']:
        if c['cls'] == 114: print('MB', nodes[t]['path'], c['script'])
        elif c['cls'] == 137: print('SMR', nodes[t]['path'], c['mesh'], 'bones', len(c['bones']), 'enabled', c['enabled'])
        else: print('C', c['cls'], nodes[t]['path'])
