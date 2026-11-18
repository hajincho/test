"""Lyra 에디터(`py <파일>`): 경험/액션 세트의 AddWidgets 액션(레이아웃 요청, HUD 요소) 내용을 덤프 -> Data/lyra_layout_dump.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_layout_dump.json'
R = {}
def d_action(a):
    row = {'class': a.get_class().get_name()}
    if 'AddWidgets' in row['class']:
        try: row['layout'] = [{'layout': str(x.get_editor_property('layout_class')), 'layer': str(x.get_editor_property('layer_id'))} for x in a.get_editor_property('layout')]
        except Exception as e: row['layout_err'] = str(e)[:100]
        try: row['widgets'] = [{'slot': str(x.get_editor_property('slot_id')), 'w': str(x.get_editor_property('widget_class'))} for x in a.get_editor_property('widgets')]
        except Exception as e: row['widgets_err'] = str(e)[:100]
    return row
try:
    for p in ['/Game/System/Experiences/B_Furina_Experience', '/Game/System/Experiences/B_LyraDefaultExperience', '/ShooterCore/Experiences/B_ShooterGame_Elimination', '/TopDownArena/System/Experiences/B_TopDownArenaExperience']:
        bp = unreal.load_asset(p + '.' + p.rsplit('/', 1)[1]); cdo = unreal.get_default_object(bp.generated_class())
        R[p] = [d_action(a) for a in cdo.get_editor_property('actions') if a]
    for p in ['/ShooterCore/Experiences/LAS_ShooterGame_StandardHUD', '/ShooterCore/Experiences/LAS_ShooterGame_StandardComponents']:
        a = unreal.load_asset(p); R[p] = [d_action(x) for x in a.get_editor_property('actions') if x]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_LAYOUT_DUMP')
