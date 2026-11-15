import bpy,json,os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\ar15\source\ar15 (2)\ar_15.fbx')
verts=[];faces=[];S=80/4.949013233184814
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 start=len(verts)
 for v in o.data.vertices:
  p=o.matrix_world@v.co;verts.append((p.y*S,-(p.x-.65)*S-10.8,(p.z-.8)*S))
 for p in o.data.polygons:faces.append([start+i for i in p.vertices])
b=BVHTree.FromPolygons(verts,faces,all_triangles=False);R={'scan':[]}
for ix in [0,-.1,.1]:
 for j in range(70,116):
  z=j/10;hit,n,idx,d=b.ray_cast(Vector((ix,-25,z)),Vector((0,1,0)),100);R['scan'].append({'x':ix,'z':z,'hit':list(hit) if hit else None})
R['front_center_vertices']=sorted([list(v) for v in verts if abs(v[0])<.2 and 20<v[1]<38 and v[2]>7],key=lambda x:x[2],reverse=True)[:30]
R['rear_center_vertices']=sorted([list(v) for v in verts if abs(v[0])<.2 and -23<v[1]<-8 and v[2]>7],key=lambda x:x[2],reverse=True)[:50]
R['rear_plane']=[list(v) for v in verts if abs(v[1]+11.757165)<.001 and 9.2<v[2]<10.5 and abs(v[0])<1.5]
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\m4_sights_refine.json','w'),indent=1)
