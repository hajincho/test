import json, itertools, sys
S = sys.argv[1]
ue = json.load(open(S + r'\ue_ref.json', encoding='utf-8'))
pl = json.load(open(S + r'\furina_player.json', encoding='utf-8'))
un = {n['name']: n for n in pl['nodes'].values() if n['path'].startswith('Furina Player/ModelRoot/Furina/Armature/')}
names = [n for n in ue if n.replace('-', ' ') in un]
best = []
for perm in itertools.permutations(range(4)):
    for signs in itertools.product((1, -1), repeat=4):
        err = 0
        for n in names:
            u = un[n.replace('-', ' ')]['lr']; uq = [u['x'], u['y'], u['z'], u['w']]
            m = [signs[i] * uq[perm[i]] for i in range(4)]
            e = ue[n]['q']
            d = abs(sum(a * b for a, b in zip(m, e)))
            err += 1 - min(1, d)
        best.append((err, perm, signs))
best.sort()
print('rot', best[:3], len(names))
bp = []
for perm in itertools.permutations(range(3)):
    for signs in itertools.product((1, -1), repeat=3):
        for scale in (1, 100):
            err = 0
            for n in names:
                if n == 'Hips': continue
                u = un[n.replace('-', ' ')]['lp']; up = [u['x'], u['y'], u['z']]
                m = [signs[i] * up[perm[i]] * scale for i in range(3)]
                err += sum(abs(a - b) for a, b in zip(m, ue[n]['p']))
            bp.append((err, perm, signs, scale))
bp.sort(); print('pos', bp[:2])
h = un['Hips']; print('hips unity', h['lp'], h['lr'], 'ue', ue['Hips'])
