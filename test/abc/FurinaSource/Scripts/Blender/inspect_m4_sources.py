import bpy,json,os
R={}
for name,p in {'m4':r'C:\Users\fromj\Downloads\ar15\source\ar15 (2)\ar_15.fbx','ammo':r'C:\Users\fromj\Downloads\223-remington-556mm-nato-case-and-shell\source\bullet.fbx','old':r'C:\Users\fromj\Downloads\blender_source_files_freefpstemplate\Blender_Source_Files_FreeFpsTemplate\_Exported\Meshes\SK_AssaultRifle.fbx'}.items():
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=p)
 data=[]
 for o in bpy.context.scene.objects:
  d={'name':o.name,'type':o.type,'dims':list(o.dimensions),'scale':list(o.scale),'location':list(o.location)}
  if o.type=='MESH':
   vs=[o.matrix_world@v.co for v in o.data.vertices];d['bounds']=[[min(v[i] for v in vs),max(v[i] for v in vs)]for i in range(3)];d['materials']=[s.name for s in o.data.materials];d['groups']=[g.name for g in o.vertex_groups];d['verts']=len(vs)
  if o.type=='ARMATURE':d['bones']={b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in o.data.bones}
  data.append(d)
 R[name]=data
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\m4_source_inspect.json','w'),indent=1)
