"""blender.exe -b --python inspect_pistol_fbx.py : Downloads/fps-pistol-animations/source/Armpist.fbx 의 액션/뼈/객체/타임라인 덤프 -> Data/pistol_fbx_inspect.json"""
import bpy, json, math
SRC = r'C:\Users\fromj\Downloads\fps-pistol-animations\source\Armpist.fbx'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\pistol_fbx_inspect.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True, anim_offset=0, automatic_bone_orientation=False, ignore_leaf_bones=False)
sc = bpy.context.scene
R = {'fps': sc.render.fps, 'frame_range': [sc.frame_start, sc.frame_end], 'unit_scale': sc.unit_settings.scale_length}
R['objects'] = [[o.name, o.type, (o.parent.name if o.parent else None), [round(x, 3) for x in o.location], [round(math.degrees(x), 1) for x in o.rotation_euler], [round(x, 3) for x in o.scale]] for o in bpy.data.objects]
R['meshes'] = [[o.name, len(o.data.vertices), [round(x, 3) for x in o.dimensions]] for o in bpy.data.objects if o.type == 'MESH']
R['armatures'] = [{'name': o.name, 'n': len(o.data.bones), 'bones': [b.name for b in o.data.bones]} for o in bpy.data.objects if o.type == 'ARMATURE']
R['actions'] = []
for a in bpy.data.actions:
    fr = a.frame_range; fcs = []
    try: fcs = list(a.fcurves)
    except Exception: pass
    if not fcs:
        try: fcs = [fc for layer in a.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
        except Exception: fcs = []
    bones = set(fc.data_path.split('"')[1] for fc in fcs if '"' in fc.data_path)
    nk = sum(len(fc.keyframe_points) for fc in fcs)
    R['actions'].append({'name': a.name, 'frame_range': [fr[0], fr[1]], 'frames': round(fr[1] - fr[0], 1), 'seconds': round((fr[1] - fr[0]) / R['fps'], 2), 'n_fcurves': len(fcs), 'n_keys': nk, 'n_bones': len(bones)})
R['markers'] = [[m.name, m.frame] for m in sc.timeline_markers]
R['anim_data'] = [[o.name, o.animation_data.action.name if o.animation_data and o.animation_data.action else None] for o in bpy.data.objects]
json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False); print('INSPECT_OK', len(R['actions']))
