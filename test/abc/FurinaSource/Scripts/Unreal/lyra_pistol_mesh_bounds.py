"""Lyra 에디터(`py <파일>`): 권총 프레임/슬라이드 정적 메시의 로컬 경계 상자와 정점 단면(손잡이 위치 추정용)을 FurinaRifle 컴포넌트 기준(상대 위치/회전 적용)으로 계산.
 BP 기본값(CDO 컴포넌트 템플릿)에서 읽는다.   -> Data/lyra_pistol_mesh_bounds.json"""
import unreal, json, traceback, math
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_pistol_mesh_bounds.json'
R = {}
def run():
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    cdo = unreal.get_default_object(bp.generated_class())
    comps = {c.get_name(): c for c in cdo.get_components_by_class(unreal.SceneComponent)}
    R['comp_names'] = [n for n in comps if 'Pistol' in n or n in ('FurinaRifle',)]
    for nm in ('FurinaPistolFrame', 'FurinaPistolSlide'):
        c = comps.get(nm)
        if c is None: R[nm] = None; continue
        m = c.static_mesh; bb = m.get_bounding_box(); rl = c.relative_location; rr = c.relative_rotation; rs = c.relative_scale3d
        row = {'mesh': m.get_path_name(), 'rel_loc': [rl.x, rl.y, rl.z], 'rel_rot': [rr.pitch, rr.yaw, rr.roll], 'rel_scale': [rs.x, rs.y, rs.z], 'bb_min': [bb.min.x, bb.min.y, bb.min.z], 'bb_max': [bb.max.x, bb.max.y, bb.max.z]}
        # 8 코너를 컴포넌트 변환(부모=FurinaRifle 컴포넌트 기준)으로 옮겨 최소/최대
        tf = unreal.Transform(location=rl, rotation=rr.quaternion(), scale=rs)
        pts = []
        for x in (bb.min.x, bb.max.x):
            for y in (bb.min.y, bb.max.y):
                for z in (bb.min.z, bb.max.z):
                    q = tf.transform_location(unreal.Vector(x, y, z)); pts.append([round(q.x, 2), round(q.y, 2), round(q.z, 2)])
        row['rifle_min'] = [min(p[i] for p in pts) for i in range(3)]; row['rifle_max'] = [max(p[i] for p in pts) for i in range(3)]
        R[nm] = row
    del comps, cdo, bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-800:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PISTOL_MESH_BOUNDS', R.get('error', 'ok'))
import gc; gc.collect()
