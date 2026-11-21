"""실행 중 PIE(Cmd: py <파일>): 무기창 포커스/호버 상태 -> Data/lyra_wm_live_diag2.json"""
import unreal, json, traceback
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    ws = unreal.WidgetLibrary.get_all_widgets_of_class(w, unreal.load_asset('/Game/Furina/UI/WBP_FurinaWeaponMenu').generated_class(), False)
    for i, m in enumerate(ws):
        e = {'active': m.is_activated(), 'nation': m.get_editor_property('NationIndex'), 'kb_focus': m.has_keyboard_focus(), 'any_focus': m.has_any_user_focus(),
             'focused_desc': m.has_focused_descendants(), 'hover_self': m.is_hovered(), 'visible': str(m.get_visibility()), 'in_vp': m.is_in_viewport()}
        e['tabs_hover'] = [m.get_editor_property('Tab_%d' % k).is_hovered() for k in range(6)]
        e['tabrow_hover'] = m.get_editor_property('TabRow').is_hovered()
        R['w%d' % i] = e
except Exception: R['error'] = traceback.format_exc()[-800:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_wm_live_diag2.json', 'w'), indent=1, default=str)
