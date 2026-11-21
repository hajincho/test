"""Lyra 에디터(`py <파일> <태그> [R|L|RL]`): 1인칭 권총 모드에서 손가락 뼈를 대기 자세 상수로 고정(꿈틀거림 제거).
 Data/lyra_pistol_twitch_probe_<태그>.json 의 consts(대기 구간 중앙값 = 부모 기준 로컬 회전)를 사용:
   PgK_<뼈> = SetRotation(Local, Value=상수 쿼터니언, Weight=PistW, bPropagateToChildren=True)
 삽입 위치: SetHairFlow 앞 (PgS_* 손가락 증분 노드들 뒤)  -> 가중치 1(권총 모드)에서는 애니메이션/재장전 몽타주 손가락 움직임과 무관하게 고정 자세.
 손 단위(R/L)로 나눠 실행(노드 추가가 느림). 다시 실행하면 값만 갱신.   -> Data/lyra_cr_pistol_lock.json"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
U = '/Script/ControlRig.RigUnit_'
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; TAG = ARGS[0]; HAND = ARGS[1] if len(ARGS) > 1 else 'RL'
J = json.load(open(D + r'\lyra_pistol_twitch_probe_%s.json' % TAG)); C = J['consts']; R = {'tag': TAG, 'hand': HAND, 'prog': []}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes(); assert 'PistW' in N and 'SetHairFlow' in N
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    bones = [b for b in C if b.endswith('_' + HAND[0]) or (len(HAND) > 1 and b.endswith('_' + HAND[1]))]
    # 근위 -> 원위 순서(Thumb0..3, Index1..3 ...)
    bones.sort(key=lambda b: (b[-1], b))
    ONLY = ARGS[2:]
    if ONLY: bones = [b for b in bones if b in ONLY]
    first = None; prev = None; newfirst = None
    for bn in bones:
        q = C[bn]; nm = 'PgK_' + bn
        if nm not in N:
            c.add_unit_node_from_struct_path(U + 'SetRotation', 'Execute', unreal.Vector2D(0, 0), nm)
        c.set_pin_default_value(nm + '.Item', '(Type=Bone,Name="%s")' % bn, True, False); c.set_pin_default_value(nm + '.Space', 'LocalSpace', True, False)
        c.set_pin_default_value(nm + '.bPropagateToChildren', 'True', True, False)
        c.set_pin_default_value(nm + '.Value', '(X=%.7f,Y=%.7f,Z=%.7f,W=%.7f)' % tuple(q), True, False)
        if nm not in N:
            link('PistW.Result', nm + '.Weight')
            if prev is None: newfirst = nm
            else: link(prev + '.ExecutePin', nm + '.ExecutePin')
            prev = nm
        R['prog'].append(bn); json.dump(R, open(D + r'\lyra_cr_pistol_lock.json', 'w'), indent=1, default=str)
    if newfirst:
        N2 = nodes(); src = None
        for nm2, n in N2.items():
            for p in n.get_pins():
                if str(p.get_name()) == 'ExecutePin':
                    for t in p.get_linked_target_pins():
                        if str(t.get_pin_path()) == 'SetHairFlow.ExecutePin': src = nm2
        R['src_exec'] = src
        assert src, 'SetHairFlow 앞 노드를 못 찾음'
        c.break_link(src + '.ExecutePin', 'SetHairFlow.ExecutePin'); link(src + '.ExecutePin', newfirst + '.ExecutePin'); link(prev + '.ExecutePin', 'SetHairFlow.ExecutePin')
    R['links_fail'] = [l for l in L if l[2] is not True]
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\lyra_cr_pistol_lock.json', 'w'), indent=1, default=str); print('LYRA_CR_PISTOL_LOCK', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
