import unreal, json
m = unreal.load_asset('/Game/Furina/M4/SM_M4Mag'); bs = m.get_editor_property('body_setup'); g = bs.get_editor_property('agg_geom')
R = dict(convex=len(g.get_editor_property('convex_elems')), box=len(g.get_editor_property('box_elems')), sphyl=len(g.get_editor_property('sphyl_elems')), sphere=len(g.get_editor_property('sphere_elems')), trace_flag=str(bs.get_editor_property('collision_trace_flag')))
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\mag_collision_check.json', 'w')); print('MAG_COLL', R)
