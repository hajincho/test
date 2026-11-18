"""Lyra 에디터(`py <파일>`): 재장전 중 왼손 엄지를 평상시 자세로 고정해 '엄지 까딱' 제거.
 원인(PIE 측정 lyra_thumb_probe_thFP2.json): 일반 재장전 끝(탄창 장착 직후 2.3~2.5초)에 템플릿 재장전 애니메이션이 엄지를 손목 기준 최대 58° 돌렸다가 0.06초 만에 평상시 자세(약 45° 되돌림)로 뚝 끊어 놓는다.
 CR 은 엄지를 건드리지 않았다(검지~소지만 손가락 IK/감싸기).  수정: 재장전 중(가중치 ReloadSm) Thumb0/1/2_L 의 로컬 회전을 평상시 값(Data/thumb_rest.json: PIE 에서 읽은 부모 본 기준 회전)으로 덮어쓴다.
 노드: ThSet0/1/2 (SetRotation Local, Weight = ReloadSm).  실행 순서: RLArmIK -> ThSet0 -> ThSet1 -> ThSet2 -> (원래 다음).   -> Data/lyra_thumb_hold.json"""
import unreal, json, os, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; OUT = D + r'\lyra_thumb_hold.json'
U = '/Script/ControlRig.RigUnit_'
R = {}
def run():
    q = json.load(open(D + r'\thumb_rest.json'))
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('RLArmIK', 'ReloadSm'): assert need in N, 'missing ' + need
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    chain = []
    for i, b in enumerate(('Thumb0_L', 'Thumb1_L', 'Thumb2_L')):
        nm = 'ThSet%d' % i; chain.append(nm)
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + 'SetRotation', 'Execute', unreal.Vector2D(0, 0), nm)
            c.set_pin_default_value(nm + '.Item', '(Type=Bone,Name="%s")' % b, True, False)
            c.set_pin_default_value(nm + '.Space', 'LocalSpace', True, False)
            c.set_pin_default_value(nm + '.Value', '(X=%.8f,Y=%.8f,Z=%.8f,W=%.8f)' % tuple(q[b]), True, False)
            c.set_pin_default_value(nm + '.bPropagateToChildren', 'True', True, False)
            link('ReloadSm.Result', nm + '.Weight')
        else: c.set_pin_default_value(nm + '.Value', '(X=%.8f,Y=%.8f,Z=%.8f,W=%.8f)' % tuple(q[b]), True, False)
    if 'ThSet0' not in N:
        N = nodes()
        ik = [p for p in N['RLArmIK'].get_pins() if str(p.get_name()) == 'ExecutePin'][0]; nxt = [str(t.get_pin_path()) for t in ik.get_linked_target_pins()]; R['next'] = nxt
        for t in nxt:
            try: L.append(['x', t, bool(c.break_link('RLArmIK.ExecutePin', t))])
            except Exception as e: L.append(['x', t, 'err ' + str(e)[:60]])
        prev = 'RLArmIK.ExecutePin'
        for nd in chain: link(prev, nd + '.ExecutePin'); prev = nd + '.ExecutePin'
        for t in nxt: link(prev, t)
    R['links'] = L; R['q'] = q
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_THUMB_HOLD', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
