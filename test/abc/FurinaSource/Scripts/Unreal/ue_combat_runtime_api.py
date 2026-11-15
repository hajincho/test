import unreal,json
R={'timers':{n:getattr(unreal.SystemLibrary,n).__doc__ for n in dir(unreal.SystemLibrary) if 'timer' in n and any(k in n for k in ('set','clear'))}}
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\combat_runtime_api.json','w'),indent=1)
