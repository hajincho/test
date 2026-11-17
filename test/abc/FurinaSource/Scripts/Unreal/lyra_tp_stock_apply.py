"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): Data/fp_rig.json 의 poses.tp_hip_d / tp_sh_d / tp_lback 값을 CR_FurinaSecondary 의 TpD.A / TpD.B / LBack.B 에 직접 넣는다.
(ue_build_cr.py 전체 재빌드 없이 살아 있는 자산만 바꿈. 3인칭 총 위치(개머리판이 몸을 뚫는 문제) + 왼손 총열 쥐는 위치)   -> Data/lyra_tp_stock_apply.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_tp_stock_apply.json'
R = {}
try:
    SRC = 'fp_rig.before_stock_shift.json' if 'orig' in sys.argv else 'fp_rig.json'   # orig: 이동 전 원래 값(A/B 비교용)
    PO = json.load(open('C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data/' + SRC))['poses']
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); nodes = {str(n.get_node_path()): n for n in c.get_graph().get_nodes()}
    def vec(v): return '(X=%.4f,Y=%.4f,Z=%.4f)' % tuple(v)
    def pin(node, name): return [str(p.get_default_value()) for p in nodes[node].get_pins() if str(p.get_name()) == name][0]
    R['before'] = {'TpD.A': pin('TpD', 'A'), 'TpD.B': pin('TpD', 'B'), 'LBack.B': pin('LBack', 'B')}
    R['set'] = [bool(c.set_pin_default_value('TpD.A', vec(PO['tp_hip_d']), True, False)), bool(c.set_pin_default_value('TpD.B', vec(PO['tp_sh_d']), True, False)), bool(c.set_pin_default_value('LBack.B', str(-PO['tp_lback']), True, False))]
    R['after'] = {'TpD.A': pin('TpD', 'A'), 'TpD.B': pin('TpD', 'B'), 'LBack.B': pin('LBack', 'B')}
    cr.recompile_vm(); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(cr, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_TP_STOCK', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
