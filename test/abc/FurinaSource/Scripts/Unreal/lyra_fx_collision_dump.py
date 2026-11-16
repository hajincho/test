"""Lyra 에디터(`py <파일> keep`): 사격 때 총구 근처에 생기는 액터(BP_M4Flash, BP_223Case, BP_M4MagDrop, BP_RicoSpark, BP_FurinaBullet) 컴포넌트별 충돌 설정과
푸리나 폰의 소총/탄창 컴포넌트 충돌 설정 덤프 -> Data/lyra_fx_collision_dump.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fx_collision_dump.json'
R = {}
def dump(bp):
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary; out = {}
    for h in S.k2_gather_subobject_data_for_blueprint(bp):
        d = L.get_data(h); name = str(L.get_variable_name(d)); o = L.get_associated_object(d)
        row = {'class': o.get_class().get_name() if o else None}
        if isinstance(o, unreal.PrimitiveComponent):
            try: row['profile'] = str(o.get_collision_profile_name()); row['enabled'] = str(o.get_collision_enabled()); row['obj_type'] = str(o.get_collision_object_type())
            except Exception as e: row['err'] = str(e)[:60]
            try: row['simulate'] = o.get_editor_property('body_instance').get_editor_property('simulate_physics')
            except Exception: pass
        out[name] = row
    return out
try:
    for p in ('/Game/Furina/M4/BP_M4Flash', '/Game/Furina/M4/BP_223Case', '/Game/Furina/M4/BP_M4MagDrop', '/Game/Furina/M4/BP_RicoSpark', '/Game/Furina/FP/BP_FurinaBullet'):
        try: R[p.split('/')[-1]] = dump(unreal.load_asset(p))
        except Exception as e: R[p.split('/')[-1]] = 'ERR ' + str(e)[:100]
    pawn = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    full = dump(pawn); R['pawn_relevant'] = {k: v for k, v in full.items() if any(s in k for s in ('Rifle', 'Mag', 'Furina', 'Capsule', 'Cylinder', 'Mesh'))}
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FX_COLLISION', R.get('error', 'ok')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
