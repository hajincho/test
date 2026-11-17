"""Lyra PIE(Play 전에 무장): 폰이 생기고 8초 뒤 소총 상태에서 FurinaRifle/FurinaMag/FurinaPistolFrame/FurinaPistolSlide 의 가시성(컴포넌트/숨김)과 소총 기준 상대 변환 기록 -> Data/lyra_pistol_vis.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_pistol_vis.json'
S = {'st': 0, 't': 0}
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None or unreal.GameplayStatics.get_player_pawn(w, 0) is None: return
        now = time.time()
        if S['st'] == 0: S['st'] = 1; S['t'] = now + 8; return
        if S['st'] == 1 and now >= S['t']:
            p = unreal.GameplayStatics.get_player_pawn(w, 0); R = {}
            comps = {c.get_name(): c for c in p.get_components_by_class(unreal.SceneComponent)}
            rifle = comps['FurinaRifle']; R['pistol_on'] = str(p.get_editor_property('FurinaPistolOn').is_active()) if hasattr(p.get_editor_property('FurinaPistolOn'), 'is_active') else str(p.get_editor_property('FurinaPistolOn'))
            for n in ('FurinaRifle', 'FurinaMag', 'FurinaPistolFrame', 'FurinaPistolSlide'):
                c = comps.get(n)
                if c is None: R[n] = 'missing'; continue
                rel = unreal.MathLibrary.make_relative_transform(c.get_world_transform(), rifle.get_world_transform()); r = rel.rotation.rotator()
                row = {'visible': c.is_visible(), 'hidden_in_game': c.get_editor_property('hidden_in_game'), 'rel_loc': [round(rel.translation.x, 2), round(rel.translation.y, 2), round(rel.translation.z, 2)], 'rel_rot': [round(r.roll, 1), round(r.pitch, 1), round(r.yaw, 1)], 'parent': str(c.get_attach_parent().get_name()) if c.get_attach_parent() else None}
                try: row['mesh'] = c.get_editor_property('static_mesh').get_name() if hasattr(c, 'static_mesh') and c.get_editor_property('static_mesh') else None
                except Exception: pass
                try: o, e, rr = unreal.SystemLibrary.get_component_bounds(c); inv = rifle.get_world_transform().inverse(); ct = inv.transform_location(o); row['center_in_rifle'] = [round(ct.x, 1), round(ct.y, 1), round(ct.z, 1)]; row['extent'] = [round(e.x, 1), round(e.y, 1), round(e.z, 1)]
                except Exception: pass
                R[n] = row
            json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); S['st'] = 2; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        open(OUT, 'w').write(traceback.format_exc()); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); print('LYRA_PISTOL_VIS armed')
