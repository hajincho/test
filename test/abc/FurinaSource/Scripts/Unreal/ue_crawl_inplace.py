"""The retargeted crawl loops carry their forward travel in the Hips track (Hips is the only root of the Furina skeleton, so the pack's root-motion bone was lost): over the 1 s loop Hips.y rises by
~61 cm, which would snap back at every loop. This duplicates AS_Furina_Crawl_Prone_Fwd_Loop_L as AS_Furina_Crawl_Move (in place): the linear drift (Y_end - Y_start) * t / length is subtracted from the
Hips position track (rotation / scale untouched); the drift is the crawl speed in cm/s (the character must move at that speed so planted hands and feet do not slide). Also reports the same drift for
Prone_Idle. -> Data/crawl_inplace.json  usage: py ue_crawl_inplace.py"""
import unreal, json, traceback, math, sys
ROT_SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5      # usage: py ue_crawl_inplace.py [pelvis_rotation_scale]
D =r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def hips_keys(seq):
    opts = unreal.AnimPoseEvaluationOptions(); length = seq.get_editor_property('sequence_length'); n = int(round(length * 30)) + 1; pos = []; rot = []
    for i in range(n):
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, min(length, i / 30.0), opts); tr = unreal.AnimPoseExtensions.get_bone_pose(pose, 'Hips', unreal.AnimPoseSpaces.LOCAL)
        pos.append(tr.translation); rot.append(tr.rotation)
    return length, pos, rot
def main():
    R = {}
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools()
    dest = '/Game/Furina/Crawl'
    for name in ('AS_Furina_Crawl_Prone_Idle', 'AS_Furina_Crawl_Prone_Fwd_Loop_R'):
        l, p, r = hips_keys(unreal.load_asset(dest + '/' + name)); R[name] = dict(length=l, drift=[round(p[-1].x - p[0].x, 2), round(p[-1].y - p[0].y, 2), round(p[-1].z - p[0].z, 2)])
    src = unreal.load_asset(dest + '/AS_Furina_Crawl_Prone_Fwd_Loop_L')
    mp = dest + '/AS_Furina_Crawl_Move'
    seq = unreal.load_asset(mp) or T.duplicate_asset('AS_Furina_Crawl_Move', dest, src)
    length, pos, rot = hips_keys(src)
    dy = pos[-1].y - pos[0].y; n = len(pos); new = []
    for i, p in enumerate(pos): new.append(unreal.Vector(p.x, p.y - dy * (i / (n - 1)), p.z))
    R['drift_cm_per_loop'] = dy; R['speed_cm_s'] = dy / length; R['keys'] = n
    # pelvis twist: the Hips rotation swings around its loop mean; keep the mean (lying orientation) and scale the swing (ROT_SCALE 0.5 = half the pelvis rotation angle while crawling)
    q = [(r.x, r.y, r.z, r.w) for r in rot]; ref = q[0]; acc = [0.0] * 4
    for a in q:
        s = 1.0 if sum(x * y for x, y in zip(a, ref)) >= 0 else -1.0
        for k in range(4): acc[k] += s * a[k]
    nm = sum(x * x for x in acc) ** 0.5; mean = [x / nm for x in acc]
    def slerp(a, b, t):
        d = sum(x * y for x, y in zip(a, b))
        if d < 0: b = [-x for x in b]; d = -d
        if d > 0.9995:
            r = [x + t * (y - x) for x, y in zip(a, b)]
        else:
            th = math.acos(d); s0 = math.sin((1 - t) * th) / math.sin(th); s1 = math.sin(t * th) / math.sin(th); r = [s0 * x + s1 * y for x, y in zip(a, b)]
        m = sum(x * x for x in r) ** 0.5; return [x / m for x in r]
    def ang(a, b): return math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(a, b))))))
    R['hips_swing_deg_before'] = round(max(ang(mean, a) for a in q), 2)
    rot = [unreal.Quat(*slerp(mean, a, ROT_SCALE)) for a in q]
    R['hips_swing_deg_after'] = round(max(ang(mean, (r.x, r.y, r.z, r.w)) for r in rot), 2); R['rot_scale'] = ROT_SCALE
    scales = [unreal.Vector(1, 1, 1)] * n
    ctrl = seq.get_editor_property('controller'); ctrl.open_bracket(unreal.Text('In-place crawl: remove Hips forward drift, scale pelvis swing'), True)
    ctrl.set_bone_track_keys('Hips', new, rot, scales, True); ctrl.close_bracket(True)
    l2, p2, r2 = hips_keys(seq); R['after_drift'] = [round(p2[-1].x - p2[0].x, 3), round(p2[-1].y - p2[0].y, 3), round(p2[-1].z - p2[0].z, 3)]
    R['saved'] = E.save_loaded_asset(seq, False)
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\crawl_inplace.json', 'w'), indent=1); print('CRAWL_INPLACE', R.get('speed_cm_s'), R.get('error', '')[-400:])
