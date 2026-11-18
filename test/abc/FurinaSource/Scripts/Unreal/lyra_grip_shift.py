"""Lyra 에디터(`py <파일> [D] [fit]`, PIE 중지 상태): 오른손이 권총손잡이를 제대로 쥐도록 소총을 손에 대해 총 앞방향(+Y)으로 D cm 옮기고, 왼손 목표도 같은 D 만큼 앞으로 옮긴다.
측정(Data/lyra_hand_bones.json, Blender 손잡이 단면): 오른손 손가락 뿌리(MiddleFinger1_R/IndexFinger1_R)가 소총 기준 y≈-3.8 (탄창 뒤, 방아쇠 앞)에 있고,
 권총손잡이 앞면은 z -5.5 에서 y -11.5 → 손이 손잡이보다 약 7.3cm 앞을 잡고 있었다.
방법: (1) 폰 BP(ThirdPersonCharacter_BP)의 FurinaRifle 상대 변환(오른손목 기준)을 총 로컬 +Y 로 D 이동 → 손은 그대로, 총이 D 앞으로 → 손잡이가 손바닥으로 온다.
      (2) CR_FurinaSecondary 의 왼손 목표 LHandOff.A/B(총 기준점 좌표, Y=앞)에 +D → 왼손도 총의 같은 자리를 잡도록 같이 앞으로.
      팔이 모자라면 CR 의 기존 왼어깨 당김(LShOver, 37cm 초과분만큼 어깨를 목표 쪽으로)과 3인칭 상체 비틀기(TwSet)가 받는다.
원래 값은 Data/lyra_grip_shift_orig.json 에 처음 한 번 저장하고 항상 그 값 + D 로 설정(누적 안 됨). D=0 이면 원상 복구. `fit`: 쓰지 않고 보고만.
-> Data/lyra_grip_shift.json"""
import unreal, json, sys, os, traceback
D_DIR = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
OUT = D_DIR + r'\lyra_grip_shift.json'; ORIG = D_DIR + r'\lyra_grip_shift_orig.json'
D = 7.3
for a in sys.argv[1:]:
    try: D = float(a)
    except ValueError: pass
R = {'D': D}
def v3(v): return [round(v.x, 4), round(v.y, 4), round(v.z, 4)]
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary; rifle = None
    for h in S.k2_gather_subobject_data_for_blueprint(bp):
        if str(L.get_variable_name(L.get_data(h))) == 'FurinaRifle': rifle = L.get_associated_object(L.get_data(h))
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller()
    nodes = {str(n.get_node_path()): n for n in c.get_graph().get_nodes()}
    def pin(node, name): return [str(p.get_default_value()) for p in nodes[node].get_pins() if str(p.get_name()) == name][0]
    def parse(s):
        d = {}
        for kv in s.strip('()').split(','):
            k, v = kv.split('='); d[k.strip()] = float(v)
        return [d['X'], d['Y'], d['Z']]
    # 이벤트 그래프에서 FurinaRifle 을 다시 붙이거나 상대 위치를 바꾸는 노드가 있는지 보고(있으면 그쪽도 고쳐야 함)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); hits = []
    for n in ed.list_all_nodes():
        try: t = str(n.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace('\n', ' ')
        except Exception: t = ''
        if any(k in t for k in ('Attach', 'Relative', 'Socket')):
            try:
                pins = [[str(p.get_pin_name()), str(p.get_pin_value())[:40], [x.get_owning_node().get_name() for x in p.list_connected_pins()][:2]] for p in n.list_all_pins()]
                if any('Rifle' in str(pp) for pp in pins): hits.append({'node': n.get_name(), 'title': t[:60], 'pins': [pp for pp in pins if pp[1] or pp[2]][:8]})
            except Exception: pass
    R['rifle_attach_nodes'] = hits
    if os.path.exists(ORIG): O = json.load(open(ORIG, encoding='utf-8'))
    else:
        rl = rifle.get_editor_property('relative_location'); rr = rifle.get_editor_property('relative_rotation')
        O = {'rifle_loc': v3(rl), 'rifle_rot': [rr.roll, rr.pitch, rr.yaw], 'LHandOff.A': parse(pin('LHandOff', 'A')), 'LHandOff.B': parse(pin('LHandOff', 'B'))}
        json.dump(O, open(ORIG, 'w', encoding='utf-8'), indent=1)
    R['orig'] = O
    rot = unreal.Rotator(roll=O['rifle_rot'][0], pitch=O['rifle_rot'][1], yaw=O['rifle_rot'][2])
    rel = unreal.Transform(unreal.Vector(*O['rifle_loc']), rot, unreal.Vector(1, 1, 1))
    new_loc = unreal.MathLibrary.transform_location(rel, unreal.Vector(0, D, 0))   # 총 로컬 +Y(앞)로 D
    R['new_rifle_loc'] = v3(new_loc)
    la = O['LHandOff.A']; lb = O['LHandOff.B']
    NA = '(X=%.4f,Y=%.4f,Z=%.4f)' % (la[0], la[1] + D, la[2]); NB = '(X=%.4f,Y=%.4f,Z=%.4f)' % (lb[0], lb[1] + D, lb[2])
    R['new_LHandOff'] = [NA, NB]
    if 'fit' not in sys.argv:
        rifle.set_editor_property('relative_location', new_loc)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['bp_saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(bp, False))
        R['set_l'] = [bool(c.set_pin_default_value('LHandOff.A', NA, True, False)), bool(c.set_pin_default_value('LHandOff.B', NB, True, False))]
        cr.recompile_vm(); R['cr_saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
        R['after'] = {'rifle_loc': v3(rifle.get_editor_property('relative_location')), 'LHandOff.A': pin('LHandOff', 'A')}
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_GRIP_SHIFT', R.get('D'), R.get('error', '')[-200:])
