"""Read-only FBX morph inspection: verify eye-closing shapes contain real deltas."""
import bpy,sys,json,math
args=sys.argv[sys.argv.index('--')+1:]
source,dest=args
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=source,automatic_bone_orientation=False,ignore_leaf_bones=False)
R={'source':source,'meshes':[]}
for o in bpy.data.objects:
    if o.type!='MESH' or not o.data.shape_keys:continue
    base=o.data.shape_keys.key_blocks[0]
    m={'name':o.name,'vertices':len(o.data.vertices),'shapes':{}}
    for sk in o.data.shape_keys.key_blocks:
        if sk==base:continue
        moves=[(i,(p.co-base.data[i].co).length) for i,p in enumerate(sk.data) if (p.co-base.data[i].co).length>1e-7]
        if moves:
            points=[base.data[i].co for i,v in moves]
            bounds=[[min(p[j] for p in points),max(p[j] for p in points)] for j in range(3)]
        else:bounds=None
        m['shapes'][sk.name]={'moved_vertices':len(moves),'max_delta':max((d for i,d in moves),default=0),'bounds':bounds,'relative':sk.relative_key.name}
    R['meshes'].append(m)
with open(dest,'w',encoding='utf-8') as f:json.dump(R,f,ensure_ascii=False,indent=1)
print('BLINK_SHAPES_INSPECTED')
