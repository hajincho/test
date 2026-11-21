"""헤드리스(에디터 세션당 한 번): 1인칭 전용 권총 팔(권총 프레임과 한몸)을 ThirdPersonCharacter_BP 에 연결. (lyra_fp_arms_bp.py + _fix.py 이후)
 1) 컴포넌트 FurinaFPPistArmL / R (StaticMesh SM_FurinaFPPistArmL/R, 부모 FurinaPistolFrame, 상대 변환 0), 충돌 없음, 처음엔 숨김.
 2) FPA 로직 확장:  PArmsOn = FPCamera 활성 AND 권총,  권총 팔 R 보이기 = PArmsOn,  L = PArmsOn AND (재장전 아님 AND 대기 끝)
    본체 'Right-arm' 숨김 = 1인칭(소총/권총 공통),  'Left-arm' 숨김 = 1인칭 AND (재장전 아님 AND 대기 끝)
 노드: FPP_*   -> Data/lyra_fp_arms_bp_pistol.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'log': []}
def run():
    bp = unreal.load_asset(PAWN)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    def comp(name): return lib.get_associated_object(lib.get_data(handles()[name]))
    for side in ('L', 'R'):
        nm = 'FurinaFPPistArm' + side
        if nm not in handles():
            h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()['FurinaPistolFrame'], new_class=unreal.StaticMeshComponent, blueprint_context=bp)); sub.rename_subobject(h, unreal.Text(nm)); R['log'].append('added ' + nm)
        c = comp(nm)
        c.set_editor_property('static_mesh', unreal.load_asset('/Game/Furina/FPArms/SM_FurinaFPPistArm' + side))
        c.set_editor_property('relative_location', unreal.Vector(0, 0, 0)); c.set_editor_property('relative_rotation', unreal.Rotator(0, 0, 0)); c.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1))
        c.set_editor_property('visible', False); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property('cast_shadow', True)
        c.set_editor_property('can_character_step_up_on', unreal.CanBeCharacterBase.ECB_NO)
        try: c.set_editor_property('generate_overlap_events', False)
        except Exception: pass
    BEL.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    K = '/Script/Engine.KismetMathLibrary:'; E = '/Script/Engine.'
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name); return p
    def link(a, b):
        assert CONN(a, b), ('link', a.get_owning_node().get_name(), a.get_pin_name(), '->', b.get_owning_node().get_name(), b.get_pin_name())
    def relink(src, dst):
        dst.break_pin_links(); link(src, dst)
    def fn(name, path, **vals):
        n = ed.add_call_function_node(path); assert n, path; n.rename(name)
        for k, v in vals.items(): pin(n, k).set_pin_value(str(v))
        return n
    def getv(name, var): n = ed.add_get_member_variable_node(var); n.rename(name); return n
    if 'FPP_ArmsOn' in N: R['note'] = 'exists'
    else:
        FP = pin(N['FPA_FpA'], 'ReturnValue', True); PO = pin(N['FPA_PoA'], 'ReturnValue', True); A1 = pin(N['FPA_LA1'], 'ReturnValue', True)
        pa = fn('FPP_ArmsOn', K + 'BooleanAND'); link(FP, pin(pa, 'A')); link(PO, pin(pa, 'B')); PA = pin(pa, 'ReturnValue', True)
        pl = fn('FPP_LeftOn', K + 'BooleanAND'); link(PA, pin(pl, 'A')); link(A1, pin(pl, 'B')); PL = pin(pl, 'ReturnValue', True)
        la = fn('FPP_LeftAny', K + 'BooleanAND'); link(FP, pin(la, 'A')); link(A1, pin(la, 'B')); LA = pin(la, 'ReturnValue', True)
        gr = getv('FPP_ArmRG', 'FurinaFPPistArmR'); vr = fn('FPP_VisR', E + 'SceneComponent:SetVisibility', bPropagateToChildren='false'); link(pin(gr, 'FurinaFPPistArmR', True), vr.find_self_pin()); link(PA, pin(vr, 'bNewVisibility'))
        gl = getv('FPP_ArmLG', 'FurinaFPPistArmL'); vl = fn('FPP_VisL', E + 'SceneComponent:SetVisibility', bPropagateToChildren='false'); link(pin(gl, 'FurinaFPPistArmL', True), vl.find_self_pin()); link(PL, pin(vl, 'bNewVisibility'))
        # 실행선: FPA_VisL -> FPP_VisR -> FPP_VisL -> (원래 다음 = FPA_HidR)
        v0 = N['FPA_VisL']; nxt = list(v0.find_then_pin().list_connected_pins()); R['old_next'] = [p.get_owning_node().get_name() for p in nxt]
        v0.find_then_pin().break_pin_links(); link(v0.find_then_pin(), vr.find_execute_pin()); link(vr.find_then_pin(), vl.find_execute_pin())
        for p in nxt: link(vl.find_then_pin(), p)
        # 본체 팔 숨김 조건: 오른팔 = 1인칭, 왼팔 = 1인칭 AND 대기 끝
        relink(FP, pin(N['FPA_DiffR'], 'B')); relink(FP, pin(N['FPA_BrWR'], 'Condition'))
        relink(LA, pin(N['FPA_DiffL'], 'B')); relink(LA, pin(N['FPA_BrWL'], 'Condition'))
        R['added'] = True
    del ed, N, sub, lib
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\lyra_fp_arms_bp_pistol.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_ARMS_BP_PISTOL', R.get('status'), R.get('error', ''))
import gc; gc.collect()
