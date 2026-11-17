"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 푸리나 폰 액터 틱 상태 확인 후 켠다.
ALyraCharacter 생성자는 PrimaryActorTick.bCanEverTick=false/bStartWithTickEnabled=false 라서, LyraCharacter 로 부모를 바꾼 뒤 BP 의 Event Tick 로직
(앉기 90/360 속도 제한, 조준·견착 속도 제한 등)이 멈춘다.   -> Data/lyra_fix_tick.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fix_tick.json'
R = {}
P = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
try:
    bp = unreal.load_asset(P); cdo = unreal.get_default_object(bp.generated_class())
    t = cdo.get_editor_property('primary_actor_tick'); R['before'] = t.export_text()
    t.import_text('(bStartWithTickEnabled=True,bCanEverTick=True)')
    cdo.set_editor_property('primary_actor_tick', t); R['after'] = cdo.get_editor_property('primary_actor_tick').export_text()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    cdo2 = unreal.get_default_object(bp.generated_class()); R['after_compile'] = cdo2.get_editor_property('primary_actor_tick').export_text()
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIX_TICK', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
