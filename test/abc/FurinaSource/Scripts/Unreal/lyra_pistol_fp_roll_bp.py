"""Lyra 에디터(`py <파일>`, 새로 시작한 에디터에서 이 스크립트만 한 번): 1인칭 권총 프레임(FurinaPistolFrame, 슬라이드는 자식)의 상대 위치/회전을 Blender 관통 최적화 결과로 바꾼다 (lyra_pistol_fp_offset_bp.py 의 노드 확장).
 값: Data/pistol_roll_constants.json  (loc_new, q_frame_new).  1인칭(FurinaFPWanted 활성) = 새 값, 3인칭 = (0,-4.27,0.63) / 회전(0,90,0) 그대로.
 변경: FBP_VecFP 값 갱신, FBP_RotTP/FBP_RotFP(MakeRotator) + FBP_RLerp + FBP_SetRot(K2_SetRelativeRotation) 추가, FBP_SetLoc 다음에 실행.   -> Data/lyra_pistol_fp_roll_bp.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
K = json.load(open(D + r'\pistol_roll_constants.json'))
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'const': K}
def run():
    bp = unreal.load_asset(PAWN)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    for need in ('FBP_VecFP', 'FBP_SetLoc', 'FBP_ToF', 'FBP_FrameGet'): assert need in N, 'missing ' + need
    Kc = '/Script/Engine.KismetMathLibrary:'
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name); return p
    def link(a, b):
        assert a is not None and b is not None and a.is_valid() and b.is_valid(), ('link', a, b)
        assert CONN(a, b), ('link', a.get_owning_node().get_name(), a.get_pin_name(), '->', b.get_owning_node().get_name(), b.get_pin_name())
    def fn(name, path, **vals):
        n = ed.add_call_function_node(path); assert n, path; n.rename(name)
        for k, v in vals.items(): pin(n, k).set_pin_value(str(v))
        return n
    x, y, z = K['loc_new']
    for k, v in (('X', x), ('Y', y), ('Z', z)): pin(N['FBP_VecFP'], k).set_pin_value('%.5f' % v)
    qn = K['q_frame_new']; rot = unreal.Quat(qn[0], qn[1], qn[2], qn[3]).rotator(); R['rot_fp'] = [rot.pitch, rot.yaw, rot.roll]
    if 'FBP_SetRot' in N: R['note'] = 'exists (only values updated)'
    else:
        rt = fn('FBP_RotTP', Kc + 'MakeRotator', Roll=0.0, Pitch=0.0, Yaw=90.0)
        rf = fn('FBP_RotFP', Kc + 'MakeRotator', Roll='%.5f' % rot.roll, Pitch='%.5f' % rot.pitch, Yaw='%.5f' % rot.yaw)
        rl = fn('FBP_RLerp', Kc + 'RLerp', bShortestPath='true'); link(pin(rt, 'ReturnValue', True), pin(rl, 'A')); link(pin(rf, 'ReturnValue', True), pin(rl, 'B')); link(pin(N['FBP_ToF'], 'ReturnValue', True), pin(rl, 'Alpha'))
        sr = fn('FBP_SetRot', '/Script/Engine.SceneComponent:K2_SetRelativeRotation', bSweep='false', bTeleport='true')
        link(pin(N['FBP_FrameGet'], 'FurinaPistolFrame', True), sr.find_self_pin()); link(pin(rl, 'ReturnValue', True), pin(sr, 'NewRotation'))
        link(N['FBP_SetLoc'].find_then_pin(), sr.find_execute_pin())
        R['added'] = True
    del ed, N
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(D + r'\lyra_pistol_fp_roll_bp.json', 'w'), indent=1, default=str); print('LYRA_PISTOL_FP_ROLL_BP', R.get('status'), R.get('error', ''))
import gc; gc.collect()
