"""Lyra 에디터(`py <파일>`, 새로 시작한 에디터에서 이 스크립트만 한 번): ABP_Furina 의 ModifyCurve_ViewState 에 곡선 'PistolOn' 추가 (ue_prone_abp.py 와 같은 방식).
 곡선 이름: ViewTP, Crouch, Zip, FireHold, Prone, PistolOn   PistolOn = IsActive(FindComponentByTag(Owner, 'FurinaPistolOn')) -> 0/1
 컨트롤 릭이 권총 장착 여부(1인칭 양손 파지)를 알 수 있게 한다.   -> Data/lyra_abp_pistol_curve.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    ab = unreal.load_asset('/Game/Furina/ABP_Furina')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ab, 'AnimGraph')
    n = next(n for n in unreal.AnimationLibrary.get_nodes_of_class(ab, unreal.AnimGraphNode_ModifyCurve, True) if n.get_name().endswith('ViewState'))
    v = n.get_editor_property('node'); text = v.export_text(); R['text_before'] = text[-300:]
    if '"PistolOn"' not in text:
        assert 'CurveNames=("ViewTP","Crouch","Zip","FireHold","Prone")' in text, text[-300:]
        text = text.replace('CurveValues=(0.000000,0.000000,0.000000,0.000000,0.000000)', 'CurveValues=(0.000000,0.000000,0.000000,0.000000,0.000000,0.000000)').replace('CurveNames=("ViewTP","Crouch","Zip","FireHold","Prone")', 'CurveNames=("ViewTP","Crouch","Zip","FireHold","Prone","PistolOn")')
        assert v.import_text(text); n.set_editor_property('node', v)
        old = n.get_editor_property('initial_update_function').copy(); tmp = old.copy()
        tmp.import_text('(MemberName="FurinaReconstructTemporary")'); n.set_editor_property('initial_update_function', tmp); n.set_editor_property('initial_update_function', old)
    R['pins'] = [str(p.get_pin_name()) for p in n.list_all_pins()]
    an = {x.get_name(): x for x in ed.list_all_nodes()}
    owner = an.get('TFPOwner') or an.get('FurinaCrouchOwner') or an.get('K2Node_FPAA_Owner'); R['owner'] = owner.get_name() if owner else None
    def acall(name, path):
        a = an.get(name)
        if not a: a = ed.add_call_function_node(path); assert a, path; a.rename(name); an[name] = a
        return a
    find = acall('FurinaPistolCvFind', '/Script/Engine.Actor:FindComponentByTag'); find.find_input_pin('ComponentClass').set_pin_value('/Script/Engine.ActorComponent'); find.find_input_pin('Tag').set_pin_value('FurinaPistolOn')
    act = acall('FurinaPistolCvActive', '/Script/Engine.ActorComponent:IsActive'); cv = acall('FurinaPistolCvFloat', '/Script/Engine.KismetMathLibrary:Conv_BoolToDouble')
    for a, b in [(owner.find_output_pin('ReturnValue'), find.find_input_pin('self')), (find.find_output_pin('ReturnValue'), act.find_input_pin('self')), (act.find_output_pin('ReturnValue'), cv.find_input_pin('InBool')), (cv.find_output_pin('ReturnValue'), n.find_input_pin('CurveValues_5'))]:
        assert a is not None and b is not None and unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), ('abp link', a, b)
    del ed, n, v, an, owner, find, act, cv
    unreal.BlueprintEditorLibrary.compile_blueprint(ab); R['abp_status'] = str(ab.get_editor_property('status'))
    if ab.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['abp_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(ab, False)
    del ab
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\lyra_abp_pistol_curve.json', 'w'), indent=1); print('LYRA_ABP_PISTOL_CURVE', R.get('abp_status'), R.get('error', '')[-400:])
import gc; gc.collect()
