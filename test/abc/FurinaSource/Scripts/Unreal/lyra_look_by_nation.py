"""에디터(편집 전용, 2026-11-22): 무기창 병과(외형) 버튼 한 줄 + 나라 탭 기준 -> Saved/LookByNation.json
 사용자 지정: 나라별로 두 줄(제3제국 Look_1..7 / 대일본제국 Look_8..14)로 늘어놓지 말고, 위 나라 탭(NationIndex)이 제3제국이면 '장교' -> 독일 장교,
 대일본제국이면 '장교' -> 일본 장교. (캐릭터가 아직 없는 나라 탭에서는 독일 캐릭터)
 - 레이아웃: LookHead 글자 '병과 (외형)  -  위 국가 탭 기준', 일본 줄(LookHead2/LookRow2)은 접음.
 - 클릭 로직(OnPreviewMouseButtonDown): Look_i(1..7) 형변환 성공 뒤 '분기 NationIndex == 1' 을 끼움:
     참 -> FurinaLookJp<Key>(같은 병과) + '현재 외형: 대일본제국 …' 글자,  거짓 -> 기존(독일) 호출. 노드 접두사 LN_."""
import json, sys, time, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import PAWN
from lyra_classes import CLASSES
from lyra_classes_jp import JP, MENU
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}; BEL = unreal.BlueprintEditorLibrary; ASSETS = unreal.EditorAssetLibrary
TOK = '%x' % (int(time.time()) % 0xFFFFF); CONN = unreal.BlueprintGraphPinLibrary.try_create_connection


def link(a, b): assert a and b and CONN(a, b), ('link', a.get_owning_node().get_name() if a else None, b.get_owning_node().get_name() if b else None)


def run():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    wbp = unreal.load_asset(MENU); wt = unreal.find_object(None, MENU + '.WBP_FurinaWeaponMenu:WidgetTree')
    W = {o.get_name(): o for o in unreal.ObjectIterator(unreal.Widget) if o.get_outer() == wt}
    W['LookHead'].set_text(unreal.Text('병과 (외형)  -  위 국가 탭 기준(제3제국 / 대일본제국)'))
    for n in ('LookHead2', 'LookRow2'):
        if n in W: W[n].set_visibility(unreal.SlateVisibility.COLLAPSED)
    for i, (key, Key, cls, who, h) in enumerate(CLASSES, start=1):
        jk = JP[i - 1]; W['Look_%d' % i].set_tool_tip_text(unreal.Text(f'외형: {cls}  -  제3제국 {who}({h}cm) / 대일본제국 {jk[3]}({jk[4]}cm)'))
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnPreviewMouseButtonDown'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    if any(k.startswith('LN_B_') for k in N): R['logic'] = 'exists'
    else:
        pawn_cls = unreal.load_asset(PAWN).generated_class().get_path_name(); out = []
        for i in range(1, 8):
            cast = next(n for k, n in N.items() if k.startswith('LK_C_%d_' % i)); call_de = next(n for k, n in N.items() if k.startswith('LK_E_%d_' % i))
            as_pin = next(p for p in cast.list_output_pins() if str(p.get_pin_name()).startswith('As'))
            then = cast.find_then_pin(); then.break_pin_links()
            gi = ed.add_get_member_variable_node('NationIndex'); gi.rename('LN_N_%d_%s' % (i, TOK))
            eq = ed.add_call_function_node('/Script/Engine.KismetMathLibrary:EqualEqual_IntInt'); eq.rename('LN_Q_%d_%s' % (i, TOK))
            link(gi.find_output_pin('NationIndex'), eq.find_input_pin('A')); eq.find_input_pin('B').set_pin_value('1')
            br = ed.add_branch_node(); br.rename('LN_B_%d_%s' % (i, TOK)); link(eq.find_output_pin('ReturnValue'), br.find_input_pin('Condition'))
            link(then, br.find_execute_pin()); link(br.find_else_pin(), call_de.find_execute_pin())
            jk = JP[i - 1]
            cj = ed.add_call_function_node(pawn_cls + ':FurinaLook' + jk[1]); assert cj, jk[1]; cj.rename('LN_E_%d_%s' % (i, TOK)); link(as_pin, cj.find_self_pin())
            gc = ed.add_get_member_variable_node('LookCurrent'); gc.rename('LN_T_%d_%s' % (i, TOK))
            st = ed.add_call_function_node('/Script/UMG.TextBlock:SetText'); st.rename('LN_S_%d_%s' % (i, TOK)); link(gc.find_output_pin('LookCurrent'), st.find_self_pin())
            st.find_input_pin('InText').set_pin_value(f'현재 외형: 대일본제국 {jk[2]} ({jk[3]}, {jk[4]}cm)')
            r = ed.add_return_node(); u = ed.add_call_function_node('/Script/UMG.WidgetBlueprintLibrary:Unhandled'); u.rename('LN_U_%d_%s' % (i, TOK))
            link(u.find_output_pin('ReturnValue'), r.find_input_pin('ReturnValue'))
            link(br.find_then_pin(), cj.find_execute_pin()); link(cj.find_then_pin(), st.find_execute_pin()); link(st.find_then_pin(), r.find_execute_pin())
            out.append(jk[1])
        R['logic'] = out
    BEL.compile_blueprint(wbp); s = wbp.get_editor_property('status'); R['status'] = str(s); assert s != unreal.BlueprintStatus.BS_ERROR, str(s)
    assert ASSETS.save_loaded_asset(wbp, False)


try: run()
except Exception: R['error'] = traceback.format_exc()[-1800:]
R['done'] = True; (ROOT / 'Saved' / 'LookByNation.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8'); print('LOOK_BY_NATION', json.dumps(R, ensure_ascii=False)[:1500])
