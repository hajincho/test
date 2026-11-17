"""Lyra PIE(Play 전에 무장): 입력 없이 자동 점검. 폰이 생기고 12초 뒤에 (1) lyra_stock_probe.py(태그 인자) 실행, 2초 뒤 (2) lyra_idle_view.py(좌/우/뒤 옆모습 HighResShot 3) 실행.
PIE 중에 Cmd 창을 클릭하면 마우스 이동으로 카메라가 돌아가 버려서 측정이 틀어지므로, Play 전에 이 스크립트만 무장해 두고 손대지 않는다.
사용: py "<파일>" keep <태그>  -> Data/lyra_stock_probe_<태그>.json, Saved/Screenshots/WindowsEditor/HighresScreenshot*.png 3장"""
import unreal, sys, time, traceback
TAG = sys.argv[-1] if sys.argv[-1] != 'keep' else 'auto'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Scripts\Unreal'
S = {'st': 0, 't': 0}
def run(fn, argv):
    old = sys.argv; sys.argv = argv
    try: exec(compile(open(D + '\\' + fn, encoding='utf-8').read(), fn, 'exec'), {'__name__': '__main__'})
    finally: sys.argv = old
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None or unreal.GameplayStatics.get_player_pawn(w, 0) is None: return
        now = time.time()
        if S['st'] == 0: S['st'] = 1; S['t'] = now + 12
        elif S['st'] == 1 and now >= S['t']: run('lyra_stock_probe.py', ['x', 'keep', TAG]); S['st'] = 2; S['t'] = now + 2
        elif S['st'] == 2 and now >= S['t']: run('lyra_idle_view.py', ['x', 'keep']); S['st'] = 3; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        open(D.replace('Scripts\\Unreal', 'Data') + '\\lyra_auto_check_err.txt', 'w').write(traceback.format_exc()); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); print('LYRA_AUTO_CHECK armed', TAG)
