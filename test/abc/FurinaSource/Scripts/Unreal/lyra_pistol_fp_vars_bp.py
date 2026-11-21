"""Lyra 에디터(`py <파일> [LX LY LZ RP RY RR]`, 새로 시작한 에디터에서 이 스크립트만 한 번): 1인칭 권총 프레임의 위치/회전 상수를 BP 변수로 바꿔 런타임에 조절 가능하게 한다.
 변수(실수): FurinaPFLocX/Y/Z, FurinaPFRotP/Y/R  (기본값 = 인자, 없으면 현재 상수)
 FBP_VLerp.B <- MakeVector(FBP_VecVar) <- 변수 3개,  FBP_RLerp.B <- MakeRotator(FBP_RotVar) <- 변수 3개.   -> Data/lyra_pistol_fp_vars_bp.json"""
import unreal, json, sys, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
nums = []
for a in sys.argv[1:]:
    try: nums.append(float(a))
    except ValueError: pass
DEF = nums if len(nums) == 6 else [3.34537, -20.02663, 0.5891, -2.59778, 91.50103, -30.03404]
NAMES = ['FurinaPFLocX', 'FurinaPFLocY', 'FurinaPFLocZ', 'FurinaPFRotP', 'FurinaPFRotY', 'FurinaPFRotR']
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'defaults': DEF}
def run():
    bp = unreal.load_asset(PAWN)
    existing = [str(x) for x in BEL.list_member_variable_names(bp)]
    ty = None
    for tn in ('real', 'float', 'double'):
        try:
            ty = BEL.get_basic_type_by_name(tn); R['type'] = tn; break
        except Exception as e: R.setdefault('type_err', []).append(tn)
    assert ty is not None
    for n in NAMES:
        if n not in existing: R.setdefault('added_vars', []).append([n, bool(BEL.add_member_variable(bp, n, ty))])
    BEL.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    for need in ('FBP_VLerp', 'FBP_RLerp'): assert need in N, 'missing ' + need
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
    def getv(name, var): n = ed.add_get_member_variable_node(var); n.rename(name); return n
    if 'FBP_VecVar' in N: R['note'] = 'exists'
    else:
        g = [getv('FBPV_Get%d' % i, NAMES[i]) for i in range(6)]
        mv = fn('FBP_VecVar', Kc + 'MakeVector'); mr = fn('FBP_RotVar', Kc + 'MakeRotator')
        for i, k in enumerate(('X', 'Y', 'Z')): link(pin(g[i], NAMES[i], True), pin(mv, k))
        for i, k in zip((3, 4, 5), ('Pitch', 'Yaw', 'Roll')): link(pin(g[i], NAMES[i], True), pin(mr, k))
        vb = pin(N['FBP_VLerp'], 'B'); vb.break_pin_links(); link(pin(mv, 'ReturnValue', True), vb)
        rb = pin(N['FBP_RLerp'], 'B'); rb.break_pin_links(); link(pin(mr, 'ReturnValue', True), rb)
        R['added'] = True
    del ed, N
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    cdo = unreal.get_default_object(bp.generated_class())
    for n, v in zip(NAMES, DEF):
        try: cdo.set_editor_property(n, float(v))
        except Exception as e: R.setdefault('cdo_err', []).append([n, str(e)[:80]])
    R['cdo'] = {n: cdo.get_editor_property(n) for n in NAMES}
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(D + r'\lyra_pistol_fp_vars_bp.json', 'w'), indent=1, default=str); print('LYRA_PISTOL_FP_VARS_BP', R.get('status'), R.get('error', ''))
import gc; gc.collect()
