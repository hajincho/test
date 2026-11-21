"""blender -b --python de_weapons_inspect.py : 독일 무기 원본(FurinaWeaponSrc/Germany)을 하나씩 가져와 크기/부품/머티리얼/텍스처/애니메이션 조사 -> FurinaSource/Data/de_weapons_inspect.json"""
import bpy, json, os, glob
import numpy as np
SRC = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\de_weapons_inspect.json'
FILES = {
 'ammo_7_92x94': '7_92x94_ammo/Patronen_painted.fbx', 'g43': 'g43/source/Gewehr43.fbx', 'grw34': 'grw34/source/Blender_unzipped/sgw34.blend',
 'kar98k': 'kar98k/source/model_unzipped/model/model.dae', 'mauser_clip': 'mauser_ammo_clip/source/bullet2.blend', 'mg34': 'mg34/source/mg 34 full tex.blend',
 'mg42': 'mg42/source/MG 42.fbx', 'mortar_shell': 'Mortar_Shell/source/ArtilleryShell.fbx', 'mp38': 'mp38/MP38_Rosewood_Metal060B.fbx', 'mp40': 'mp40/source/MP40_unzipped/MP40/MP40.fbx',
 'p08': 'p08/source/model_unzipped/model/model.dae', 'p38': 'p38/source/Walther_P38+SatinFloor.fbx', 'panzerfaust': 'panzerfaust/source/model_unzipped/model/model.dae',
 'panzerschreck': 'panzerschreck/source/model_unzipped/model/model.dae', 'panzerschreck_rocket': 'panzerschreck/Panzerschreck_Rocket/Panzerschreck_Rocket.fbx',
 'pp': 'pp/source/walther_pp_unzipped/walther_pp.obj', 'pzb39': 'PzB39/PzB39_Colored.fbx', 'stg44': 'stg44/source/STG44_Full.fbx', 'zf4': 'zf4_scope/ZF4_scope_with_mount.fbx',
 'zf39': 'zf39_scope/*.stl', 'zf41': 'zf41_scope/new ZF41/*.stl',
}
R = {}
for key, rel in FILES.items():
    bpy.ops.wm.read_factory_settings(use_empty=True); e = {'file': rel}
    try:
        paths = sorted(glob.glob(os.path.join(SRC, rel)))
        for p in paths:
            ext = p.lower().rsplit('.', 1)[1]
            if ext == 'fbx': bpy.ops.import_scene.fbx(filepath=p)
            elif ext == 'obj': bpy.ops.wm.obj_import(filepath=p)
            elif ext == 'stl': bpy.ops.wm.stl_import(filepath=p)
            elif ext == 'dae': bpy.ops.wm.collada_import(filepath=p)
            elif ext == 'blend':
                with bpy.data.libraries.load(p, link=False) as (src, dst): dst.objects = list(src.objects)
                for o in dst.objects:
                    if o is not None: bpy.context.scene.collection.objects.link(o)
        bpy.context.view_layer.update()
        meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        e['objects'] = len(bpy.context.scene.objects); e['meshes'] = len(meshes); e['types'] = sorted(set(o.type for o in bpy.context.scene.objects))
        e['verts'] = sum(len(o.data.vertices) for o in meshes); e['tris'] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
        pts = []
        for o in meshes:
            M = np.array(o.matrix_world); co = np.array([v.co[:] for v in o.data.vertices]) if len(o.data.vertices) else np.zeros((0, 3))
            if len(co): pts.append(co @ M[:3, :3].T + M[:3, 3])
        if pts:
            P = np.vstack(pts); e['bmin'] = P.min(0).round(4).tolist(); e['bmax'] = P.max(0).round(4).tolist(); e['size'] = (P.max(0) - P.min(0)).round(4).tolist()
        e['mesh_names'] = [o.name for o in meshes][:30]
        mats = {}
        for o in meshes:
            for s in o.material_slots:
                m = s.material
                if m and m.name not in mats:
                    imgs = []
                    if m.use_nodes:
                        for n in m.node_tree.nodes:
                            if n.type == 'TEX_IMAGE' and n.image: imgs.append(os.path.basename(n.image.filepath or n.image.name))
                    mats[m.name] = imgs
        e['materials'] = mats; e['actions'] = [a.name for a in bpy.data.actions]; e['unit_scale'] = bpy.context.scene.unit_settings.scale_length
    except Exception as ex: e['error'] = str(ex)[:300]
    R[key] = e; print('INSPECT', key, e.get('size'), e.get('meshes'), e.get('error', ''))
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('DE_INSPECT_DONE')
