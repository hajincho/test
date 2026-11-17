"""P220(.45 ACP, 230gr FMJ) 용 총알/탄피 블루프린트를 소총용에서 복제해 값만 바꾼다. (열린 에디터, Remote Execution)
 - BP_P220Bullet: 초기 속도 255 m/s (112 mm 배럴 .45 ACP 230gr ~ 835 fps), 항력 K = rho*Cd*A/(2m) = 1.2*0.35*1.04e-4/(2*0.0149) = 1.466e-3 /m -> 1.466e-5 /cm
                  (dv/dt = -K v^2, 소총 BP 의 Tick 항력식 그대로), 중력 1.0 (980 cm/s^2) => 낙차 자동 반영, 수명 3 s
 - BP_P220Case: SM_223Case 를 .45 ACP 비율(길이 22.8/44.7, 직경 12.1/9.6)로 축소/확대"""
import unreal, json, traceback
EAL = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary
ROOT = '/Game/Furina/P200'
R = {'log': []}
def dup(src, dst):
    if EAL.does_asset_exist(dst): EAL.delete_asset(dst)
    assert EAL.duplicate_asset(src, dst), 'dup ' + dst
    return unreal.load_asset(dst)
def sub_obj(bp, name):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        d = lib.get_data(h)
        if str(lib.get_variable_name(d)) == name: return lib.get_associated_object(d)
def set_float_pin(ed, node, pin, val):
    n = {x.get_name(): x for x in ed.list_all_nodes()}[node]; p = n.find_input_pin(pin); p.set_pin_value(repr(float(val)))
    got = str(p.get_pin_value())
    if got in ('', '0.0') and float(val) != 0.0:     # 핀 값 설정이 무시되는 경우 -> 상수 노드로 연결
        lit = ed.add_call_function_node('/Script/Engine.KismetSystemLibrary:MakeLiteralDouble'); lit.rename('P220_Lit_%s_%s' % (node, pin))
        lit.find_input_pin('Value').set_pin_value(repr(float(val)))
        p.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(lit.find_result_pin(), p), 'lit link'
        got = 'literal ' + str(lit.find_input_pin('Value').get_pin_value())
    return got
def bullet():
    bp = dup('/Game/Furina/FP/BP_FurinaBullet', ROOT + '/BP_P220Bullet')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    R['log'].append(['drag K', set_float_pin(ed, 'K2Node_FPB_Kv', 'B', 1.466e-05)])
    R['log'].append(['tracer ref speed', set_float_pin(ed, 'K2Node_FPB_Flown', 'B', 25500.0)])
    R['log'].append(['tracer max len', set_float_pin(ed, 'K2Node_FPB_Len0', 'B', 600.0)])
    pm = sub_obj(bp, 'Ballistics'); pm.set_editor_property('initial_speed', 25500.0); pm.set_editor_property('projectile_gravity_scale', 1.0)
    R['log'].append(['speed', pm.get_editor_property('initial_speed'), 'max', pm.get_editor_property('max_speed')])
    cdo = unreal.get_default_object(bp.generated_class()); cdo.set_editor_property('initial_life_span', 3.0)
    BEL.compile_blueprint(bp); R['log'].append(['bullet status', str(bp.get_editor_property('status'))]); EAL.save_loaded_asset(bp, False)
def case():
    bp = dup('/Game/Furina/M4/BP_223Case', ROOT + '/BP_P220Case')
    m = sub_obj(bp, 'FXMesh'); sm = m.get_editor_property('static_mesh'); ext = sm.get_bounds().box_extent
    R['log'].append(['case extent', str(ext), 'scale before', str(m.get_editor_property('relative_scale3d'))])
    axes = [ext.x, ext.y, ext.z]; long_i = axes.index(max(axes))
    k_len, k_dia = 22.8 / 44.7, 12.1 / 9.6
    s = [k_dia] * 3; s[long_i] = k_len
    old = m.get_editor_property('relative_scale3d'); m.set_editor_property('relative_scale3d', unreal.Vector(old.x * s[0], old.y * s[1], old.z * s[2]))
    R['log'].append(['case scale after', str(m.get_editor_property('relative_scale3d')), 'long axis', long_i])
    BEL.compile_blueprint(bp); R['log'].append(['case status', str(bp.get_editor_property('status'))]); EAL.save_loaded_asset(bp, False)
try: bullet(); case()
except Exception: R['error'] = traceback.format_exc()
print('P220_BULLET_CASE', json.dumps(R, default=str, ensure_ascii=False)[:2500])
