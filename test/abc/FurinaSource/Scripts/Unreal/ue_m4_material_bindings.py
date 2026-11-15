import unreal,json
s=unreal.load_asset('/Game/Furina/M4/SK_M4A1');slots=s.get_editor_property('materials')
for i,slot in enumerate(slots):
 name=str(slot.get_editor_property('imported_material_slot_name'));slot.set_editor_property('material_interface',unreal.load_asset('/Game/Furina/M4/M_M4_'+name));slots[i]=slot
s.set_editor_property('materials',slots);assert unreal.EditorAssetLibrary.save_loaded_asset(s,False)
