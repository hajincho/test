"""Lyra 에디터(`py <파일>`, PIE 중지 상태): lyra_fp_mag_base_grab6.py 후속 - '높이 누르기' 대신 '옆 이동 막기'.
측정(6차): 벽 침범은 거의 없어졌지만(2샘플 0.58cm) 뽑는 순간 높이 제한 때문에 탄창이 한 프레임에 10cm 아래로 순간이동했다.
수정: 높이는 원래 경로(부드럽게 거른 RgSm.z)를 그대로 따르고, 옆 이동(xy)을 '얼마나 내려왔는지'로 제한한다.
 내려온 거리 desc = P_G.z - z,  허용 반경 rlim = remap(desc, CLEAR..CLEAR+RAMP -> R0..30cm),  xy = P_G.xy + (xy - P_G.xy) x min(1, rlim / r).
 -> 탄창이 삽입구를 다 빠져나오기(CLEAR) 전에는 축에서 R0 이상 못 벗어나고, 빠져나온 뒤 RAMP 동안 옆으로 따라간다. 끼울 때는 반대로 축을 먼저 맞춘 뒤 올라간다.
노드: RcDesc/RcRlim/RcRs/RcSc0/RcSc/RcDxyS/RcXY/RcP2 (RcOut.B: RcP -> RcP2). -> Data/lyra_fp_mag_base_grab7.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_mag_base_grab7.json'
CLEAR = 9.0; RAMP = 8.0; R0 = 0.15
R = {'CLEAR': CLEAR, 'RAMP': RAMP, 'R0': R0}
U = '/Script/ControlRig.RigUnit_'
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    L = []
    def link(a, b):
        try: L.append(['+', a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append(['+', a, b, 'err ' + str(e)[:80]])
    def brk(a, b):
        try: L.append(['x', a, b, bool(c.break_link(a, b))])
        except Exception as e: L.append(['x', a, b, 'err ' + str(e)[:60]])
    if 'RcP2' not in nodes():
        mk('MathFloatSub', 'RcDesc'); mk('MathFloatRemap', 'RcRlim', TargetMaximum='30.0', bClamp='True')
        mk('MathFloatMax', 'RcRs', B='0.0001'); mk('MathFloatDiv', 'RcSc0'); mk('MathFloatMin', 'RcSc', B='1.0')
        mk('MathVectorScale', 'RcDxyS'); mk('MathVectorAdd', 'RcXY'); mk('MathVectorMake', 'RcP2')
        link('RcPg.Result.Z', 'RcDesc.A'); link('RgSm.Result.Z', 'RcDesc.B'); link('RcDesc.Result', 'RcRlim.Value')
        link('RcR.Result', 'RcRs.A'); link('RcRlim.Result', 'RcSc0.A'); link('RcRs.Result', 'RcSc0.B'); link('RcSc0.Result', 'RcSc.A')
        link('RcDxy.Result', 'RcDxyS.Value'); link('RcSc.Result', 'RcDxyS.Factor'); link('RcPg.Result', 'RcXY.A'); link('RcDxyS.Result', 'RcXY.B')
        link('RcXY.Result.X', 'RcP2.X'); link('RcXY.Result.Y', 'RcP2.Y'); link('RgSm.Result.Z', 'RcP2.Z')
        brk('RcP.Result', 'RcOut.B'); link('RcP2.Result', 'RcOut.B')
    R['links'] = L
    S = [c.set_pin_default_value('RcRlim.SourceMinimum', '%.3f' % CLEAR, True, False), c.set_pin_default_value('RcRlim.SourceMaximum', '%.3f' % (CLEAR + RAMP), True, False),
         c.set_pin_default_value('RcRlim.TargetMinimum', '%.3f' % R0, True, False)]
    R['set'] = [bool(x) for x in S]
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_MAG_BASE7', R.get('saved'), R.get('error', '')[-200:])
