import unreal,json
n=unreal.AnimationLibrary.get_nodes_of_class(unreal.load_asset('/Game/Furina/ABP_Furina'),unreal.AnimGraphNode_ModifyCurve,True)[0];v=n.get_editor_property('node')
R={'struct':v.export_text(),'api':[k for k in dir(v) if not k.startswith('_')],'import':getattr(v,'import_text',None).__doc__}
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\combat_struct.json','w'),indent=1)
