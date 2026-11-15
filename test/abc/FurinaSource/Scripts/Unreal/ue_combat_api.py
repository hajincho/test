import unreal,json,os
R={}
for cn in ('BlueprintEditorLibrary','BlueprintGraphLibrary','EditorUtilityLibrary','UnrealClipboard','SystemLibrary'):
 cls=getattr(unreal,cn,None)
 R[cn]={n:getattr(cls,n).__doc__ for n in dir(cls or ()) if any(t in n.lower() for t in ('paste','import','export','clipboard','text'))}
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\combat_api.json','w'),indent=1)
