import unreal,json
R={k:[n for n in dir(getattr(unreal,k)) if n.isupper()] for k in dir(unreal) if k.startswith('CollisionResponse')};R['doc']=unreal.PrimitiveComponent.set_collision_response_to_channel.__doc__
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\collision_api.json','w'),indent=1)
