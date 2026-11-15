import bpy,json,glob
R={}
for p in glob.glob(r'C:\Users\fromj\Downloads\blender_source_files_freefpstemplate\Blender_Source_Files_FreeFpsTemplate\**\*.blend',recursive=True):
 with bpy.data.libraries.load(p,link=False) as (src,dst):R[p]=list(src.actions)
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fps_blend_actions.json','w'),indent=1)
