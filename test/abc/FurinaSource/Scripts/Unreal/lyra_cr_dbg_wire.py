"""Lyra 에디터(`py <파일> on|off`): 임시 진단 - CR 의 디버그 곡선 DbgL/DbgR/DbgW/DbgC 에 ThW / RlFpW / ReloadSm / PistW 를 연결해 PIE 에서 읽는다. off 면 원래(LD/RD/SlopeW/Run)로 복구.  -> Data/lyra_cr_dbg_wire.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_dbg_wire.json'
MODE = 'off' if 'off' in sys.argv else 'on'
ON = [('SetDbgL', 'ThW.Result'), ('SetDbgR', 'RlFpW.Result'), ('SetDbgW', 'ReloadSm.Result'), ('SetDbgC', 'PistW.Result')]
OFF = [('SetDbgL', 'LD.Result'), ('SetDbgR', 'RD.Result'), ('SetDbgW', 'SlopeW.Result'), ('SetDbgC', 'Run.Result')]
R = {'mode': MODE, 'links': []}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    N = {str(n.get_node_path()): n for n in g.get_nodes()}
    for node, src in (ON if MODE == 'on' else OFF):
        pin = node + '.Value'
        for p in N[node].get_pins():
            if str(p.get_name()) == 'Value':
                for s in list(p.get_linked_source_pins()):
                    try: c.break_link(str(s.get_pin_path()), pin)
                    except Exception as e: R['links'].append(['break', str(e)[:60]])
        R['links'].append([src, pin, bool(c.add_link(src, pin))])
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CR_DBG_WIRE', MODE, R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
