"""Dumps the components of BP_M4Flash (class default subobjects): name, mesh, material, scale, location, rotation, hidden_in_game, visible -> Data/flash_probe.json"""
import unreal, json
S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
bp = unreal.load_asset('/Game/Furina/M4/BP_M4Flash'); R = {}
for h in S.k2_gather_subobject_data_for_blueprint(bp):
    o = L.get_associated_object(L.get_data(h)); n = str(L.get_variable_name(L.get_data(h)))
    d = {'class': o.get_class().get_name() if o else None}
    if isinstance(o, unreal.StaticMeshComponent):
        d.update(mesh=str(o.static_mesh.get_name()) if o.static_mesh else None, mat=[str(m.get_path_name()) for m in o.get_materials()], scale=str(o.get_editor_property('relative_scale3d')), loc=str(o.get_editor_property('relative_location')), rot=str(o.get_editor_property('relative_rotation')), hidden=o.get_editor_property('hidden_in_game'), visible=o.get_editor_property('visible'))
    R[n] = d
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\flash_probe.json', 'w'), indent=1); print('FLASH_PROBE')
