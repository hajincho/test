"""Keep the existing Panzerfaust meshes visible from either side."""
import unreal


MATERIAL = '/Game/Furina/Weapons/Germany/panzerfaust/MI_DE_panzerfaust_Material'
VIEWMODEL = '/Game/Furina/FPVM/PANZERFAUST/SK_FPVM_PANZERFAUST'
WARHEAD = '/Game/Furina/FPVM/PANZERFAUST/SM_FPVM_PzfWarhead'


def ensure_two_sided():
    asset = unreal.load_asset(MATERIAL)
    assert isinstance(asset, unreal.MaterialInstanceConstant)
    overrides = asset.get_editor_property('base_property_overrides')
    overrides.set_editor_property('override_two_sided', True)
    overrides.set_editor_property('two_sided', True)
    asset.set_editor_property('base_property_overrides', overrides)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
    for reference, slots in ((VIEWMODEL, 'materials'), (WARHEAD, 'static_materials')):
        mesh = unreal.load_asset(reference)
        assert any(slot.material_interface == asset for slot in mesh.get_editor_property(slots)), reference
    print('PANZERFAUST_TWO_SIDED_SAVED')


if __name__ == '__main__':
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    ensure_two_sided()
