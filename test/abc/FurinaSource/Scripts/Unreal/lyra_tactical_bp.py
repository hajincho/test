"""Lyra 에디터(`py <파일> [revert]`, 새로 시작한 에디터에서 이 스크립트만 한 번): 전술 재장전을 3.69초로 늘린다.
 - K2Node_FP_ReloadMontage(소총 일반 재장전 몽타주 재생)의 InPlayRate 1.0 -> 0.85  (AS 길이 3.133초 -> 3.686초)
 - 재장전 타이머 시간을 고르는 P2_SelF_5ce19d38 의 소총용 값 3.0 -> 3.69 (권총 값은 그대로).  긴급 재장전(2.0초)은 FBX_/FBT_EmptyCond 선택이 따로 있어 영향 없음.
 변경 전 값은 JSON 에 기록.   -> Data/lyra_tactical_bp.json"""
import unreal, json, sys, traceback
REVERT = 'revert' in sys.argv
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_tactical_bp.json'
RATE = 1.0 if REVERT else 0.85; TIME = 3.0 if REVERT else 3.69; OLD = 3.69 if REVERT else 3.0   # revert: 전술 재장전을 옛 방식(속도 1.0, 3.0초)으로
R = {}
def run():
    bp = unreal.load_asset(PAWN); BEL = unreal.BlueprintEditorLibrary
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    m = N['K2Node_FP_ReloadMontage']; p = m.find_input_pin('InPlayRate'); R['rate_before'] = str(p.get_pin_value()); p.set_pin_value('%.2f' % RATE); R['rate_after'] = str(p.get_pin_value())
    s = N['P2_SelF_5ce19d38']; pins = []
    for q in s.list_all_pins():
        nm = str(q.get_pin_name()); pins.append([nm, str(q.get_pin_value()), [c.get_owning_node().get_name() + '.' + str(c.get_pin_name()) for c in q.list_connected_pins()]])
    R['sel_pins'] = pins
    done = []
    for q in s.list_all_pins():
        if str(q.get_pin_name()) in ('A', 'B') and not list(q.list_connected_pins()):
            try: v = float(str(q.get_pin_value()))
            except Exception: continue
            if abs(v - OLD) < 1e-6: q.set_pin_value('%.2f' % TIME); done.append(str(q.get_pin_name()))
    R['time_pins_changed'] = done
    del ed, N, m, p, s
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_TACTICAL_BP', R.get('status'), R.get('time_pins_changed'), R.get('error', ''))
import gc; gc.collect()
