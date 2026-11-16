"""Lyra 에디터(PIE 중지 후): 푸리나 폰 BP 기본값 AutoPossessPlayer 를 Disabled 로 (Lyra 게임 모드가 직접 possess 하도록). 레벨에 놓인 인스턴스는 자기 값을 가지므로 영향 없음.
usage: py lyra_pawn_autopossess.py [disabled|player0]  -> Data/lyra_pawn_autopossess.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_pawn_autopossess.json'
R = {}
try:
    mode = sys.argv[1] if len(sys.argv) > 1 else 'disabled'
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); cdo = unreal.get_default_object(bp.generated_class())
    R['before'] = str(cdo.get_editor_property('auto_possess_player'))
    cdo.set_editor_property('auto_possess_player', unreal.AutoReceiveInput.DISABLED if mode == 'disabled' else unreal.AutoReceiveInput.PLAYER0)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    R['after'] = str(unreal.get_default_object(bp.generated_class()).get_editor_property('auto_possess_player'))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PAWN_AUTOPOSSESS', R)
