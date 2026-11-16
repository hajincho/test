"""Lyra 에디터(`py <파일> keep`, PIE 중지 후): 총알끼리 충돌해 총구에서 사라지는 버그 수정.
원인: 낮은 프레임에서 발사 타이머가 한 프레임에 여러 번 실행되어(bMaxOncePerFrame=false) 같은 총구 위치에 총알이 동시에 생기고, 총알(오브젝트 타입 WorldDynamic)이 WorldDynamic 을 Block 하므로
서로 막혀 첫 틱에 사라진다(슬로모션 시험: 프레임당 3발 그룹에서 3발 중 0~1발만 관측, 나머지는 생성 즉시 소멸).
수정: Bullet 구의 오브젝트 타입을 WorldDynamic -> PhysicsBody 로. 총알은 PhysicsBody 응답이 이미 Ignore 라서 총알끼리(그리고 탄피/버린 탄창과) 충돌하지 않고, 벽/액터/폰은 그대로 맞춘다. -> Data/lyra_bullet_objtype.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_bullet_objtype.json'
R = {}
try:
    bul = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet')
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary; sphere = None
    for h in S.k2_gather_subobject_data_for_blueprint(bul):
        d = L.get_data(h)
        if str(L.get_variable_name(d)) == 'Bullet': sphere = L.get_associated_object(d)
    R['before'] = [str(sphere.get_collision_object_type()), str(sphere.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PHYSICS_BODY)), str(sphere.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC))]
    sphere.set_collision_object_type(unreal.CollisionChannel.ECC_PHYSICS_BODY)
    R['after'] = [str(sphere.get_collision_object_type()), str(sphere.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PHYSICS_BODY)), str(sphere.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC))]
    unreal.BlueprintEditorLibrary.compile_blueprint(bul); R['status'] = str(bul.get_editor_property('status')); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bul, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_BULLET_OBJTYPE', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
