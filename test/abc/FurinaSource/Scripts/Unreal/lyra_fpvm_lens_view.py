"""Render the three game lenses inside the ordinary first-person ADS view."""
import sys
import uuid
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, HUD, MATH, PAWN, STRINGS, Graph, chain, wire


FOLDER = '/Game/Furina/FPVM'
EDIT = unreal.MaterialEditingLibrary
ASSETS = unreal.EditorAssetLibrary
LENSES = {
    'kar98k_zf39': ('ZF39', 4., .213, .026, .002, .013),
    'kar98k_zf41': ('ZF41', 1.5, .165, .036, .0015, .010),
    'g43_zf4': ('ZF4', 4., .207, .025, .0017, .011),
}


def lens_material(name, power, radius, gap, line_width, post_width):
    name = 'M_FPVM_LocalLens_' + name
    path = f'{FOLDER}/{name}'
    if ASSETS.does_asset_exist(path):
        material = unreal.load_asset(path)
        EDIT.delete_all_material_expressions(material)
    else:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, FOLDER, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property('material_domain', unreal.MaterialDomain.MD_POST_PROCESS)
    location = next(name for name in dir(unreal.BlendableLocation) if name in
                    ('BL_SCENE_COLOR_AFTER_TONEMAPPING', 'BL_AFTER_TONEMAPPING'))
    material.set_editor_property('blendable_location', getattr(unreal.BlendableLocation, location))
    material.set_editor_property('blendable_priority', 20)
    screen = EDIT.create_material_expression(material, unreal.MaterialExpressionScreenPosition, -600, 0)
    size = EDIT.create_material_expression(material, unreal.MaterialExpressionViewSize, -600, 140)
    scene = EDIT.create_material_expression(material, unreal.MaterialExpressionSceneTexture, -600, 280)
    scene.set_editor_property('scene_texture_id', unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    paint = EDIT.create_material_expression(material, unreal.MaterialExpressionCustom, -290, 0)
    paint.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    inputs = []
    for pin in ('UV', 'Viewport', 'Unfiltered'):
        item = unreal.CustomInput()
        item.set_editor_property('input_name', pin)
        inputs.append(item)
    paint.set_editor_property('inputs', inputs)
    paint.set_editor_property('code', f'''
float2 p = UV - 0.5;
float2 lens = float2(p.x * Viewport.x / Viewport.y, p.y);
float r = length(lens);
float pixel = 1.0 / Viewport.y;
if (r > {radius} + 0.009 + pixel) return Unfiltered;
float2 center = 0.5 + p / {power};
// Composite the focused image and a weaker defocused contribution from
// peripheral rays. Keep this independent of image magnification.
float2 spread = float2(1.0, 1.0) * (0.42 + 0.98 * smoothstep(0.0, {radius}, r)) / Viewport;
float3 field = SceneTextureLookup(ViewportUVToSceneTextureUV(center, 14), 14, true).rgb;
float3 defocused = SceneTextureLookup(ViewportUVToSceneTextureUV(center + float2(spread.x, 0), 14), 14, true).rgb
                  + SceneTextureLookup(ViewportUVToSceneTextureUV(center - float2(spread.x, 0), 14), 14, true).rgb
                  + SceneTextureLookup(ViewportUVToSceneTextureUV(center + float2(0, spread.y), 14), 14, true).rgb
                  + SceneTextureLookup(ViewportUVToSceneTextureUV(center - float2(0, spread.y), 14), 14, true).rgb;
field = lerp(field, defocused * 0.25, 0.18);
float2 cross = lens / ({radius} * 2.0);
float arms = smoothstep({gap} - pixel, {gap} + pixel, abs(cross.x))
           * (1.0 - smoothstep({line_width}, {line_width} + pixel, abs(cross.y)));
float width = {post_width} * saturate(cross.y / 0.065);
float post = smoothstep(0.0, pixel, cross.y) * (1.0 - smoothstep(width, width + pixel, abs(cross.x)));
field = lerp(field, float3(0.013, 0.014, 0.016), saturate(max(post, arms)));
float edge = smoothstep({radius}-0.029, {radius}, r);
field *= lerp(float3(1.0, 1.0, 1.0), float3(0.62, 0.68, 0.73), edge);
float glass = 1.0 - smoothstep({radius} - pixel, {radius} + pixel, r);
float rim = 1.0 - smoothstep({radius} + 0.008, {radius} + 0.008 + pixel, r);
float3 metal = float3(0.029, 0.03, 0.032) + 0.022 * saturate(-lens.y / {radius});
return lerp(Unfiltered, lerp(metal, field, glass), rim);
''')
    for expression, output, pin in ((screen, 'ViewportUV', 'UV'), (size, '', 'Viewport'), (scene, 'Color', 'Unfiltered')):
        assert EDIT.connect_material_expressions(expression, output, paint, pin), pin
    assert EDIT.connect_material_property(paint, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    EDIT.recompile_material(material)
    assert ASSETS.save_loaded_asset(material, False)
    return material


def wire_lenses(pawn, materials):
    graph = Graph(pawn, 'LocalLens_')
    if 'LocalLens_ZF4_Camera' in graph.nodes:
        return
    previous = [node for name, node in graph.nodes.items() if name.startswith('LocalLens_')]
    for node in previous:
        node.rename('Discarded_' + uuid.uuid4().hex)
    if previous:
        graph.editor.remove_nodes(previous)
    field = graph.nodes['ScopeView_SetCamera'].find_input_pin('InFieldOfView')
    field.break_pin_links()
    wire(graph.nodes['ScopeView_StandardFOV'].find_result_pin(), field)
    camera = graph.get('FPCamera')
    active = graph.get('FurinaScopeActive')
    # The applied selection follows the rig, even if the weapon menu changes during a reload.
    selected = graph.get('FurinaVMLastKey')
    sequence = []
    for item in materials:
        name = LENSES[item][0]
        matches = graph.call(name + '_Selected', STRINGS + 'EqualEqual_StrStr', A=selected, B=item).find_result_pin()
        enabled = graph.call(name + '_Active', MATH + 'BooleanAND', A=matches, B=active).find_result_pin()
        weight = graph.call(name + '_Weight', MATH + 'SelectFloat', A=1., B=0., bPickA=enabled).find_result_pin()
        sequence.append(graph.call(name + '_Camera', ENGINE + 'CameraComponent:AddOrUpdateBlendable', target=camera,
                                   InBlendableObject=graph.get('FurinaLocalLens_' + name), InWeight=weight))
    outgoing = graph.nodes['ScopeView_SetCamera'].find_then_pin()
    destinations = list(outgoing.list_connected_pins())
    outgoing.break_pin_links()
    tail = chain(outgoing, sequence)
    for continuation in destinations:
        wire(tail, continuation)


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'End PIE before editing assets'
    materials = {key: lens_material(*style) for key, style in LENSES.items()}
    pawn = unreal.load_asset(PAWN)
    bp = unreal.BlueprintEditorLibrary
    fields = {str(name) for name in bp.list_member_variable_names(pawn)}
    for item in materials:
        variable = 'FurinaLocalLens_' + LENSES[item][0]
        if variable not in fields:
            assert bp.add_member_variable(pawn, variable, bp.get_object_reference_type(unreal.MaterialInterface))
    wire_lenses(pawn, materials)
    hud = unreal.load_asset(HUD)
    Graph(hud).nodes['ScopeView_HasGlass'].find_then_pin().break_pin_links()
    for asset in (pawn, hud):
        unreal.BlueprintEditorLibrary.compile_blueprint(asset)
        assert asset.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR, asset.get_name()
        if asset == pawn:
            defaults = unreal.get_default_object(pawn.generated_class())
            system = unreal.get_default_object(unreal.SystemLibrary)
            for item, material in materials.items():
                system.call_method('SetObjectPropertyByName', (defaults, 'FurinaLocalLens_' + LENSES[item][0], material))
        assert ASSETS.save_loaded_asset(asset, False), asset.get_name()
    print('FPVM_LOCAL_LENSES_SAVED')


if __name__ == '__main__':
    main()
