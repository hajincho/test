"""Lyra 에디터(`py <파일> comp|tick`, 새로 시작한 에디터에서, 한 번에 한 단계): 장전손잡이 컴포넌트와 곡선 구동을 ThirdPersonCharacter_BP 에 넣는다.
 comp : 컴포넌트 FurinaHandle(SM_M4Handle, 부모 FurinaRifle, 소총과 같은 위치), 렌더 설정은 FurinaBolt 에서 복사
 tick : FBX_SetVis(노리쇠 틱의 끝) 뒤에 이어서: 곡선 HandleBack(0~1) x -5.9cm 를 FurinaHandle 의 상대 Y 로 설정, 권총 장착 중이면 숨김.  노드 이름 FBH_*
 (규칙: 지운 노드와 같은 이름을 쓰면 에디터가 죽는다 / 'float' 변수는 정수가 된다 / 전역에 노드 객체를 남기지 않는다)   -> Data/lyra_handle_graph.json"""
import unreal, json, sys, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_handle_graph.json'
STEP = [a for a in sys.argv[1:] if a in ('comp', 'tick')]; STEP = STEP[0] if STEP else 'comp'
PULL = 5.9
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'step': STEP}
def run():
    bp = unreal.load_asset(PAWN)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    def comp(name): return lib.get_associated_object(lib.get_data(handles()[name]))
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name); return p
    def link(a, b):
        assert a is not None and b is not None and a.is_valid() and b.is_valid(), ('link: 핀이 없음', a, b); assert CONN(a, b)
    if STEP == 'comp':
        if 'FurinaHandle' in handles(): R['comp'] = 'exists'
        else:
            h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()['FurinaRifle'], new_class=unreal.StaticMeshComponent, blueprint_context=bp)); sub.rename_subobject(h, unreal.Text('FurinaHandle'))
            b = comp('FurinaHandle'); m = comp('FurinaBolt'); b.set_editor_property('static_mesh', unreal.load_asset('/Game/Furina/M4/SM_M4Handle'))
            b.set_editor_property('relative_location', unreal.Vector(0, 0, 0)); b.set_editor_property('relative_rotation', unreal.Rotator(roll=0, pitch=0, yaw=0)); b.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1))
            b.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); copied = []
            for pn in ('cast_shadow', 'render_in_main_pass', 'render_in_depth_pass', 'owner_no_see', 'only_owner_see', 'visible', 'hidden_in_game', 'cast_contact_shadow', 'cast_dynamic_shadow', 'receives_decals', 'visible_in_ray_tracing', 'lighting_channels', 'cast_hidden_shadow', 'use_as_occluder'):
                try: b.set_editor_property(pn, m.get_editor_property(pn)); copied.append(pn)
                except Exception: pass
            R['comp'] = ['added', copied]
        BEL.compile_blueprint(bp)
    else:
        ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
        if 'FBH_SetLoc' in N: R['tick'] = 'exists'
        else:
            K = '/Script/Engine.KismetMathLibrary:'
            def fn(name, path):
                n = ed.add_call_function_node(path); assert n, path; n.rename(name); return n
            curve = fn('FBH_Curve', '/Script/Engine.AnimInstance:GetCurveValue'); pin(curve, 'CurveName').set_pin_value('HandleBack'); link(pin(N['FMG_Anim'], 'ReturnValue', True), curve.find_self_pin())
            ys = fn('FBH_Y', K + 'Multiply_DoubleDouble'); link(pin(curve, 'ReturnValue', True), pin(ys, 'A')); pin(ys, 'B').set_pin_value('%.3f' % -PULL)
            vec = fn('FBH_Vec', K + 'MakeVector'); link(pin(ys, 'ReturnValue', True), pin(vec, 'Y')); pin(vec, 'X').set_pin_value('0.0'); pin(vec, 'Z').set_pin_value('0.0')
            hg = ed.add_get_member_variable_node('FurinaHandle'); hg.rename('FBH_HandleGet')
            sl = fn('FBH_SetLoc', '/Script/Engine.SceneComponent:K2_SetRelativeLocation'); pin(sl, 'bSweep').set_pin_value('false'); pin(sl, 'bTeleport').set_pin_value('true')
            link(pin(hg, 'FurinaHandle', True), sl.find_self_pin()); link(pin(vec, 'ReturnValue', True), pin(sl, 'NewLocation'))
            hg2 = ed.add_get_member_variable_node('FurinaHandle'); hg2.rename('FBH_HandleGet2')
            sv = fn('FBH_SetVis', '/Script/Engine.SceneComponent:SetVisibility'); pin(sv, 'bPropagateToChildren').set_pin_value('false')
            link(pin(hg2, 'FurinaHandle', True), sv.find_self_pin()); link(pin(N['FBX_NotPistol'], 'ReturnValue', True), pin(sv, 'bNewVisibility'))
            last = N['FBX_SetVis']; old = list(last.find_then_pin().list_connected_pins()); assert old
            last.find_then_pin().break_pin_links(); link(last.find_then_pin(), sl.find_execute_pin()); link(sl.find_then_pin(), sv.find_execute_pin())
            for p in old: link(sv.find_then_pin(), p)
            R['tick'] = ['added', [p.get_owning_node().get_name() for p in old]]
        del ed, N
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp, sub, lib
try: run()
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_HANDLE_GRAPH', R.get('step'), R.get('status'), R.get('error', ''))
import gc; gc.collect()
