"""Lyra 에디터(`py <파일> keep`): BP_FurinaBullet 의 Bullet 구, BP_223Case/BP_M4MagDrop 물리 메시의 채널별 충돌 응답 덤프 -> Data/lyra_bullet_resp_dump.json
(총알이 PhysicsBody 를 무시하는지, 탄피/탄창이 총알 채널(WorldDynamic)에 어떻게 응답하는지)"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_bullet_resp_dump.json'
R = {}
CH = ['ECC_WORLD_STATIC', 'ECC_WORLD_DYNAMIC', 'ECC_PAWN', 'ECC_VISIBILITY', 'ECC_CAMERA', 'ECC_PHYSICS_BODY', 'ECC_VEHICLE', 'ECC_DESTRUCTIBLE',
      'ECC_GAME_TRACE_CHANNEL1', 'ECC_GAME_TRACE_CHANNEL2', 'ECC_GAME_TRACE_CHANNEL3', 'ECC_GAME_TRACE_CHANNEL4', 'ECC_GAME_TRACE_CHANNEL5']
def resp(o):
    out = {}
    for ch in CH:
        try: out[ch] = str(o.get_collision_response_to_channel(getattr(unreal.CollisionChannel, ch))).split('.')[-1].split(':')[0]
        except Exception as e: out[ch] = 'ERR'
    return out
def find(bp, name):
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in S.k2_gather_subobject_data_for_blueprint(bp):
        d = L.get_data(h)
        if str(L.get_variable_name(d)) == name: return L.get_associated_object(d)
for bpn, comp in (('/Game/Furina/FP/BP_FurinaBullet', 'Bullet'), ('/Game/Furina/M4/BP_223Case', 'FXMesh'), ('/Game/Furina/M4/BP_M4MagDrop', 'MagBody')):
    try:
        o = find(unreal.load_asset(bpn), comp); R[bpn.split('/')[-1] + '.' + comp] = {'profile': str(o.get_collision_profile_name()), 'obj_type': str(o.get_collision_object_type()), 'responses': resp(o)}
    except Exception: R[bpn] = traceback.format_exc()[-200:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_BULLET_RESP', 'ok')
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
