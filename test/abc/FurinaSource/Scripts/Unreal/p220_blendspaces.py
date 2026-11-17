"""권총용 이동 블렌드스페이스 생성 (기존 BS_FurinaStanding/Crouching 과 같은 축: 방향 -180..180 x 속도). 샘플 = 리타게팅한 Lyra 권총 애니. 만들자마자 저장."""
import unreal, math, statistics, json, traceback
T = unreal.AssetToolsHelpers.get_asset_tools(); E = unreal.EditorAssetLibrary; A = unreal.AnimPoseExtensions
opts = unreal.AnimPoseEvaluationOptions(); W = unreal.AnimPoseSpaces.WORLD
FOLDER = '/Game/Furina/P220/Anim/'; DEST = '/Game/Furina/P220'
R = {'log': [], 'rates': {}}
def load(n):
    a = unreal.load_asset(FOLDER + 'Furina_Pistol_' + n); assert a, n; return a
def contact_speed(a):
    name = a.get_name()
    if name in R['rates']: return R['rates'][name]
    length = a.get_play_length(); rows = []; N = max(24, round(length * 30))
    for k in range(N):
        p = A.get_anim_pose_at_time(a, k * length / N, opts); row = {}
        for side in ('Left', 'Right'):
            ankle = A.get_bone_pose(p, side + '-ankle', W).translation; toe = A.get_bone_pose(p, side + '-toe', W).translation; row[side] = (ankle.x, ankle.y, toe.z)
        rows.append(row)
    speeds = []
    for side in ('Left', 'Right'):
        low = min(r[side][2] for r in rows)
        for k in range(1, len(rows)):
            x, y, z = rows[k][side]; px, py, pz = rows[k - 1][side]; v = math.hypot(x - px, y - py) / (length / N)
            if z < low + 2.5 and pz < low + 2.5 and v > 15: speeds.append(v)
    s = statistics.median(speeds) if speeds else 120.0; R['rates'][name] = s; return s
def blend(name, crouch):
    path = DEST + '/' + name
    if E.does_asset_exist(path): b = unreal.load_asset(path)
    else:
        f = unreal.BlendSpaceFactoryNew(); f.set_editor_property('target_skeleton', unreal.load_asset('/Game/Furina/SK_Furina_Skeleton'))
        b = T.create_asset(name, DEST, unreal.BlendSpace, f)
    pars = list(b.get_editor_property('BlendParameters'))
    for i, (label, mi, ma, grid) in enumerate([('Direction', -180, 180, 8), ('Speed', 0, 360 if crouch else 600, 6)]):
        q = pars[i]; q.import_text('(DisplayName="%s",Min=%f,Max=%f,GridNum=%d,bSnapToGrid=False,bWrapInput=%s)' % (label, mi, ma, grid, 'True' if i == 0 else 'False')); pars[i] = q
    b.set_editor_property('BlendParameters', pars)
    samples = []
    def sample(a, d, s, rate=1.0):
        x = unreal.BlendSample(); assert x.import_text('(Animation="/Script/Engine.AnimSequence\'%s\'",SampleValue=(X=%f,Y=%f,Z=0),RateScale=%f)' % (a.get_path_name(), d, s, rate)); samples.append(x)
    idle = load('Crouch_Idle' if crouch else 'Idle_Hipfire')
    for d in (-180, -135, -90, -45, 0, 45, 90, 135, 180): sample(idle, d, 0)
    for d in (-180, -135, -90, -45, 0, 45, 90, 135, 180):
        dirn = 'Bwd' if abs(d) > 135 else 'Fwd' if abs(d) < 45 else ('Left' if d < 0 else 'Right')
        if crouch:
            a = load('Crouch_Walk_' + dirn); sample(a, d, 90, 0.8); sample(a, d, 360, 1.3)
        else:
            a = load('Walk_' + dirn); sample(a, d, 120, 0.75)
            a = load('Jog_' + dirn); sample(a, d, 600, 1.2)
    b.set_editor_property('SampleData', samples); R['log'].append([name, len(samples), 'saved', E.save_loaded_asset(b, False)]); return b
try:
    blend('BS_Furina_PistolStanding', False); blend('BS_Furina_PistolCrouching', True)
except Exception: R['error'] = traceback.format_exc()[-1000:]
print('P220_BS', json.dumps(R, default=str, ensure_ascii=False)[:1800])

