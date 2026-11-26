"""Create the cartridge-head detail material using the supplied Metal008 maps."""
from pathlib import Path
from zipfile import ZipFile

import unreal

from lyra_pzb39 import ASSETS, FOLDER, ROOT


PACKAGE = Path('C:/Users/fromj/Downloads/Metal008_2K-PNG.zip')
MAPS = {
    'Color': (unreal.MaterialProperty.MP_BASE_COLOR, unreal.TextureCompressionSettings.TC_DEFAULT, True),
    'NormalDX': (unreal.MaterialProperty.MP_NORMAL, unreal.TextureCompressionSettings.TC_NORMALMAP, False),
    'Metalness': (unreal.MaterialProperty.MP_METALLIC, unreal.TextureCompressionSettings.TC_MASKS, False),
    'Roughness': (unreal.MaterialProperty.MP_ROUGHNESS, unreal.TextureCompressionSettings.TC_MASKS, False),
}


def import_textures():
    textures = {}
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    work = ROOT / 'Saved/Pzb39Metal008'
    work.mkdir(exist_ok=True)
    with ZipFile(PACKAGE) as archive:
        for kind, (output, compression, srgb) in MAPS.items():
            name = f'T_PZB39_Primer_Metal008_{kind}'
            destination = FOLDER + '/Textures'
            member = f'Metal008_2K-PNG_{kind}.png'
            native = work / member
            native.write_bytes(archive.read(member))
            task = unreal.AssetImportTask()
            task.filename = str(native)
            task.destination_path = destination
            task.destination_name = name
            task.automated = True
            task.replace_existing = True
            tools.import_asset_tasks([task])
            tx = unreal.load_asset(f'{destination}/{name}')
            assert tx, kind
            tx.set_editor_property('compression_settings', compression)
            tx.set_editor_property('srgb', srgb)
            assert ASSETS.save_loaded_asset(tx, False)
            textures[kind] = (output, tx)
    return textures


def material():
    edit = unreal.MaterialEditingLibrary
    name = 'M_PZB39_Primer_Metal008'
    path = f'{FOLDER}/{name}'
    asset = unreal.load_asset(path) if ASSETS.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, FOLDER, unreal.Material, unreal.MaterialFactoryNew())
    sample_types = {
        'Color': unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
        'NormalDX': unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
        'Metalness': unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
        'Roughness': unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    }
    edit.delete_all_material_expressions(asset)
    for row, (kind, (output, texture)) in enumerate(import_textures().items()):
        sample = edit.create_material_expression(asset, unreal.MaterialExpressionTextureSample, -490, row * 260)
        sample.set_editor_property('texture', texture)
        sample.set_editor_property('sampler_type', sample_types[kind])
        assert edit.connect_material_property(sample, 'RGB' if kind in ('Color', 'NormalDX') else 'R', output)
    asset.set_editor_property('used_with_skeletal_mesh', True)
    edit.recompile_material(asset)
    assert ASSETS.save_loaded_asset(asset, False)
    return asset


def apply_primer():
    asset = material()
    mesh = unreal.load_asset(FOLDER + '/SK_FPVM_PZB39')
    slots = list(mesh.materials)
    primer = [slot for slot in slots if str(slot.material_slot_name) == 'Primer_Metal008']
    assert len(primer) == 1
    primer[0].material_interface = asset
    mesh.set_editor_property('materials', slots)
    assert ASSETS.save_loaded_asset(mesh, False)
    print('PZB39_METAL008_ASSIGNED', asset.get_path_name())
