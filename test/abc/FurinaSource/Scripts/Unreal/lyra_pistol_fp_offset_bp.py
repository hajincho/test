"""Lyra 에디터(`py <파일> [dY]`, 새로 시작한 에디터에서 이 스크립트만 한 번): 1인칭일 때만 권총 프레임(FurinaPistolFrame, 슬라이드는 그 자식)을 손 쪽(소총 컴포넌트 -Y)으로 dY cm 당긴다.
 원인(lyra_pistol_grip_probe_g7/g9): FurinaRifle 은 오른손목 소켓에 붙어 손-총 관계가 고정이고, 권총 프레임 경계 Y -8.5~10.8 인데 오른손 손가락 끝은 Y -7~-13 -> 손잡이 뒤 3~5 cm 에서 떨어져 있었다.
 FurinaMagUpdate(0.016초 타이머)의 P2_Branch_01989945(권총 장착) then 쪽에:  FurinaPistolFrame.SetRelativeLocation( VLerp((0,-4.27,0.63), (0,-4.27-dY,0.63), IsActive(FurinaFPWanted)) )
 3인칭은 원래 위치 (0,-4.27,0.63) 그대로.   노드: FBP_*   -> Data/lyra_pistol_fp_offset_bp.json"""
import unreal, json, sys, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_pistol_fp_offset_bp.json'
nums = []
for a in sys.argv[1:]:
    try: nums.append(float(a))
    except ValueError: pass
DY = nums[0] if nums else 9.5
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'dY': DY}
def run():
    bp = unreal.load_asset(PAWN)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    K = '/Script/Engine.KismetMathLibrary:'
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
    def getv(name, var): n = ed.add_get_member_variable_node(var); n.rename(name); return n
    if 'FBP_SetLoc' in N: R['note'] = 'exists'
    else:
        va = fn('FBP_VecTP', K + 'MakeVector', X=0.0, Y=-4.27, Z=0.63); vb = fn('FBP_VecFP', K + 'MakeVector', X=0.0, Y=-4.27 - DY, Z=0.63)
        fpv = getv('FBP_FPGet', 'FurinaFPWanted'); act = fn('FBP_FPActive', '/Script/Engine.ActorComponent:IsActive'); link(pin(fpv, 'FurinaFPWanted', True), act.find_self_pin())
        tf = fn('FBP_ToF', K + 'Conv_BoolToDouble'); link(pin(act, 'ReturnValue', True), pin(tf, 'InBool'))
        vl = fn('FBP_VLerp', K + 'VLerp'); link(pin(va, 'ReturnValue', True), pin(vl, 'A')); link(pin(vb, 'ReturnValue', True), pin(vl, 'B')); link(pin(tf, 'ReturnValue', True), pin(vl, 'Alpha'))
        fr = getv('FBP_FrameGet', 'FurinaPistolFrame')
        sl = fn('FBP_SetLoc', '/Script/Engine.SceneComponent:K2_SetRelativeLocation', bSweep='false', bTeleport='true'); link(pin(fr, 'FurinaPistolFrame', True), sl.find_self_pin()); link(pin(vl, 'ReturnValue', True), pin(sl, 'NewLocation'))
        br = N['P2_Branch_01989945']; assert not list(br.find_then_pin().list_connected_pins()), 'then 이미 연결됨'
        link(br.find_then_pin(), sl.find_execute_pin())
        R['added'] = True
    del ed, N
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PISTOL_FP_OFFSET_BP', R.get('status'), R.get('error', ''))
import gc; gc.collect()
