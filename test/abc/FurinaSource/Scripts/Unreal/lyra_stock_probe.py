"""Lyra PIE 중 실행(3인칭 상태에서): 개머리판 끝이 몸(Furina 메시 충돌/본)에 얼마나 들어가는지 측정 -> Data/lyra_stock_probe_<tag>.json
 py "<파일>" keep <tag>. 총 컴포넌트 찾기, 개머리판 끝(총 로컬 (0,-39.37,4.53)) 월드 좌표, 폰 로컬 좌표, 몸 충돌까지 거리(0이면 내부), 가까운 본까지 거리, 양손목 위치."""
import unreal, json, sys, traceback
TAG = sys.argv[-1] if sys.argv[-1] != 'keep' else 'run'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_stock_probe_%s.json' % TAG
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
    comps = p.get_components_by_class(unreal.PrimitiveComponent)
    R['comps'] = [[c.get_name(), c.get_class().get_name(), str(c.get_attach_parent().get_name()) if c.get_attach_parent() else None] for c in comps if isinstance(c, (unreal.SkeletalMeshComponent, unreal.StaticMeshComponent))][:30]
    body = [c for c in comps if isinstance(c, unreal.SkeletalMeshComponent) and 'Mesh' == c.get_name()]
    body = body[0] if body else [c for c in comps if isinstance(c, unreal.SkeletalMeshComponent)][0]
    gun = None
    for c in comps:
        if isinstance(c, unreal.SkeletalMeshComponent) and c is not body and c.skeletal_mesh_asset and 'M4' in c.skeletal_mesh_asset.get_name(): gun = c
    R['gun'] = gun.get_name() if gun else None
    inv = p.get_actor_transform().inverse()
    def loc(v): t = inv.transform_location(v); return [round(t.x, 1), round(t.y, 1), round(t.z, 1)]
    if gun:
        gt = gun.get_world_transform()
        for nm, lv in (('stock_butt', (0, -39.37, 4.53)), ('stock_mid', (0, -30.0, 3.0)), ('stock_top', (0, -39.37, 9.0)), ('stock_bottom', (0, -39.37, -2.0))):
            wv = gt.transform_location(unreal.Vector(*lv)); row = {'pawn_local': loc(wv)}
            try:
                res = body.get_closest_point_on_collision(wv); row['dist_raw'] = str(res)[:80]
                row['dist_to_body_collision'] = round(float(res[0] if isinstance(res, tuple) else res), 2)
                # 폰 로컬 x(앞) 0..10, y(오른쪽) 0..4 만큼 밀었을 때 몸 충돌까지 거리(0이면 내부)
                grid = {}
                pt = p.get_actor_transform()
                for dx in (0, 2, 4, 6, 8, 10):
                    for dy in (0, 2, 4):
                        q = pt.transform_location(unreal.Vector(row['pawn_local'][0] + dx, row['pawn_local'][1] + dy, row['pawn_local'][2]))
                        r2 = body.get_closest_point_on_collision(q); grid['fwd%d_right%d' % (dx, dy)] = round(float(r2[0] if isinstance(r2, tuple) else r2), 1)
                row['push_grid'] = grid
            except Exception as e: row['dist_err'] = str(e)[:80]
            R[nm] = row
    names = [str(body.get_bone_name(i)) for i in range(body.get_num_bones())]; R['n_bones'] = len(names)
    keys = ('spine', 'chest', 'neck', 'arm', 'wrist', 'shoulder', 'clav', 'hips', 'elbow', 'hand')
    pick = [n for n in names if any(k in n.lower() for k in keys) and 'HB' not in n and 'finger' not in n.lower()][:40]
    for n in pick: R['bone_' + n] = loc(body.get_socket_location(n))
    for b in ('Hips', 'Spine', 'Chest', 'Neck', 'Head', 'Right-shoulder', 'Right-arm', 'Left-shoulder', 'Left-arm', 'Right-wrist', 'Left-wrist'):
        try: R['F_' + b] = loc(body.get_socket_location(b))
        except Exception as e: R['F_' + b] = str(e)[:40]
    R['view_tp'] = None
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_STOCK', TAG, R.get('error', 'ok')[-200:])
