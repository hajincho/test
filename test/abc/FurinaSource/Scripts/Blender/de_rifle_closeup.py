"""blender -b --python de_rifle_closeup.py -- <키> <y0> <y1> : 정리본 FBX 의 y0~y1(cm, 총구 -Y) 구간 옆/위 정사영 확대(20 px/cm, 5 cm 눈금선) -> Data/de_close_<키>_<side|top>.png
 옆: 화면 왼쪽 = 총구(-Y), 위 = +Z.  위: 화면 왼쪽 = 총구, 화면 위 = 총의 오른쪽(-X)."""
import bpy, sys, math
A = sys.argv[sys.argv.index('--') + 1:]; K, Y0, Y1 = A[0], float(A[1]), float(A[2]); H = float(A[3]) if len(A) > 3 else 22.0; ZC = float(A[4]) if len(A) > 4 else 4.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany\_export\SM_DE_%s.fbx' % K)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True
for m in bpy.data.materials: m.diffuse_color = (0.6, 0.6, 0.62, 1)
grid = bpy.data.materials.new('G'); grid.diffuse_color = (1, 0.2, 0.2, 1)
W = (Y1 - Y0)
for yy in range(int(math.floor(Y0 / 5) * 5), int(Y1) + 1, 5):   # 5 cm 눈금: 얇은 판(옆/위 둘 다 보이게)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, yy / 100.0, 0)); c = bpy.context.object; c.scale = (0.30, 0.0004, 0.30); c.data.materials.append(grid)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
yc = (Y0 + Y1) / 2 / 100.0
for nm, loc, rot, res in (('side', (1.0, yc, ZC / 100), (90, 0, 90), (int(W * 20), int(H * 20))), ('top', (0, yc, 1.0), (0, 0, 90), (int(W * 20), int(H * 20))), ('front', (0, -1.0, ZC / 100), (90, 0, 0), (int(H * 20), int(H * 20)))):
    sc.render.resolution_x, sc.render.resolution_y = res; cd.ortho_scale = (W if nm != 'front' else H) / 100.0
    cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
    sc.render.filepath = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\de_close_%s_%s.png' % (K, nm); bpy.ops.render.render(write_still=True)
print('CLOSE_OK')
