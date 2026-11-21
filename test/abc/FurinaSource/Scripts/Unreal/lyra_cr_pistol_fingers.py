"""Lyra 에디터(`py <파일> [태그]`, 기본 g17): 1인칭 권총 파지 손가락 - Blender 최적화(Scripts/Blender/pistol_finger_author.py -> Data/pistol_finger_author_<태그>.json)가 구한
 마디별 굽힘 증분(Δ도)을 CR 에서 뼈 로컬 회전에 더한다:   SetRotation(Local) = GetTransform(Local).Rotation x FromAxisAndAngle(뼈 로컬 굽힘 축, Δ),  Weight = PistW.
 삽입 위치: 마지막 손가락 노드(Fing_LittleFinger3_L) 뒤, SetHairFlow 앞 (왼손은 소총용 Fing_* 감기/엄지 고정 위에 더해짐 - 측정 당시와 같은 상태).
 노드: PgG_<뼈>/PgQ_<뼈>/PgM_<뼈>/PgS_<뼈>.   다시 실행하면 값만 갱신.   -> Data/lyra_cr_pistol_fingers.json"""
import unreal, json, sys, math, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
U = '/Script/ControlRig.RigUnit_'
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; TAG = ARGS[0] if ARGS else 'g17'; HAND = ARGS[1] if len(ARGS) > 1 else 'RL'
A = json.load(open(D + r'\pistol_finger_author_%s.json' % TAG)); R = {'tag': TAG, 'hand': HAND, 'bones': [], 'prog': []}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes(); assert 'PistW' in N and 'SetHairFlow' in N
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    def mk(typ, nm):
        if nm not in nodes(): c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
    todo = []
    for key, v in A['fingers'].items():
        if key[0] not in HAND: continue
        dd = v['delta_deg']; names = sorted(v['axis_local'].keys(), key=lambda s: s)
        if key.endswith('Thumb'): order = ['Thumb0_%s' % key[0], 'Thumb1_%s' % key[0], 'Thumb2_%s' % key[0]]
        else:
            f = key[1:]; order = ['%sFinger%d_%s' % (f, i, key[0]) for i in (1, 2, 3)]
        for bn, ang in zip(order, dd):
            if abs(ang) < 1e-6: continue
            todo.append((bn, v['axis_local'][bn], ang))
    first = None; prev = None
    for bn, ax, ang in todo:
        for typ, pre in (('GetTransform', 'PgG_'), ('MathQuaternionFromAxisAndAngle', 'PgQ_'), ('MathQuaternionMul', 'PgM_'), ('SetRotation', 'PgS_')): mk(typ, pre + bn)
        c.set_pin_default_value('PgG_%s.Item' % bn, '(Type=Bone,Name="%s")' % bn, True, False); c.set_pin_default_value('PgG_%s.Space' % bn, 'LocalSpace', True, False)
        c.set_pin_default_value('PgQ_%s.Axis' % bn, '(X=%.6f,Y=%.6f,Z=%.6f)' % tuple(ax), True, False); c.set_pin_default_value('PgQ_%s.Angle' % bn, '%.6f' % math.radians(ang), True, False)
        c.set_pin_default_value('PgS_%s.Item' % bn, '(Type=Bone,Name="%s")' % bn, True, False); c.set_pin_default_value('PgS_%s.Space' % bn, 'LocalSpace', True, False); c.set_pin_default_value('PgS_%s.bPropagateToChildren' % bn, 'True', True, False)
        if 'PgS_%s' % bn not in N:
            link('PgG_%s.Transform.Rotation' % bn, 'PgM_%s.A' % bn); link('PgQ_%s.Result' % bn, 'PgM_%s.B' % bn); link('PgM_%s.Result' % bn, 'PgS_%s.Value' % bn); link('PistW.Result', 'PgS_%s.Weight' % bn)
        R['bones'].append([bn, [round(x, 3) for x in ax], ang]); R['prog'].append(bn); json.dump(R, open(D + r'\lyra_cr_pistol_fingers.json', 'w'), indent=1, default=str)
        todo_node = 'PgS_%s' % bn
        if prev is None: first = todo_node
        else:
            if 'PgS_%s' % bn not in N: link(prev + '.ExecutePin', todo_node + '.ExecutePin')
        prev = todo_node
    # 실행 선 삽입: (SetHairFlow 로 가던 노드) -> first ... prev -> SetHairFlow
    if todo and first and 'PgS_' + todo[0][0] not in N:
        N2 = nodes(); src = None
        for nm, n in N2.items():
            for p in n.get_pins():
                if str(p.get_name()) == 'ExecutePin':
                    for t in p.get_linked_target_pins():
                        if str(t.get_pin_path()) == 'SetHairFlow.ExecutePin': src = nm
        R['src_exec'] = src
        assert src, 'SetHairFlow 앞 노드를 못 찾음'
        c.break_link(src + '.ExecutePin', 'SetHairFlow.ExecutePin'); link(src + '.ExecutePin', first + '.ExecutePin'); link(prev + '.ExecutePin', 'SetHairFlow.ExecutePin')
    R['links_fail'] = [l for l in L if l[2] is not True]
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\lyra_cr_pistol_fingers.json', 'w'), indent=1, default=str); print('LYRA_CR_PISTOL_FINGERS', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
