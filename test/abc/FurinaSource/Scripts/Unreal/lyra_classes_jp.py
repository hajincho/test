"""에디터(편집 전용, PIE 아님, 2026-11-22): 대일본제국 병과 캐릭터 7종 -> Saved/ClassesJP.json("done": true)
 Blender build_class_on_furina.py -- jp_<병과> build 결과(FBX/Classes/jp_*_cm.fbx). 키(의상 포함, 받은 압축 이름): 장교 아야토 187, 보병 토마 186, 돌격병 헤이조 166,
 대전차병 요이미야 163, 중화기병 라이덴 177, 저격수 사라 178, 기갑병 이토 190.
 1) 텍스처·재질(lyra_classes.import_class) -> 자기 뼈대 메시 SKM_<Key>(lyra_class_skeletons.import_class: 푸리나 뼈대와 호환, 몸 뼈 이동 = 이 캐릭터 길이)
 2) 캐릭터 BP 이벤트 FurinaLook<Key>(외형 값 jpofficer 등: 1인칭 팔 슬롯 CA<Key>_ 과 대소문자 무시로 맞음)
 3) 무기창: 제3제국 줄 아래 '병과 (외형) - 대일본제국' 줄(Look_8..14) + 클릭 로직"""
import json, sys, time, traceback, uuid
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib, lyra_fpvm_optics, lyra_classes, lyra_class_skeletons
for _m in (lyra_fpvm_optics, lyra_classes, lyra_class_skeletons): importlib.reload(_m)
from lyra_fpvm_optics import ENGINE, MATH, PAWN, Graph, wire
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
ASSETS = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary
BASE = '/Game/Furina/Classes'; MENU = '/Game/Furina/UI/WBP_FurinaWeaponMenu'
JP = [('jp_officer', 'JpOfficer', '장교', '아야토', 187), ('jp_infantry', 'JpInfantry', '보병', '토마', 186), ('jp_assault', 'JpAssault', '돌격병', '헤이조', 166),
      ('jp_antitank', 'JpAntiTank', '대전차병', '요이미야', 163), ('jp_heavy', 'JpHeavy', '중화기병', '라이덴', 177), ('jp_sniper', 'JpSniper', '저격수', '사라', 178),
      ('jp_armor', 'JpArmor', '기갑병', '이토', 190)]
TOK = '%x' % (int(time.time()) % 0xFFFFF)


def assets():
    body = lyra_class_skeletons.body_bones(); out = {}
    for key, Key, *_ in JP:
        out[key] = {'tmp': lyra_classes.import_class(key, Key), 'skm': lyra_class_skeletons.import_class(key, Key, body)}
        tmp = f'{BASE}/{Key}/SK_Class_{Key}'
        if ASSETS.does_asset_exist(tmp): out[key]['tmp_deleted'] = ASSETS.delete_asset(tmp)
    return out


def pawn():
    bp = unreal.load_asset(PAWN); g = Graph(bp, 'LOOK_'); made = []
    for key, Key, *_ in JP:
        if 'LOOK_Set_' + Key in g.nodes: continue
        ev = g.editor.add_custom_event_node('FurinaLook' + Key); assert ev, Key; ev.rename('LOOK_Ev_' + Key)
        setm = g.call('Set_' + Key, ENGINE + 'SkeletalMeshComponent:SetSkeletalMeshAsset', target=g.get('FurinaMesh'), NewMesh=unreal.load_asset(f'{BASE}/{Key}/SKM_{Key}'))
        num = g.call('Num_' + Key, ENGINE + 'PrimitiveComponent:GetNumMaterials', target=g.get('FurinaMesh'))
        last = g.call('Last_' + Key, MATH + 'Subtract_IntInt', A=num.find_result_pin(), B=1)
        loop = g.editor.add_macro_node('/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForLoop'); loop.rename('LOOK_Loop_' + Key)
        loop.find_input_pin('FirstIndex').set_pin_value('0'); wire(last.find_result_pin(), loop.find_input_pin('LastIndex'))
        clear = g.call('Clear_' + Key, ENGINE + 'PrimitiveComponent:SetMaterial', target=g.get('FurinaMesh'))
        wire(loop.find_output_pin('Index'), clear.find_input_pin('ElementIndex')); wire(loop.find_output_pin('LoopBody'), clear.find_execute_pin())
        store = g.store('Store_' + Key, 'FurinaLook', Key.lower())
        wire(ev.find_then_pin(), setm.find_execute_pin()); wire(setm.find_then_pin(), loop.find_input_pin('execute')); wire(loop.find_output_pin('Completed'), store.find_execute_pin())
        made.append('FurinaLook' + Key)
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    assert ASSETS.save_loaded_asset(bp, False); return {'made': made, 'status': str(st)}


def menu():
    wbp = unreal.load_asset(MENU); wt = unreal.find_object(None, MENU + '.WBP_FurinaWeaponMenu:WidgetTree')
    W = {o.get_name(): o for o in unreal.ObjectIterator(unreal.Widget) if o.get_outer() == wt and not o.get_name().startswith(('Old', 'Discarded'))}
    out = {}
    if 'LookRow2' not in W:
        vb = W['VBox']; kids = [vb.get_child_at(i) for i in range(vb.get_children_count())]; pads = [k.slot.get_editor_property('padding') for k in kids]
        mk = lambda cls, nm: unreal.new_object(cls, outer=wt, name=nm); SL = unreal.get_default_object(unreal.SystemLibrary)
        def txt(nm, s, size, bold=False):
            t = mk(unreal.TextBlock, nm); t.set_text(unreal.Text(s)); f = t.get_editor_property('font'); f.set_editor_property('size', size)
            if bold: f.set_editor_property('typeface_font_name', 'Bold')
            t.set_editor_property('font', f); return t
        head = txt('LookHead2', '병과 (외형)  -  대일본제국', 18, True); row = mk(unreal.HorizontalBox, 'LookRow2')
        for j, (key, Key, cls, who, h) in enumerate(JP):
            i = 8 + j; b = mk(unreal.Button, 'Look_%d' % i); b.set_tool_tip_text(unreal.Text(f'외형: {cls} - {who} ({h}cm)'))
            b.add_child(txt('LookTxt_%d' % i, cls, 16)); SL.call_method('SetBoolPropertyByName', (b, 'bIsVariable', True))
            sb = mk(unreal.SizeBox, 'LookBox_%d' % i); sb.set_width_override(150); sb.set_height_override(42); sb.add_child(b)
            row.add_child_to_horizontal_box(sb).set_padding(unreal.Margin(0, 0, 6, 0))
        at = [k.get_name() for k in kids].index('LookRow') + 1
        order = kids[:at] + [head, row] + kids[at:]; opads = pads[:at] + [unreal.Margin(0, 2, 0, 4), unreal.Margin(0, 0, 0, 4)] + pads[at:]
        vb.clear_children()
        for w, p in zip(order, opads): vb.add_child_to_vertical_box(w).set_padding(p)
        BEL.compile_blueprint(wbp); out['layout'] = [w.get_name() for w in order]
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnPreviewMouseButtonDown'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    if any(k.startswith('LK_B_8_') for k in N): return 'exists'
    CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
    def link(a, b): assert a and b and CONN(a, b), ('link', a.get_owning_node().get_name() if a else None)
    last = [n for k, n in N.items() if k.startswith('LK_B_7_')][0]
    cont = list(last.find_else_pin().list_connected_pins()); last.find_else_pin().break_pin_links()
    prev = last.find_else_pin(); pawn_cls = unreal.load_asset(PAWN).generated_class().get_path_name()
    for j, (key, Key, cls, who, h) in enumerate(JP):
        i = 8 + j; bn = 'Look_%d' % i
        g_ = ed.add_get_member_variable_node(bn); assert g_, bn; g_.rename('LK_G_%d_%s' % (i, TOK))
        hv = ed.add_call_function_node('/Script/UMG.Widget:IsHovered'); hv.rename('LK_H_%d_%s' % (i, TOK)); link(g_.find_output_pin(bn), hv.find_self_pin())
        br = ed.add_branch_node(); br.rename('LK_B_%d_%s' % (i, TOK)); link(hv.find_output_pin('ReturnValue'), br.find_input_pin('Condition')); link(prev, br.find_execute_pin())
        op = ed.add_call_function_node('/Script/UMG.UserWidget:GetOwningPlayerPawn'); op.rename('LK_P_%d_%s' % (i, TOK))
        cast = ed.create_node_from_name('Utilities|Casting|CastToThirdPersonCharacter_BP', unreal.Vector2D(600, 300 * i), []); assert cast; cast.rename('LK_C_%d_%s' % (i, TOK))
        link(op.find_output_pin('ReturnValue'), cast.find_input_pin('Object'))
        as_pin = next(p for p in cast.list_output_pins() if str(p.get_pin_name()).startswith('As'))
        call = ed.add_call_function_node(pawn_cls + ':FurinaLook' + Key); assert call, Key; call.rename('LK_E_%d_%s' % (i, TOK)); link(as_pin, call.find_self_pin())
        gc_ = ed.add_get_member_variable_node('LookCurrent'); gc_.rename('LK_T_%d_%s' % (i, TOK))
        st = ed.add_call_function_node('/Script/UMG.TextBlock:SetText'); st.rename('LK_S_%d_%s' % (i, TOK)); link(gc_.find_output_pin('LookCurrent'), st.find_self_pin())
        st.find_input_pin('InText').set_pin_value(f'현재 외형: 대일본제국 {cls} ({who}, {h}cm)')
        for tag, src in (('U', st.find_then_pin()), ('UF', next(p for p in cast.list_output_pins() if str(p.get_pin_name()) == 'CastFailed'))):
            r = ed.add_return_node(); u = ed.add_call_function_node('/Script/UMG.WidgetBlueprintLibrary:Unhandled'); u.rename('LK_%s_%d_%s' % (tag, i, TOK))
            link(u.find_output_pin('ReturnValue'), r.find_input_pin('ReturnValue')); link(src, r.find_execute_pin())
        link(br.find_then_pin(), cast.find_execute_pin()); link(cast.find_then_pin(), call.find_execute_pin()); link(call.find_then_pin(), st.find_execute_pin())
        prev = br.find_else_pin()
    for p in cont: link(prev, p)
    del ed, N
    BEL.compile_blueprint(wbp); s = wbp.get_editor_property('status'); assert s != unreal.BlueprintStatus.BS_ERROR, str(s)
    assert ASSETS.save_loaded_asset(wbp, False); out['status'] = str(s); return out


def run():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    only = [a for a in sys.argv[1:] if not a.endswith('.py')]; want = lambda s: not only or s in only[0].split('+')
    try:
        if want('assets'): R['assets'] = assets()
    finally: unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
    if want('pawn'): R['pawn'] = pawn()
    if want('menu'): R['menu'] = menu()


if __name__ == '__main__':
    try: run()
    except Exception: R['error'] = traceback.format_exc()[-1800:]
    R['done'] = True; (ROOT / 'Saved' / 'ClassesJP.json').write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
    print('CLASSES_JP', json.dumps(R, default=str, ensure_ascii=False)[:2500])
