"""Import the scoped game meshes and apply their supplied PBR maps."""
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_receiver_import import import_viewmodel, receiver_material


ROOT = Path(unreal.Paths.project_dir()).resolve()
FOLDER = '/Game/Furina/FPVM/ScopeMetals'
ASSETS = unreal.EditorAssetLibrary
EDIT = unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
TEXTURES = {
    'Color': (unreal.TextureCompressionSettings.TC_DEFAULT, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR),
    'NormalDX': (unreal.TextureCompressionSettings.TC_NORMALMAP, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL),
    'Metalness': (unreal.TextureCompressionSettings.TC_MASKS, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS),
    'Roughness': (unreal.TextureCompressionSettings.TC_MASKS, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS),
}
STYLES = {
    'ZF39': ('Kar98k', 'kar98k_zf39', 'Metal063', (.28, .31, .35), .22, (.30, .33, .37), .30),
    'ZF41': ('Kar98k', 'kar98k_zf41', 'Metal063', (.24, .27, .30), .29, (.30, .33, .35), .38),
    'ZF4': ('G43', 'g43_zf4', 'Metal038', (.28, .30, .34), .28, (.43, .42, .40), .41),
}


def source_maps(number, folder=FOLDER, source='FurinaSource/Textures/FPVM/Metals'):
    maps = {}
    for role, (compression, _sampler) in TEXTURES.items():
        name = f'T_FPVM_{number}_{role}'
        path = f'{folder}/{name}'
        if not ASSETS.does_asset_exist(path):
            task = unreal.AssetImportTask()
            task.filename = str(ROOT / source / (name + '.png'))
            task.destination_path = folder
            task.destination_name = name
            task.automated = True
            TOOLS.import_asset_tasks([task])
        texture = unreal.load_asset(path)
        assert texture, path
        texture.set_editor_property('srgb', role == 'Color')
        texture.set_editor_property('compression_settings', compression)
        assert ASSETS.save_loaded_asset(texture, False)
        maps[role] = texture
    return maps


def rendered_metal(name, maps, tint, rough_bias, folder=FOLDER):
    path = f'{folder}/M_FPVM_{name}'
    if ASSETS.does_asset_exist(path):
        return unreal.load_asset(path)
    material = TOOLS.create_asset('M_FPVM_' + name, folder, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property('used_with_skeletal_mesh', True)

    def expression(cls, x, y):
        return EDIT.create_material_expression(material, cls, x, y)

    def scalar(number, x, y):
        expr = expression(unreal.MaterialExpressionConstant, x, y)
        expr.set_editor_property('r', number)
        return expr

    def pin(node, output, end, name):
        assert EDIT.connect_material_expressions(node, output, end, name), name

    def result(node, output, prop):
        assert EDIT.connect_material_property(node, output, prop), prop

    samples = {}
    for row, (role, texture) in enumerate(maps.items()):
        sample = expression(unreal.MaterialExpressionTextureSample, -740, row * 260)
        sample.set_editor_property('texture', texture)
        sample.set_editor_property('sampler_type', TEXTURES[role][1])
        samples[role] = sample

    tone = expression(unreal.MaterialExpressionConstant3Vector, -740, -170)
    tone.set_editor_property('constant', unreal.LinearColor(*tint, 1.))
    color = expression(unreal.MaterialExpressionMultiply, -240, 0)
    pin(samples['Color'], 'RGB', color, 'A')
    pin(tone, '', color, 'B')
    result(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    result(samples['NormalDX'], 'RGB', unreal.MaterialProperty.MP_NORMAL)
    metal = expression(unreal.MaterialExpressionLinearInterpolate, -240, 500)
    pin(scalar(.69, -420, 570), '', metal, 'A')
    pin(scalar(.93, -420, 640), '', metal, 'B')
    pin(samples['Metalness'], 'R', metal, 'Alpha')
    result(metal, '', unreal.MaterialProperty.MP_METALLIC)
    rough = expression(unreal.MaterialExpressionLinearInterpolate, -240, 760)
    pin(scalar(rough_bias, -420, 810), '', rough, 'A')
    pin(scalar(rough_bias + .30, -420, 880), '', rough, 'B')
    pin(samples['Roughness'], 'R', rough, 'Alpha')
    result(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    EDIT.recompile_material(material)
    assert ASSETS.save_loaded_asset(material, False)
    return material


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE before editing assets'
    source = {number: source_maps(number) for number in ('Metal063', 'Metal038')}
    interior = receiver_material()
    for scope, (family, key, metal, tint, rough, mount_tint, mount_rough) in STYLES.items():
        mesh, report = import_viewmodel(ROOT, family, scope, interior, key)
        body = rendered_metal(f'{scope}_{metal}_Body', source[metal], tint, rough)
        mount = rendered_metal(f'{scope}_{metal}_Mount', source[metal], mount_tint, mount_rough)
        slots = list(mesh.materials)
        covered = set()
        for slot in slots:
            name = str(slot.material_slot_name)
            if name.startswith('Mount_'):
                slot.material_interface = mount
                covered.add('mount')
            elif name.startswith(scope + '_') and not name.endswith('_Glass'):
                slot.material_interface = body
                covered.add('body')
        assert covered == {'body', 'mount'}, (scope, [str(slot.material_slot_name) for slot in slots])
        mesh.set_editor_property('materials', slots)
        assert ASSETS.save_loaded_asset(mesh, False)
        print(f'FPVM_SCOPE_METAL_SAVED {scope} {metal} {report["vertices"]}')


if __name__ == '__main__':
    main()
