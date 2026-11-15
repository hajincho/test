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
# Bounded travelling sway replaces the overlapping AnimDynamics chain solvers.
# amp is the extra radians per joint at 600 cm/s, added to idle. Small values
# matter: 18 braid joints accumulate their rotations down the strand.
hair = [('F_0_1_L', 8, [.016, .0085], [.003, .00225], 1.0, 2.0, .02, 0.0),
        ('F_0_1_R', 8, [.016, .0085], [.003, .00225], 1.0, 2.0, .02, .75),
        ('CF_1_L', 2, [.070, .040], [.010, .006], 1.1, .8, .35, .5),
        ('CF_1_R', 2, [.070, .040], [.010, .006], 1.1, .8, .35, 1.25),
        ('DM_0_1', 0, [.024, .014], [.004, .0025], 1.2, 1.2, .10, .9)]
# Silky follow-through on every joint (ChainHarmonics pendulum, rig space): each joint chases its rest direction with
# a lag of ~1/stiffness s, so head turns / footstep bobs ripple from root to tip instead of the strand moving as one
# rigid piece. min/max = how much of the lag each joint keeps (root -> tip), gravity = slight sag (cm/s, rig -Z).
# tuned in PIE: stiff 4 / drag .97 kept swinging +-10 cm for 4 s after stopping and +-20 cm while walking
# user: half way between the first version (unit default: lag 0 root -> .1 tip) and the full follow-through above.
PEND = {'F_0_1': dict(stiff=7.0, blend=.55, drag=.94, min=.1, max=.45, grav=-4.0),
        'CF_1': dict(stiff=6.0, blend=.6, drag=.96, min=.17, max=.45, grav=-1.5),
        'DM_0': dict(stiff=10.0, blend=.7, drag=.95, min=.03, max=.27, grav=0.0)}
for root, lift, amp, idle, tempo, spatial, rootAmp, phase in hair:
    pend = next(v for k, v in PEND.items() if root.startswith(k))
    out.append(dict(root=root, kind='hair', lift=lift, bob=0.0, amp=amp, idle=idle, tempo=tempo, spatial=spatial, phase=phase, rootAmp=rootAmp, pend=pend))
# stride warp (2026-11-15): feet stay 28 % closer to the pelvis when walking and 8 % when running (run is limited: 600 cm/s already needs a 2x play rate; 0.80 made the feet too fast) (ue_tfp_stride.py raises the rates by 1/s)
json.dump(dict(walk=120, sprint=600, run_narrow_cm=0.0, stride_warp=True, walk_stride=0.72, run_stride=0.92, run_kick=1.0,
               tfp_locomotion=True, crouch_drop_cm=0.0, crouch_back_cm=0.0,
               hair_motion_mode='bounded_speed_sway', hair_speed_blend=3.8, hair_idle_alpha=0.0, chains=out),
          open(S + r'\cr_params.json', 'w', encoding='utf-8'), indent=1)
for o in out: print(ascii(o['root']), o['kind'], o['lift'])


