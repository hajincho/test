"""Lyra 에디터(`py <파일>`): FurinaMesh 의 스켈레탈 메시 에셋 -> 후처리 애님 BP, 물리 에셋(Thumb 바디 유무), 소켓 중 Thumb3 확인.  -> Data/lyra_mesh_postprocess_probe.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
R = {}
try:
    bp = unreal.load_asset(PAWN)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    hs = {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    c = lib.get_associated_object(lib.get_data(hs['FurinaMesh']))
    sk = c.get_editor_property('skeletal_mesh_asset'); R['mesh'] = str(sk.get_path_name()) if sk else None
    R['anim_class'] = str(c.get_editor_property('anim_class')); R['anim_mode'] = str(c.get_editor_property('animation_mode'))
    for pn in ('post_process_anim_blueprint', 'physics_asset', 'shadow_physics_asset'):
        try: v = sk.get_editor_property(pn); R[pn] = str(v.get_path_name()) if v else None
        except Exception as e: R[pn] = 'err ' + str(e)[:80]
    try: R['comp_physics_asset'] = str(c.get_editor_property('physics_asset_override'))
    except Exception as e: R['comp_physics_asset'] = 'err ' + str(e)[:60]
    try: R['sockets'] = [str(s.get_editor_property('socket_name')) + '@' + str(s.get_editor_property('bone_name')) for s in sk.get_editor_property('sockets') if 'Thumb' in str(s.get_editor_property('socket_name')) or 'Thumb' in str(s.get_editor_property('bone_name'))]
    except Exception as e: R['sockets'] = 'err ' + str(e)[:80]
    pa = sk.get_editor_property('physics_asset')
    if pa:
        try: R['pa_bodies_thumb'] = [str(b.get_editor_property('bone_name')) for b in pa.get_editor_property('skeletal_body_setups') if 'Thumb' in str(b.get_editor_property('bone_name'))]
        except Exception as e: R['pa_bodies_thumb'] = 'err ' + str(e)[:80]
        try: R['pa_n'] = len(pa.get_editor_property('skeletal_body_setups'))
        except Exception: pass
except Exception: R['error'] = traceback.format_exc()[-700:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_mesh_postprocess_probe.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_MESH_PP', R)
