"""blender.exe -b --python render_carbine_frames.py -- <시작> <끝> <간격> <태그> : arms@carbine.fbx 의 옆면/위면 워크벤치 렌더 -> Scratch/carbine_<태그>_<프레임>_<side|top>.png"""
import bpy, sys, math
a = sys.argv[sys.argv.index('--') + 1:]; F0, F1, ST, TAG = int(a[0]), int(a[1]), int(a[2]), a[3]
SRC = r'C:\Users\fromj\Downloads\fps-animated-carbine\source\arms@carbine.fbx'; OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Scratch'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True, anim_offset=0, automatic_bone_orientation=False, ignore_leaf_bones=False)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = 560; sc.render.resolution_y = 360
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'
cam_d = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam; cam_d.type = 'ORTHO'; cam_d.ortho_scale = 1.5
views = {'side': ((2.0, 0.42, 0.12), (math.radians(90), 0, math.radians(90))), 'top': ((0.0, 0.42, 2.0), (0, 0, math.radians(180)))}
for f in range(F0, F1 + 1, ST):
    sc.frame_set(f)
    for v, (loc, rot) in views.items():
        cam.location = loc; cam.rotation_euler = rot; sc.render.filepath = r'%s\carbine_%s_%03d_%s.png' % (OUT, TAG, f, v); bpy.ops.render.render(write_still=True)
print('RENDER_OK')
