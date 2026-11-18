"""blender.exe -b --python inspect_carbine_fbx.py : Downloads/fps-animated-carbine/source/arms@carbine.fbx 의 액션(애니메이션) 목록과 구조 덤프 -> Data/carbine_fbx_inspect.json"""
import bpy, json, math
SRC = r'C:\Users\fromj\Downloads\fps-animated-carbine\source\arms@carbine.fbx'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\carbine_fbx_inspect.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True, anim_offset=0, automatic_bone_orientation=False, ignore_leaf_bones=False)
R = {'fps': bpy.context.scene.render.fps, 'frame_range': [bpy.context.scene.frame_start, bpy.context.scene.frame_end]}
R['objects'] = [[o.name, o.type, (o.parent.name if o.parent else None), [round(x, 3) for x in o.location], [round(math.degrees(x), 1) for x in o.rotation_euler], [round(x, 3) for x in o.scale]] for o in bpy.data.objects]
R['actions'] = []
for a in bpy.data.actions:
    fr = a.frame_range; paths = set()
    try: fcs = list(a.fcurves)
    except Exception: fcs = []
    if not fcs:
        try:
            fcs = [fc for layer in a.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
        except Exception: fcs = []
    for fc in fcs: paths.add(fc.data_path.split('"')[1] if '"' in fc.data_path else fc.data_path)
    R['actions'].append({'name': a.name, 'frame_range': [fr[0], fr[1]], 'frames': round(fr[1] - fr[0], 1), 'seconds': round((fr[1] - fr[0]) / R['fps'], 2), 'n_fcurves': len(fcs), 'bones': sorted(paths)[:80], 'n_bones': len(paths)})
R['armatures'] = [{'name': o.name, 'bones': [b.name for b in o.data.bones][:150], 'n': len(o.data.bones)} for o in bpy.data.objects if o.type == 'ARMATURE']
R['meshes'] = [[o.name, len(o.data.vertices), [round(x, 2) for x in o.dimensions]] for o in bpy.data.objects if o.type == 'MESH']
R['markers'] = [[m.name, m.frame] for m in bpy.context.scene.timeline_markers]
json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False)
print('INSPECT_OK', len(R['actions']))
