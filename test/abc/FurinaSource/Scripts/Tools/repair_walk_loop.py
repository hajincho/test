"""Repair a recorded ground-adjustment transient in the periodic walk pelvis track."""
import json,math,os,sys
D=sys.argv[1]
path=os.path.join(D,'ue_walk_tracks.json')
d=json.load(open(path,encoding='utf-8'))
N=d['frames'];old=[list(p) for p in d['hips']]
# There are two identical vertical bob cycles per stride. The first three
# recorded frames include a non-periodic ground-height correction. Fit only the
# settled frames, retaining the authored phase and amplitude of the walk bob.
indices=list(range(3,N))
basis=lambda i:[1,math.cos(4*math.pi*i/N),math.sin(4*math.pi*i/N)]
matrix=[[sum(basis(i)[a]*basis(i)[b] for i in indices) for b in range(3)]+[sum(basis(i)[a]*old[i][2] for i in indices)] for a in range(3)]
for col in range(3):
    pivot=max(range(col,3),key=lambda r:abs(matrix[r][col]))
    matrix[col],matrix[pivot]=matrix[pivot],matrix[col]
    v=matrix[col][col];matrix[col]=[x/v for x in matrix[col]]
    for row in range(3):
        if row==col:continue
        f=matrix[row][col]
        matrix[row]=[a-f*b for a,b in zip(matrix[row],matrix[col])]
coeff=[r[-1] for r in matrix]
for i,p in enumerate(d['hips']):p[2]=sum(a*b for a,b in zip(coeff,basis(i)))
new=d['hips']
def metrics(points):
    v=[points[(i+1)%N][2]-points[i][2] for i in range(N)]
    return {'seam_step_cm':abs(v[-1]),'max_step_cm':max(map(abs,v)),'max_acceleration_cm_per_frame2':max(abs(v[i]-v[(i-1)%N]) for i in range(N))}
R={'frames':N,'fps':d['fps'],'before':metrics(old),'after':metrics(new),'fit_coefficients':coeff,
   'settled_fit_rmse_cm':math.sqrt(sum((new[i][2]-old[i][2])**2 for i in indices)/len(indices)),
   'changes_cm':[new[i][2]-old[i][2] for i in range(N)]}
assert R['after']['seam_step_cm']<.7
assert R['after']['max_acceleration_cm_per_frame2']<.25
assert R['settled_fit_rmse_cm']<.1
with open(path,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False)
with open(os.path.join(D,'walk_loop_repair.json'),'w',encoding='utf-8') as f:json.dump(R,f,indent=1)
print(json.dumps({k:v for k,v in R.items() if k!='changes_cm'}))
