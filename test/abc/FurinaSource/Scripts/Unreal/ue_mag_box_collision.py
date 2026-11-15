"""SM_M4Mag: replace the convex hull collision (the dropped magazine fell through the floor with it) with one box from the mesh bounds -> Data/mag_box_collision.json"""
import unreal, json, traceback
def main():
    R = {}
    m = unreal.load_asset('/Game/Furina/M4/SM_M4Mag'); b = m.get_bounds(); R['bounds'] = [str(b.origin), str(b.box_extent)]
    bs = m.get_editor_property('body_setup'); g = bs.get_editor_property('agg_geom')
    R['convex_before'] = len(g.get_editor_property('convex_elems'))
    box = unreal.KBoxElem(); box.set_editor_property('center', b.origin); box.set_editor_property('x', b.box_extent.x * 2); box.set_editor_property('y', b.box_extent.y * 2); box.set_editor_property('z', b.box_extent.z * 2)
    g.set_editor_property('convex_elems', []); g.set_editor_property('box_elems', [box]); bs.set_editor_property('agg_geom', g)
    m.set_editor_property('body_setup', bs)
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(m, False)
    g2 = m.get_editor_property('body_setup').get_editor_property('agg_geom'); R['after'] = [len(g2.get_editor_property('convex_elems')), len(g2.get_editor_property('box_elems'))]
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\mag_box_collision.json', 'w'), indent=1); print('MAG_BOX', R)
