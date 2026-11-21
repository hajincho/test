"""Lyra 에디터(`py <파일> [전술초 빈탄창초]`, 기본 3.3 3.0; 새로 시작한 에디터에서 이 스크립트만 한 번): 소총 재장전 시간을 정한다.
 - 전술 재장전(잔탄>0, 손잡이 안 당김): 몽타주 K2Node_FP_ReloadMontage InPlayRate = 3.133/T (AS 길이 3.133초), 타이머 P2_SelF_5ce19d38 소총값 = T
 - 빈 탄창 재장전(잔탄 0, 손잡이 당김): 몽타주 FBT_EmptyMontage InPlayRate = 2.0/T (구간 2.0초), 타이머 FBT_TimeSel.A = T
 권총 값(P2_SelF A=2.3)은 그대로.  변경 전 값은 JSON 에 기록.   -> Data/lyra_rifle_reload_times.json"""
import unreal, json, sys, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_rifle_reload_times.json'
nums = []
for a in sys.argv[1:]:
    try: nums.append(float(a))
    except ValueError: pass
T_TAC = nums[0] if len(nums) > 0 else 3.3; T_EMP = nums[1] if len(nums) > 1 else 3.0
AS_LEN = 3.133; SEG = 2.0
R = {'tactical_s': T_TAC, 'empty_s': T_EMP}
def run():
    bp = unreal.load_asset(PAWN); BEL = unreal.BlueprintEditorLibrary
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    for need in ('K2Node_FP_ReloadMontage', 'P2_SelF_5ce19d38', 'FBT_EmptyMontage', 'FBT_TimeSel'): assert need in N, 'missing ' + need
    def setpin(node, pin, val, tag):
        p = N[node].find_input_pin(pin); assert p is not None and p.is_valid(), (node, pin)
        R[tag + '_before'] = str(p.get_pin_value()); p.set_pin_value('%.5f' % val); R[tag + '_after'] = str(p.get_pin_value())
    setpin('K2Node_FP_ReloadMontage', 'InPlayRate', AS_LEN / T_TAC, 'tac_rate')
    setpin('FBT_EmptyMontage', 'InPlayRate', SEG / T_EMP, 'emp_rate')
    setpin('FBT_TimeSel', 'A', T_EMP, 'emp_time')
    s = N['P2_SelF_5ce19d38']; pins = []
    for q in s.list_all_pins():
        pins.append([str(q.get_pin_name()), str(q.get_pin_value()), [c.get_owning_node().get_name() + '.' + str(c.get_pin_name()) for c in q.list_connected_pins()]])
    R['sel_pins'] = pins
    cur = []
    for q in s.list_all_pins():
        if str(q.get_pin_name()) in ('A', 'B') and not list(q.list_connected_pins()):
            try: v = float(str(q.get_pin_value()))
            except Exception: continue
            if abs(v - 2.3) > 1e-3:   # 2.3 = 권총 값, 나머지가 소총 값
                q.set_pin_value('%.2f' % T_TAC); cur.append([str(q.get_pin_name()), v, T_TAC])
    R['sel_changed'] = cur
    del ed, N, s
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_RIFLE_RELOAD_TIMES', R.get('status'), R.get('sel_changed'), R.get('error', ''))
import gc; gc.collect()
