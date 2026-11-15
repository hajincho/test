import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
unreal.EditorLoadingAndSavingUtils.load_map('/Game/3DPlatformerGameBundle/Levels/ExampleLevel')
a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors();R['text']=[]
for x in a:
 for c in x.get_components_by_class(unreal.TextRenderComponent):R['text'].append({'actor':x.get_name(),'text':str(c.get_editor_property('text'))})
json.dump(R,open(os.path.join(D,'combat_screen_text.json'),'w'),ensure_ascii=False,indent=1)
