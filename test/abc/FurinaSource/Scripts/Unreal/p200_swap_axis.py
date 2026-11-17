"""스왑 하강 축 수정: 소총 소켓 기준 Y 방향으로 -SWAP_DY 만큼 내리고, 회전은 사용 안 함 (PIE 캡처로 방향 확인)."""
import unreal, json, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
SWAP_DY = -26.0
R = {}
try:
    bx, by, bz, br, bpi, byw = -1.9545385462419, -10.6007758219875, -6.3540456497067, 178.2363577159168, -50.506775498163066, -0.4972744617336327
    Nn = N()
    mk = [v for k, v in Nn.items() if k.startswith('P2_MkVec_b425cf20')][0]
    interp = [v for k, v in Nn.items() if k.startswith('P2_SwapInterp')][0]
    a = interp.find_result_pin()
    ypin = mk.find_input_pin('Y'); ypin.break_pin_links(); link(addf(lit(by), mulf(a, lit(SWAP_DY))), ypin)
    zpin = mk.find_input_pin('Z'); zpin.break_pin_links(); link(lit(bz), zpin)
    rot = [v for k, v in Nn.items() if k.startswith('P2_MkRot_5568bf27')][0]
    pp = rot.find_input_pin('Pitch'); pp.break_pin_links(); link(lit(bpi), pp)
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['errors'] = [x.get_name()[:40] for x in ed.list_nodes_with_errors()][:10]
except Exception: R['error'] = traceback.format_exc()[-900:]
print('P200_SWAPAXIS', json.dumps(R, default=str, ensure_ascii=False))
