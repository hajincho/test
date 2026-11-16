"""Blender headless: downsizes the Colt PBR textures to 2048x2048 (the originals are up to 58 MB each) -> FBX/M4/ColtTex/<material>_<Map>.png
(maps: BaseColor, Metallic, Roughness, Normal (DirectX = what Unreal expects), AO)"""
import bpy, os
SRC = r'C:\Users\fromj\Downloads\colt-m4a1-carbine\textures'; OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\FBX\M4\ColtTex'; os.makedirs(OUT, exist_ok=True)
files = {
 'colt_m4_main': {'BaseColor': 'colt_m4_main_BaseColor_gfl.png', 'Metallic': 'colt_m4_main_Metallic_gfl.png', 'Roughness': 'colt_m4_main_Roughness_gfl.png', 'Normal': 'colt_m4_main_Normal_DirectX_gfl.png', 'AO': 'colt_m4_main_AO.png'},
 'colt_m4_furniture': {'BaseColor': 'colt_m4_furniture_BaseColor.png', 'Metallic': 'colt_m4_furniture_Metallic.png', 'Roughness': 'colt_m4_furniture_Roughness.png', 'Normal': 'colt_m4_furniture_Normal_DirectX.png', 'AO': 'colt_m4_furniture_AO.png'},
 'matech_rear_sight': {'BaseColor': 'matech_rear_sight_BaseColor.png', 'Metallic': 'matech_rear_sight_Metallic.png', 'Roughness': 'matech_rear_sight_Roughness.png', 'Normal': 'matech_rear_sight_Normal_DirectX.png', 'AO': 'matech_rear_sight_AO.png'},
 'stanag_mag': {'BaseColor': 'stanag_mag_BaseColor.png', 'Metallic': 'stanag_mag_Metallic.png', 'Roughness': 'stanag_mag_Roughness.png', 'Normal': 'stanag_mag_Normal_directx.png', 'AO': 'stanag_mag_AO.png'}}
for mat, maps in files.items():
    for k, fn in maps.items():
        im = bpy.data.images.load(os.path.join(SRC, fn)); w, h = im.size
        im.scale(min(w, 2048), min(h, 2048)); im.filepath_raw = os.path.join(OUT, '%s_%s.png' % (mat, k)); im.file_format = 'PNG'; im.save()
        print('TEX', mat, k, w, h); bpy.data.images.remove(im)
print('COLT_TEX done')
