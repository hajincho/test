"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 3인칭 상체 비틀기(소총을 어깨에 대는 자세).
오른쪽 어깨를 앞으로(총 쪽), 왼쪽 어깨를 뒤로 빼도록 spine_03 을 수직축(컴포넌트 Z)으로 -도(시계 방향, 위에서 볼 때) 회전시킨다.
회전은 propagate 라서 spine_03 위쪽(가슴, 어깨, 머리, 팔)이 함께 돌고 골반/다리는 그대로다. 가중치 = TpW(3인칭 가중, 정조준이면 0).
실행 순서: 머리 조준(HeadAim, 팔보다 먼저 실행되며 눈 위치가 최종 머리를 보게 하는 노드) 바로 앞에 끼워 넣어, 눈/총/손 위치가 비틀린 몸을 기준으로 계산되게 한다.
노드: TwAng(TpW x -도 라디안), TwQ(Z축 회전), TwXf(spine_03 월드 변환), TwRot(TwQ x 현재 회전), TwSet(SetRotation, propagate).  각도는 DEG 값(기본 14)  -> Data/lyra_torso_twist.json"""
import unreal, json, sys, math, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_torso_twist.json'
R = {}
DEG = 14.0
BONE = 'Spine'   # CR 계층(SK_Furina)의 뼈 이름. Manny 이름(spine_03)은 CR 에 없어 처음엔 아무 효과가 없었다
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    nodes = {str(n.get_node_path()): n for n in g.get_nodes()}
    R['has'] = 'TwSet' in nodes
    if not R['has']:
        U = '/Script/ControlRig.RigUnit_'
        for typ, nm in (('MathFloatMul', 'TwAng'), ('MathQuaternionFromAxisAndAngle', 'TwQ'), ('GetTransform', 'TwXf'), ('MathQuaternionMul', 'TwRot'), ('SetRotation', 'TwSet')):
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
        L = [c.add_link('TpW.Result', 'TwAng.A'), c.add_link('TwAng.Result', 'TwQ.Angle'), c.add_link('TwQ.Result', 'TwRot.A'), c.add_link('TwXf.Transform.Rotation', 'TwRot.B'), c.add_link('TwRot.Result', 'TwSet.Value')]
        R['links'] = [bool(x) for x in L]
        R['axis'] = bool(c.set_pin_default_value('TwQ.Axis', '(X=0.0,Y=0.0,Z=1.0)', True, False))
        R['items'] = [bool(c.set_pin_default_value('TwXf.Item', '(Type=Bone,Name="%s")' % BONE, True, False)), bool(c.set_pin_default_value('TwSet.Item', '(Type=Bone,Name="%s")' % BONE, True, False)),
                      bool(c.set_pin_default_value('TwXf.Space', 'GlobalSpace', True, False)), bool(c.set_pin_default_value('TwSet.Space', 'GlobalSpace', True, False)), bool(c.set_pin_default_value('TwSet.bPropagateToChildren', 'True', True, False))]
    # 실행 흐름: HeadAim 바로 앞에 TwSet 끼워 넣기(이미 끼워져 있으면 건너뜀)
    nodes = {str(n.get_node_path()): n for n in g.get_nodes()}
    R['head_aim_pins'] = [str(p.get_name()) for p in nodes['HeadAim'].get_pins()][:12]
    R['twset_pins'] = [str(p.get_name()) for p in nodes['TwSet'].get_pins()][:12]
    def exec_pin(node):
        for p in node.get_pins():
            if 'Execute' in str(p.get_name()): return p
    ha = exec_pin(nodes['HeadAim']); tw = exec_pin(nodes['TwSet'])
    R['ha_exec_name'] = str(ha.get_name()) if ha else None
    tw_srcs = [str(s.get_pin_path()) for s in tw.get_linked_source_pins()] if tw else []
    if ha and tw and not tw_srcs:
        srcs = [str(s.get_pin_path()) for s in ha.get_linked_source_pins()]; R['head_aim_exec_from'] = srcs
        for s in srcs:
            R.setdefault('exec', []).append([bool(c.break_link(s, str(ha.get_pin_path()))), bool(c.add_link(s, str(tw.get_pin_path())))])
        R['exec_tail'] = bool(c.add_link(str(tw.get_pin_path()), str(ha.get_pin_path())))
    R['twset_exec_from'] = [str(s.get_pin_path()) for s in tw.get_linked_source_pins()] if tw else None
    R['headaim_exec_from'] = [str(s.get_pin_path()) for s in ha.get_linked_source_pins()] if ha else None
    R['bone_items'] = [bool(c.set_pin_default_value('TwXf.Item', '(Type=Bone,Name="%s")' % BONE, True, False)), bool(c.set_pin_default_value('TwSet.Item', '(Type=Bone,Name="%s")' % BONE, True, False))]
    R['deg'] = DEG; R['angle_set'] = bool(c.set_pin_default_value('TwAng.B', '%.6f' % math.radians(-DEG), True, False))
    cr.recompile_vm(); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(cr, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_TWIST', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
