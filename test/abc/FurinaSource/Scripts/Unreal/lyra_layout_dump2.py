"""Lyra 에디터(`py <파일>`): AddWidgets 의 레이아웃 요청 구조체 필드와 값을 덤프 -> Data/lyra_layout_dump2.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_layout_dump2.json'
R = {}
try:
    for p, isset in [('/Game/System/Experiences/B_LyraDefaultExperience', 0), ('/ShooterCore/Experiences/LAS_ShooterGame_StandardHUD', 1), ('/TopDownArena/System/Experiences/B_TopDownArenaExperience', 0)]:
        if isset: acts = unreal.load_asset(p).get_editor_property('actions')
        else:
            bp = unreal.load_asset(p + '.' + p.rsplit('/', 1)[1]); acts = unreal.get_default_object(bp.generated_class()).get_editor_property('actions')
        rows = []
        for a in acts:
            if a and 'AddWidgets' in a.get_class().get_name():
                for x in a.get_editor_property('layout'):
                    rows.append({'fields': [n for n in dir(x) if not n.startswith('_')][:20], 'str': str(x)[:300]})
                    for n in dir(x):
                        if not n.startswith('_') and not callable(getattr(x, n)):
                            try: rows[-1][n] = str(x.get_editor_property(n))
                            except Exception: pass
                rows.append({'widgets_n': len(a.get_editor_property('widgets'))})
        R[p] = rows
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LAYOUT_DUMP2')
