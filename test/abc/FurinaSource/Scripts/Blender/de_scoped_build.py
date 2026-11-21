"""blender -b --python de_scoped_build.py -- <preview|export> : 소총 + 조준경 합본 (실제 장착 위치·마감 참고)
 좌표(정리본 재가져오기, cm): 총구 -Y, 위 +Z, 총의 오른쪽 -X.  Kar98k 총열 축 (x 0.65, z 7.1), G43 총열 축 (x 0, z 5.67).
 - Kar98k + ZF39 (저포탑 마운트): 앞 받침 = 앞 리시버 링(y 3.4), 뒤 받침 = 뒤 브리지(y 15.5), 조준경은 총열 중심선 위(축 = 총열 위 4.8), 접안부 끝 y 22.
   원본에 마운트가 없어 링+기둥을 만든다.
 - Kar98k + ZF41: 마운트가 가늠자 받침(y -13~-3.5) '왼쪽'에 물리고 팔이 수평으로 뻗어 조준경을 총열 위 중앙에 둔다(American Rifleman).
   원본 방향 그대로(대물 쪽 큰 통 = 앞, 고정 팔 = 총의 왼쪽 +X). 뒤 다리가 가늠자 받침 돌출부(y -6, x 2.09)와 0.2 cm 겹쳐 0.25 cm 왼쪽으로(접촉만).
 - G43 + ZF4: 리시버 '오른쪽' 도브테일 레일에 마운트, 조준경은 총열 중심선 위. 원본 마운트(아래로 늘어진 다리)는 장전 손잡이 이동 경로와
   겹쳐 지우고, 오른쪽 레일판 + 다리 + 링을 만든다. 접안부 끝 y 26.
 - 재질: 조준경 텍스처는 따로 구한 것이라 색감이 달라 단색 PBR(블루잉 강철)로 바꾸고, 색/거칠기는 각 소총 금속 부위 실측값(Data/de_metal_color.json)에 맞춤.
   마운트: ZF39 저포탑 = 블루잉, ZF4 = 인산염(회색, 덜 반짝임).
 -> _export/SM_DE_<키>.fbx, Data/de_prev_<키>_*.png, Data/de_scoped_build.json, Data/de_scoped_texmap.json(가져오기 스크립트가 합침)"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Matrix
A = sys.argv[sys.argv.index('--') + 1:]; STAGE = A[0]
EXP = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany\_export'; D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
# 단색 재질 [R, G, B(선형), 금속, 거칠기]: 소총 금속 실측(kar98k 중앙값 ~0.08 회색/거칠기 0.36, g43 ~0.05 약간 따뜻/0.30)
# 2차 조정(2026-11-21, 수집가 사진·설명): 조준경 관은 블루잉이 검게 보여 총 금속보다 약간 어둡게(광택은 비슷), ZF4 BLM 주조 마운트는 조준경보다 밝은 무광 회색(원본 마운트 텍스처 평균 0.18 과도 일치)
K98_BLUE = [0.078, 0.079, 0.075, 0.9, 0.36]; G43_BLUE = [0.050, 0.046, 0.043, 0.9, 0.32]
ZF39_BLUE = [0.048, 0.048, 0.052, 0.9, 0.32]; ZF41_BLUE = [0.044, 0.044, 0.048, 0.85, 0.42]; ZF4_BLUE = [0.032, 0.032, 0.035, 0.85, 0.40]
PHOSPHATE = [0.170, 0.168, 0.160, 0.55, 0.62]; GLASS = [0.018, 0.024, 0.034, 0.0, 0.04]   # 렌즈: 어두운 푸른 유리, 매끈
SPEC = {
 'kar98k_zf39': {'rifle': 'kar98k', 'scope': 'zf39', 'axis_local': (0.0, -0.275), 'axis': (0.65, 7.1 + 4.8), 'scope_y': 8.0, 'plain': ('ZF39_Blued', ZF39_BLUE),
                 'rings': [(3.4, -0.275, 8.65), (15.5, -0.275, 8.4)], 'ring_style': 'pillar', 'mount_mat': ('Mount_K98_Blued', K98_BLUE)},
 'kar98k_zf41': {'rifle': 'kar98k', 'scope': 'zf41', 'axis_local': (-0.57, 0.95), 'axis': (0.65 + 0.25, 7.1 + 3.64), 'scope_y': -8.25, 'plain': ('ZF41_Blued', ZF41_BLUE)},
 'g43_zf4': {'rifle': 'g43', 'scope': 'zf4', 'axis_local': (0.0, 0.955), 'axis': (0.0, 5.67 + 5.83), 'scope_y': 12.5, 'plain': ('ZF4_Blued', ZF4_BLUE),
             'drop_mat': 'ZF4_MountMaterial', 'rings': [(-4.9, None, None), (4.2, None, None)], 'ring_style': 'right_rail', 'mount_mat': ('Mount_ZF4_Phosphate', PHOSPHATE)},
}
def imp(path):
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=path)
    obs = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before and bpy.data.objects[k].type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(obs) > 1: bpy.ops.object.join()
    return bpy.context.view_layer.objects.active
def box(bm, x0, x1, y0, y1, z0, z1):
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))
def ring(bm, y, xa, za, r_in, r_out, L=1.4, seg=32):
    for i in range(seg):
        a0 = 2 * math.pi * i / seg; a1 = 2 * math.pi * (i + 1) / seg; vs = []
        for (a, r) in ((a0, r_in), (a0, r_out), (a1, r_out), (a1, r_in)):
            for yy in (y - L / 2, y + L / 2): vs.append(bm.verts.new((xa + r * math.cos(a), yy, za + r * math.sin(a))))
        for f in ((0, 2, 4, 6), (1, 7, 5, 3), (2, 3, 5, 4), (0, 6, 7, 1)):
            try: bm.faces.new([vs[k] for k in f])
            except ValueError: pass
def finish(bm, name, mat):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob
def plain_mat(name, v):
    m = bpy.data.materials.new(name); m.diffuse_color = (v[0] ** (1 / 2.2), v[1] ** (1 / 2.2), v[2] ** (1 / 2.2), 1); return m
OUT = {}; TMX = {}; LENS = {}
for key, sp in SPEC.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rif = imp(EXP + '\\SM_DE_%s.fbx' % sp['rifle']); sco = imp(EXP + '\\SM_DE_%s.fbx' % sp['scope'])
    for ob in (rif, sco): ob.data.transform(Matrix.Scale(100, 4)); ob.matrix_world = Matrix.Identity(4)   # cm 로 작업
    rif_mats = [m.name for m in rif.data.materials]
    if sp.get('drop_mat'):   # 원본 마운트 면 삭제
        bm = bmesh.new(); bm.from_mesh(sco.data); idx = [i for i, m in enumerate(sco.data.materials) if m and m.name.startswith(sp['drop_mat'])]
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in idx], context='FACES'); bm.to_mesh(sco.data); bm.free()
    pm = plain_mat(*sp['plain']); gm = plain_mat(sp['plain'][0].split('_')[0] + '_Glass', GLASS); sco.data.materials.clear(); sco.data.materials.append(pm); sco.data.materials.append(gm)
    lx0, lz0 = sp['axis_local']; ys = [v.co.y for v in sco.data.vertices]; y0, y1 = min(ys), max(ys); nl = 0
    for p in sco.data.polygons:
        c = p.center; n = p.normal; r = math.hypot(c.x - lx0, c.z - lz0)
        lens = abs(n.y) > 0.9 and r < 0.75 and (c.y - y0 < 3.0 or y1 - c.y < 3.0)
        p.material_index = 1 if lens else 0; nl += lens
    if nl == 0:   # 렌즈 형상이 없는 빈 관(ZF39, ZF4): 양 끝에서 0.8cm 안쪽에 내경에 맞춘 유리 원판(앞뒤 양면)
        V = np.array([v.co[:] for v in sco.data.vertices]); bmd = bmesh.new(); LENS[key + '_disc_r'] = []
        for yc, sg in ((y0 + 0.8, 1), (y1 - 0.8, -1)):
            sel = V[np.abs(V[:, 1] - yc) < 0.5]; rr = np.hypot(sel[:, 0] - lx0, sel[:, 2] - lz0); rr = rr[rr > 0.3]; ri = float(rr.min()) - 0.02 if len(rr) else 0.9
            LENS[key + '_disc_r'].append(round(ri, 3))
            for flip in (False, True):
                vs = [bmd.verts.new((lx0 + ri * math.cos(2 * math.pi * k / 40), yc, lz0 + ri * math.sin(2 * math.pi * k / 40))) for k in range(40)]
                bmd.faces.new(vs[::-1] if flip else vs)
        me = bpy.data.meshes.new('Lens'); bmd.to_mesh(me); bmd.free(); me.materials.append(pm); me.materials.append(gm)   # 합칠 때 슬롯이 맞게
        for poly in me.polygons: poly.material_index = 1
        tmp = bpy.data.objects.new('Lens', me); bpy.context.scene.collection.objects.link(tmp)
        bpy.ops.object.select_all(action='DESELECT'); tmp.select_set(True); sco.select_set(True); bpy.context.view_layer.objects.active = sco; bpy.ops.object.join()
        nl = -2
    LENS[key] = nl
    lx, lz = sp['axis_local']; ax, az = sp['axis']; dx, dz = ax - lx, az - lz
    S0 = np.array([v.co[:] for v in sco.data.vertices])   # 원본(로컬) 좌표: 링 반지름 측정용
    sco.data.transform(Matrix.Translation((dx, sp['scope_y'], dz)))
    parts = [rif, sco]; R = np.array([v.co[:] for v in rif.data.vertices]); mount = {}
    if 'rings' in sp:
        mm = plain_mat(*sp['mount_mat']); bm = bmesh.new()
        for (ry, _, zfloor) in sp['rings']:
            yl = ry if sp['ring_style'] == 'right_rail' else ry - sp['scope_y']   # 조준경 로컬 y
            sel = S0[np.abs(S0[:, 1] - yl) < 0.5]; r_tube = float(np.sqrt((sel[:, 0] - lx) ** 2 + (sel[:, 2] - lz) ** 2).max()) if len(sel) else 1.25
            yw = yl + sp['scope_y']; r_in, r_out = r_tube + 0.02, r_tube + 0.32; ring(bm, yw, ax, az, r_in, r_out)
            if sp['ring_style'] == 'pillar':   # 링 아래 ~ 리시버 윗면 기둥
                box(bm, ax - 0.8, ax + 0.8, yw - 0.7, yw + 0.7, zfloor, az - r_out + 0.3)
            mount.setdefault('rings', []).append({'y': round(yw, 2), 'r_tube': round(r_tube, 3)})
        if sp['ring_style'] == 'right_rail':   # 오른쪽(-X) 도브테일 레일판 + 각 링에서 내려오는 다리
            ys = [m_['y'] for m_ in mount['rings']]; y0, y1 = min(ys) - 1.2, max(ys) + 1.2
            side = R[(R[:, 1] > y0) & (R[:, 1] < y1) & (R[:, 2] > 6.3) & (R[:, 2] < 8.3)]; xr = float(side[:, 0].min())   # 리시버 오른쪽 면
            top = float(R[(R[:, 1] > y0) & (R[:, 1] < y1) & (np.abs(R[:, 0] - ax) < 1.0), 2].max())   # 리시버(+장전손잡이) 윗면
            box(bm, xr - 0.55, xr, y0, y1, 6.4, 8.2)   # 레일판(리시버 오른쪽 면에 붙음)
            for m_ in mount['rings']:
                ro = m_['r_tube'] + 0.32
                box(bm, xr - 0.55, xr - 0.05, m_['y'] - 0.7, m_['y'] + 0.7, 8.2, az - ro + 0.4)   # 세로 다리
                box(bm, xr - 0.55, ax - 0.2, m_['y'] - 0.7, m_['y'] + 0.7, az - ro - 0.35, az - ro + 0.4)   # 링 아래 가로 팔(오른쪽 -> 중심)
            mount.update({'rail_x': round(xr, 2), 'receiver_top': round(top, 2), 'ring_bottom_clear': round(az - max(m_['r_tube'] for m_ in mount['rings']) - 0.32 - 0.35 - top, 2)})
        parts.append(finish(bm, 'Mount', mm))
    # 간섭 점검: 조준경 관 아래와 소총 윗면(총열 중심선 ±1.5) 최소 간격
    S = np.array([v.co[:] for v in sco.data.vertices]); gaps = []
    for y in np.arange(S[:, 1].min(), S[:, 1].max(), 0.5):
        rs = R[(np.abs(R[:, 1] - y) < 0.25) & (np.abs(R[:, 0] - ax) < 1.5)]; ss = S[(np.abs(S[:, 1] - y) < 0.25) & (np.abs(S[:, 0] - ax) < 1.5)]
        if len(rs) and len(ss): gaps.append([round(float(y), 1), round(float(ss[:, 2].min() - rs[:, 2].max()), 2)])
    OUT[key] = {'scope_y_range': [round(float(S[:, 1].min()), 2), round(float(S[:, 1].max()), 2)], 'min_gap': min(gaps, key=lambda g: g[1]) if gaps else None, 'mount': mount,
                'scope_x_range': [round(float(S[:, 0].min()), 2), round(float(S[:, 0].max()), 2)]}
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = rif; bpy.ops.object.join(); ob = bpy.context.view_layer.objects.active; ob.name = 'SM_DE_' + key
    ob.data.transform(Matrix.Scale(0.01, 4))   # 다시 m
    # 합본 texmap: 소총 재질은 원본 항목 재사용, 조준경/마운트는 단색
    TMX[key] = {'@rifle': sp['rifle'], sp['plain'][0]: {'plain': sp['plain'][1]}, sp['plain'][0].split('_')[0] + '_Glass': {'plain': GLASS}}; OUT[key]['lens_faces'] = LENS[key]; OUT[key]['lens_disc_r'] = LENS.get(key + '_disc_r')
    if 'mount_mat' in sp: TMX[key][sp['mount_mat'][0]] = {'plain': sp['mount_mat'][1]}
    OUT[key]['mats'] = [m.name for m in ob.data.materials]; OUT[key]['tris'] = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    if STAGE == 'export':
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
        bpy.ops.export_scene.fbx(filepath=EXP + '\\SM_DE_%s.fbx' % key, use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True, mesh_smooth_type='FACE', path_mode='STRIP', add_leaf_bones=False, bake_anim=False)
        OUT[key]['fbx'] = True
    else:   # 미리보기: 소총 회색, 조준경 파랑, 마운트 빨강
        sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_cavity = True
        for m in bpy.data.materials: m.diffuse_color = (0.9, 0.9, 0.2, 1) if m.name.endswith('Glass') else (0.2, 0.35, 0.8, 1) if m.name.startswith('ZF') else (0.85, 0.2, 0.2, 1) if m.name.startswith('Mount') else (0.55, 0.55, 0.58, 1)
        cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
        yc = (OUT[key]['scope_y_range'][0] + OUT[key]['scope_y_range'][1]) / 200 + 0.03
        for nm, loc, rot in (('side', (1.0, yc, az / 100 - 0.02), (90, 0, 90)), ('top', (0, yc, 1.0), (0, 0, 90)), ('front', (0, -1.0, az / 100 - 0.02), (90, 0, 0)), ('rear', (0, 1.0, az / 100 - 0.02), (90, 0, 180))):
            sc.render.resolution_x, sc.render.resolution_y = (1100, 500) if nm in ('side', 'top') else (500, 500)
            cd.ortho_scale = 0.46 if nm in ('side', 'top') else 0.16
            cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
            sc.render.filepath = D + r'\de_prev_%s_%s.png' % (key, nm); bpy.ops.render.render(write_still=True)
    print('SCOPED', key, OUT[key])
json.dump(OUT, open(D + r'\de_scoped_build.json', 'w'), indent=1); json.dump(TMX, open(D + r'\de_scoped_texmap.json', 'w'), indent=1); print('SCOPED_DONE')
