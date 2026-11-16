"""Fix (2026-11-16): the muzzle flash point light of BP_M4Flash was BLUE (stored color r 55, g 150, b 255: unreal.Color's constructor takes (b, g, r, a), so Color(255, 130, 35, 255) from the first
flash script meant blue). It lit the weapon and surroundings blue on every shot. Now warm orange (255, 140, 45) set through the r/g/b fields. -> Data/flash_light.json  (PIE stopped)"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    bp = unreal.load_asset('/Game/Furina/M4/BP_M4Flash')
    for h in S.k2_gather_subobject_data_for_blueprint(bp):
        o = L.get_associated_object(L.get_data(h))
        if isinstance(o, unreal.PointLightComponent):
            R['before'] = str(o.get_editor_property('light_color'))
            c = unreal.Color(); c.r = 255; c.g = 140; c.b = 45; c.a = 255
            o.set_editor_property('light_color', c); R['after'] = str(o.get_editor_property('light_color')); R['intensity'] = o.get_editor_property('intensity')
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\flash_light.json', 'w'), indent=1); print('FLASH_LIGHT', R.get('error', R.get('status'))[-200:])
