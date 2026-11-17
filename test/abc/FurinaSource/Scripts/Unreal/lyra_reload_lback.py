"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 3인칭 재장전 중 왼손이 탄창에 닿도록, 재장전 동안 LBack(왼손을 총열 뒤로 당기는 3인칭 보정 9.6cm)을 서서히 0으로 줄인다.
원인(lyra_reload_mag_probe.py 측정): 3인칭에서는 왼팔 도달 거리 때문에 손목을 9.6cm 뒤로 당겨 두는데(LBack), 재장전 곡선(ReloadLX/Y/Z)은 그 위에 더해져서
손목이 탄창 중심에서 (8.9좌, -10.6앞뒤, -2.5상하) = 약 14cm 떨어진 곳에 도달했다(손바닥은 손목에서 약 7cm 앞). 1인칭은 TpW=0 이라 LBack 이 0이라 영향 없음.
새 노드: ReloadSm(재장전 가중 부드럽게), NotReloadL(1-값), LBackW(TpW x NotReloadL). LBack.A 연결을 TpW -> LBackW 로 바꾼다.  -> Data/lyra_reload_lback.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_reload_lback.json'
R = {}
SMOOTH = 8.0
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    nodes = {str(n.get_node_path()): n for n in g.get_nodes()}
    R['has'] = 'LBackW' in nodes
    if not R['has']:
        U = '/Script/ControlRig.RigUnit_'
        c.add_unit_node_from_struct_path(U + 'AccumulateFloatLerp', 'Execute', unreal.Vector2D(0, 0), 'ReloadSm')
        c.add_unit_node_from_struct_path(U + 'MathFloatRemap', 'Execute', unreal.Vector2D(0, 0), 'NotReloadL')
        c.add_unit_node_from_struct_path(U + 'MathFloatMul', 'Execute', unreal.Vector2D(0, 0), 'LBackW')
        R['links'] = [bool(c.add_link('ReloadW.Result', 'ReloadSm.TargetValue')), bool(c.add_link('ReloadSm.Result', 'NotReloadL.Value')),
                      bool(c.add_link('TpW.Result', 'LBackW.A')), bool(c.add_link('NotReloadL.Result', 'LBackW.B'))]
        R['broke'] = bool(c.break_link('TpW.Result', 'LBack.A')); R['relink'] = bool(c.add_link('LBackW.Result', 'LBack.A'))
        for pin, val in (('ReloadSm.Blend', str(SMOOTH)), ('ReloadSm.bIntegrateDeltaTime', 'True'), ('NotReloadL.SourceMinimum', '0'), ('NotReloadL.SourceMaximum', '1'),
                         ('NotReloadL.TargetMinimum', '1'), ('NotReloadL.TargetMaximum', '0'), ('NotReloadL.bClamp', 'True')):
            R.setdefault('set', {})[pin] = bool(c.set_pin_default_value(pin, val, True, False))
    else:
        R['set_blend'] = bool(c.set_pin_default_value('ReloadSm.Blend', str(SMOOTH), True, False))
    nodes = {str(n.get_node_path()): n for n in g.get_nodes()}
    lb = [p for p in nodes['LBack'].get_pins() if str(p.get_name()) == 'A'][0]
    R['LBack.A_linked_from'] = [str(t.get_pin_path()) for t in lb.get_linked_source_pins()] if hasattr(lb, 'get_linked_source_pins') else 'n/a'
    cr.recompile_vm(); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(cr, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_RELOAD_LBACK', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
