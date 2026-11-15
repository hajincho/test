"""Rig supplied M4 visual to the existing weapon animation skeleton; export real-size .223 parts."""
import bpy,json,os
from mathutils import Vector,Matrix
ROOT=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource';OUT=os.path.join(ROOT,'FBX','M4');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\blender_source_files_freefpstemplate\Blender_Source_Files_FreeFpsTemplate\_Exported\Meshes\SK_AssaultRifle.fbx',automatic_bone_orientation=False,ignore_leaf_bones=False)
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
for o in list(bpy.context.scene.objects):
 if o!=arm:bpy.data.objects.remove(o,do_unlink=True)
arm.animation_data_clear()
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\ar15\source\ar15 (2)\ar_15.fbx')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];S=80/4.949013233184814
vs=[];mag_count=0
for o in meshes:
 coords=[o.matrix_world@v.co for v in o.data.vertices]
 o.parent=arm;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4)
 for g in list(o.vertex_groups):o.vertex_groups.remove(g)
 grip=o.vertex_groups.new(name='Grip');mag=o.vertex_groups.new(name='Magazine')
 for v,p in zip(o.data.vertices,coords):
  q=Vector((p.y*S,(p.x-.65)*S+10.8,(p.z-.8)*S));v.co=q;vs.append([q.x,-q.y,q.z])
  # Keep the receiver/grip rigid; the detachable magazine follows the template reload bone.
  is_mag=p.z<.85 and -.55<p.x<.3
  (mag if is_mag else grip).add([v.index],1,'REPLACE');mag_count+=int(is_mag)
 mod=o.modifiers.new('WeaponRig','ARMATURE');mod.object=arm
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'SK_M4A1.fbx'),use_selection=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True)
R={'length_cm':80,'muzzle':[0,(-(-2.5313)+.65)*S-10.8,(1.1-.8)*S],'case_port':[-2,(-.4+.65)*S-10.8,(1.08-.8)*S],'stock_butt':[0,-(2.4177-.65)*S-10.8,(1.08-.8)*S],'sight_z':(1.44-.8)*S,'mag_vertices':mag_count,'verts':vs}
json.dump(R,open(os.path.join(ROOT,'Data','m4_geometry.json'),'w'),indent=1)
# Export only the projectile for flight, and an empty case for ejection (never eject a complete cartridge).
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\223-remington-556mm-nato-case-and-shell\source\bullet.fbx')
objects={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
for name,src in [('SM_223Case','Cylinder'),('SM_223Projectile','Cylinder.001')]:
 o=objects[src];coords=[o.matrix_world@v.co for v in o.data.vertices];center=sum(coords,Vector())/len(coords)
 o.matrix_world=Matrix.Identity(4)
 for v,p in zip(o.data.vertices,coords):v.co=(p-center)*(.0572/(1.6643779+1.5001512))
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,name+'.fbx'),use_selection=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True)

