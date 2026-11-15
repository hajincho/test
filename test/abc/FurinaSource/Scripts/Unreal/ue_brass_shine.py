"""Brass look for the ejected 223 cases (M_Brass): metallic 1, golden base colour, low roughness and a fresnel-driven emissive rim so the
case catches the light even where there is no reflection capture (2026-11-15)."""
import unreal, json
def main():
    ml = unreal.MaterialEditingLibrary; e = unreal.EditorAssetLibrary
    m = unreal.load_asset('/Game/Furina/M4/M_Brass'); ml.delete_all_material_expressions(m)
    def c3(r, g, b, x, y):
        n = ml.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, x, y); n.set_editor_property('constant', unreal.LinearColor(r, g, b, 1)); return n
    def c1(v, x, y):
        n = ml.create_material_expression(m, unreal.MaterialExpressionConstant, x, y); n.set_editor_property('r', v); return n
    ml.connect_material_property(c3(0.80, 0.56, 0.18, -600, 0), '', unreal.MaterialProperty.MP_BASE_COLOR)
    ml.connect_material_property(c1(1.0, -600, 150), '', unreal.MaterialProperty.MP_METALLIC)
    ml.connect_material_property(c1(0.16, -600, 250), '', unreal.MaterialProperty.MP_ROUGHNESS)
    ml.connect_material_property(c1(0.9, -600, 350), '', unreal.MaterialProperty.MP_SPECULAR)
    fres = ml.create_material_expression(m, unreal.MaterialExpressionFresnel, -700, 500)
    fres.set_editor_property('exponent', 2.5); fres.set_editor_property('base_reflect_fraction', 0.08)
    tint = c3(1.7, 1.05, 0.28, -700, 650)
    rim = ml.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, 520)
    ml.connect_material_expressions(fres, '', rim, 'A'); ml.connect_material_expressions(tint, '', rim, 'B')
    base_glow = c3(0.16, 0.09, 0.02, -450, 700)
    add = ml.create_material_expression(m, unreal.MaterialExpressionAdd, -250, 560)
    ml.connect_material_expressions(rim, '', add, 'A'); ml.connect_material_expressions(base_glow, '', add, 'B')
    ml.connect_material_property(add, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    ml.recompile_material(m); ok = e.save_loaded_asset(m, False)
    json.dump({'saved': ok}, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\brass_shine.json', 'w'))
    print('BRASS_SHINE', ok); del m
main(); del main
