"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): M4 머티리얼(총몸/개머리판·핸드가드/탄창/후방 조준기)의 금속성을 비슷하게 맞추고 더 어둡게 한다.
원래 Metallic 텍스처 값 t(0~1)를 Lerp(LO, HI, t) 로 다시 매핑해서 부품 간 차이를 줄이고 전체 금속성을 낮춘다(금속성이 높을수록 하늘/조명을 반사해 은색으로 번쩍임).
  총몸 t≈0.9 -> 약 0.54 / 탄창 t≈0.78 -> 약 0.50 / 개머리판·핸드가드 t 0~0.9(중앙 0.54) -> 0.35~0.55(중앙 약 0.45)
이미 적용했으면(MetalMatch_Lerp 노드가 있으면) 그 Lerp 의 상수만 갱신한다(여러 번 실행해도 누적되지 않음). 되돌리려면 LO=0, HI=1 로 실행하거나 `py <파일> keep revert`.
-> Data/lyra_m4_metal_match.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_m4_metal_match.json'
LO = 0.35; HI = 0.55
if 'revert' in sys.argv: LO, HI = 0.0, 1.0
MEL = unreal.MaterialEditingLibrary
MP = unreal.MaterialProperty.MP_METALLIC
MATS = ['M_Colt_Main', 'M_Colt_Furniture', 'M_Colt_Mag', 'M_Colt_Rear']
R = {'LO': LO, 'HI': HI}
try:
    for name in MATS:
        row = {}; R[name] = row
        path = '/Game/Furina/M4/' + name
        mat = unreal.load_asset(path)
        if mat is None: row['error'] = 'missing'; continue
        # 이미 만든 Lerp 가 있으면 상수만 갱신
        lerp = None
        cur = MEL.get_material_property_input_node(mat, MP)
        if isinstance(cur, unreal.MaterialExpressionLinearInterpolate) and str(cur.get_editor_property('desc')) == 'MetalMatch_Lerp': lerp = cur
        if lerp is not None:
            lerp.set_editor_property('const_a', LO); lerp.set_editor_property('const_b', HI); row['mode'] = 'update'
        else:
            src = MEL.get_material_property_input_node(mat, MP)
            row['src'] = src.get_class().get_name() if src else None
            if src is None: row['error'] = 'no metallic input node'; continue
            outname = MEL.get_material_property_input_node_output_name(mat, MP)
            lerp = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, 300, 300)
            lerp.set_editor_property('desc', 'MetalMatch_Lerp'); lerp.set_editor_property('const_a', LO); lerp.set_editor_property('const_b', HI)
            ok = MEL.connect_material_expressions(src, outname, lerp, 'Alpha'); row['alpha_connected'] = bool(ok)
            ok2 = MEL.connect_material_property(lerp, '', MP); row['metallic_connected'] = bool(ok2); row['mode'] = 'new'
        MEL.recompile_material(mat)
        row['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(mat, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_METAL_MATCH', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
