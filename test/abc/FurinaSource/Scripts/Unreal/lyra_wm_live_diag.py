"""실행 중인 PIE 에서(Cmd: py <파일>): 무기창 TabRow 의 캐시 지오메트리(절대 위치/크기), NationIndex, 위젯 활성 -> Data/lyra_wm_live_diag.json"""
import unreal, json, traceback
R = {}
SL = getattr(unreal, 'SlateLibrary', None) or getattr(unreal, 'SlateBlueprintLibrary', None)
R['sl'] = str(SL)
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    ws = unreal.WidgetLibrary.get_all_widgets_of_class(w, unreal.load_asset('/Game/Furina/UI/WBP_FurinaWeaponMenu').generated_class(), False) if hasattr(unreal, 'WidgetLibrary') else []
    R['n'] = len(ws)
    for i, m in enumerate(ws):
        e = {'active': m.is_activated(), 'nation': m.get_editor_property('NationIndex')}
        tr = m.get_editor_property('TabRow'); g = tr.get_cached_geometry()
        e['size'] = str(SL.get_local_size(g)); e['abs0'] = str(SL.local_to_absolute(g, unreal.Vector2D(0, 0)))
        e['abs_size'] = str(SL.get_absolute_size(g))
        R['w%d' % i] = e
except Exception: R['error'] = traceback.format_exc()[-800:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_wm_live_diag.json', 'w'), indent=1, default=str); print('WM_LIVE_DIAG', R)
