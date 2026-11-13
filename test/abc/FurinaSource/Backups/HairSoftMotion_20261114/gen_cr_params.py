import json, sys
S = sys.argv[1]
cloth = json.load(open(S + r'\cloth_bones.json', encoding='utf-8'))
pl = json.load(open(S + r'\furina_player.json', encoding='utf-8'))
ul = {n['name']: n['lp'] for n in pl['nodes'].values() if n['path'].startswith('Furina Player/ModelRoot/Furina/Armature/')}
chains = []
# root position relative to the hips (UE: forward = +Y); hips-local Unity z ~ -UE y
for c in cloth:
    if c['depth'] != 0: continue
    lp = ul[c['bone']]
    back = lp['z']  # Unity hips-local z: negative = behind (Unity forward is +z)... measured below
    chains.append(dict(root=c['bone'], unity=lp))
# decide rear-ness from UE world positions measured in the editor
pos = json.load(open(S + r'\ue_speeds.json', encoding='utf-8'))['pos']
out = []
for i, ch in enumerate(chains):
    r = ch['root']; long_layer = not r.startswith('HB1')
    y = pos.get(r, [0, -8, 0])[1]
    rear = max(0.0, min(1.0, (5.4 - 2.0 - y) / 10.0))
    # full-sprint lift: long tails stream almost level behind (Unity silk-run reference), peplum flares back
    out.append(dict(root=r, kind='cloth', lift=round(55.0 if long_layer else 12 + 25 * rear, 1),
                    bob=8.0 if long_layer else 7.0,
                    amp=[.08, .04] if long_layer else [.12, .06], idle=[0, 0], tempo=4.5,
                    spatial=4.0 if long_layer else 2.0, phase=round(i * .7, 2), rootAmp=.15))
# neck scarf (single joint) and hat ribbon also stream back like the Unity run
out.append(dict(root='领巾', kind='cloth', lift=60.0, bob=10.0, wave=False, amp=[0, 0], idle=[0, 0], tempo=0, spatial=0, phase=0, rootAmp=0))
out.append(dict(root='帽D1_1', kind='cloth', lift=35.0, bob=8.0, amp=[.10, .05], idle=[0, 0], tempo=5.0, spatial=1.5, phase=.3, rootAmp=.4))
# Hair motion itself now comes from the Unity chain physics (AnimDynamics in ABP_Furina, gen_t3d3.py).
# The rig only adds HuTaoChainPhysics' slow idle breeze (idleBreeze .45 x profile breeze) as a gentle target sway.
# idle: barely a breeze; the amplitude grows with Drive (0 idle .. 1 walk .. 2 sprint) so running makes the hair flap
hair = [('F_0_1_L', 0, [.020, .012], [.008, .006], 1.0, 2.0, .10, 0.0),
        ('F_0_1_R', 0, [.020, .012], [.008, .006], 1.0, 2.0, .10, 1.1),
        ('CF_1_L', 0, [.050, .030], [.004, .003], 1.2, 1.0, .40, .5),
        ('CF_1_R', 0, [.050, .030], [.004, .003], 1.2, 1.0, .40, 1.7),
        ('DM_0_1', 0, [.030, .020], [.001, .0007], 1.4, 1.5, .20, .9)]
for root, lift, amp, idle, tempo, spatial, rootAmp, phase in hair:
    out.append(dict(root=root, kind='hair', lift=lift, bob=0.0, amp=amp, idle=idle, tempo=tempo, spatial=spatial, phase=phase, rootAmp=rootAmp))
json.dump(dict(walk=120, sprint=600, run_narrow_cm=2.0, run_stride=0.55, run_kick=0.6, hair_idle_alpha=0.3, chains=out), open(S + r'\cr_params.json', 'w', encoding='utf-8'), indent=1)
for o in out: print(ascii(o['root']), o['kind'], o['lift'])


