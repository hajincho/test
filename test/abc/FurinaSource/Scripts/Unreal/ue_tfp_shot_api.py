import unreal,json
json.dump([n for n in dir(unreal.AutomationLibrary) if 'screenshot' in n],open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\tfp_shot_api.json','w'))
