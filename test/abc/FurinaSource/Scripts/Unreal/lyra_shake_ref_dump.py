"""Lyra 에디터(`py <파일>`): 번들 Medium/Low 카메라 셰이크의 부모 클래스와 진동 값, 우리 CS_FurinaShot 패턴 값 덤프 -> Data/lyra_shake_ref_dump.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_shake_ref_dump.json'
R = {}
try:
    for k, p in (('medium', '/Game/3DPlatformerGameBundle/CameraShakes/Medium_Camera_Shake_BP'), ('low', '/Game/3DPlatformerGameBundle/CameraShakes/Low_Camera_Shake_BP'), ('mine', '/Game/Furina/CameraShakes/CS_FurinaShot')):
        bp = unreal.load_asset(p); gc = bp.generated_class(); cdo = unreal.get_default_object(gc); row = {'parent': str(gc.get_super_class() if hasattr(gc, 'get_super_class') else None), 'class': str(gc)}
        for n in dir(cdo):
            if n.startswith('_') or callable(getattr(cdo, n, None)): continue
            try: row[n] = str(cdo.get_editor_property(n))[:300]
            except Exception: pass
        try:
            pat = cdo.get_root_shake_pattern(); row['pattern'] = str(pat)
            if pat:
                for n in dir(pat):
                    if n.startswith('_') or callable(getattr(pat, n, None)): continue
                    try: row['pat_' + n] = str(pat.get_editor_property(n))[:200]
                    except Exception: pass
        except Exception as e: row['pat_err'] = str(e)[:60]
        R[k] = row
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('SHAKE_REF_DUMP')
