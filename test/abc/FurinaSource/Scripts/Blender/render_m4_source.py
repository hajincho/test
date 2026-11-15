import bpy,math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\ar15\source\ar15 (2)\ar_15.fbx')
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
for o in sc.objects:
 if o.type=='MESH':
  for m in o.data.materials:m.diffuse_color=(.2,.25,.3,1)
bpy.ops.object.camera_add(location=(0,-10,1));c=bpy.context.object;c.rotation_euler=(Vector((0,0,.7))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=5.6;sc.camera=c;sc.render.resolution_x=1200;sc.render.resolution_y=500;sc.render.resolution_percentage=100;sc.render.filepath=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\m4_side.png';bpy.ops.render.render(write_still=True)
