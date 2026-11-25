"""Fit the MP38 and MP40 support palms to their exported game meshes."""

import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fpvm_fit_kar98k_contact import WORK, component_pose, dominant, sdist, stock_surface

ANGLE_LIMIT = math.radians(52.)
MIRROR = Matrix.Diagonal((1., -1., 1., 1.))


def posed_points(mesh, groups, owners, bind, posed):
    digits = ('Thumb', 'IndexFinger', 'MiddleFinger', 'RingFinger', 'LittleFinger')
    names = ('Left-wrist', *digits)
    values = {}
    weights = {}
    matrices = {name: posed[name] @ ref.inverted() for name, ref in bind.items() if name in posed}
    for label in names:
        indices = [v.index for v in mesh.data.vertices if owners[v.index].startswith(label)
                   and (label == 'Left-wrist' or owners[v.index].endswith('_L'))]
        for idx in indices[::max(1,len(indices)//30)]:
            v = mesh.data.vertices[idx]
            rest = mesh.matrix_world @ v.co
            total = sum(g.weight for g in v.groups if groups[g.group] in matrices)
            if not total:
                continue
            pivot = np.zeros(4)
            other = np.zeros(3)
            for g in v.groups:
                bone = groups[g.group]
                if bone not in matrices:
                    continue
                weight = g.weight / total
                point = matrices[bone] @ rest
                if bone == 'Left-wrist' or bone.endswith('_L') and bone.startswith(digits):
                    pivot += np.array((*point, 1.)) * weight
                else:
                    other += np.array(point) * weight
            values.setdefault(label,[]).append(pivot)
            weights.setdefault(label,[]).append(other)
    return {name:(np.array(values[name]),np.array(weights[name])) for name in labels_present(values)}


def labels_present(points):
    return [name for name, rows in points.items() if rows]


def angle(a,b):
    return a.normalized().angle(b.normalized(),0.)


def fitted_elbow(shoulder, elbow, wrist, target, palm):
    a,b = (elbow-shoulder).length,(wrist-elbow).length
    reach = target - shoulder
    length = reach.length
    if not abs(a-b)+.002 < length < a+b-.0015:
        return None
    axis = reach.normalized()
    p = elbow - shoulder
    radial=(p-axis*p.dot(axis)).normalized()
    d = (length*length+a*a-b*b)/(2*length)
    height = math.sqrt(max(0.,a*a-d*d))
    desired = axis*palm.dot(axis) - palm
    swivel = 0.
    if desired.length > .001:
        preferred=desired.normalized()
        swivel=math.atan2(axis.dot(radial.cross(preferred)),radial.dot(preferred))
        swivel=max(-ANGLE_LIMIT,min(ANGLE_LIMIT,swivel))
    return shoulder+axis*d+(Quaternion(axis,swivel)@radial)*height


def fit(name, mesh, groups, owners, data):
    surface = stock_surface(mesh, owners)
    reference = {key: component_pose(x) for key,x in data['rest'].items() if not key.startswith('VM_')}
    pose = {key: component_pose(x) for key,x in data['Idle'][0]['bones'].items()}
    skin = posed_points(mesh, groups, owners, reference, pose)
    shoulder, elbow, wrist = [pose[n].translation for n in ('Left-arm','Left-elbow','Left-wrist')]
    palm = pose['MiddleFinger1_L'].translation - wrist
    zero = np.zeros(6)

    def move(s):
        shift = Vector(s[:3]) / 1000.
        turn = Euler(tuple(math.radians(x) for x in s[3:])).to_quaternion()
        delta = Matrix.Translation(wrist+shift) @ turn.to_matrix().to_4x4() @ Matrix.Translation(-wrist)
        return delta, turn, shift

    def measure(s):
        delta,turn,shift=move(s)
        hit=fitted_elbow(shoulder, elbow, wrist, wrist+shift, turn@palm)
        if hit is None:
            return 1e6, {}
        new_bend=math.degrees(angle(wrist+shift-hit,turn@palm))
        distances={}
        for group,(moving,fixed) in skin.items():
            points=(moving @ np.array(delta).T)[:,:3] + fixed
            distances[group]=np.array([1000.*sdist(surface,Vector(p)) for p in points])
        all_dist=np.concatenate(list(distances.values()))
        buried=np.maximum(-all_dist-.10,0.)
        nearest=[abs(x).min() for x in distances.values()]
        pads=sorted(nearest[1:])[:3]
        gap=(max(nearest[0]-1.0,0.)**2+sum(max(n-1.6,0.)**2 for n in pads))
        penalty=4.0*(buried**2).sum()+36.0*buried.max(initial=0.)**2+1.6*gap
        penalty+=.065*max(new_bend-27.,0.)**2 + .0025*np.dot(s[:3],s[:3]) + .011*np.dot(s[3:],s[3:])
        return penalty,{'bend':round(new_bend,2),'max_penetration_mm':round(max(0.,-all_dist.min()),3),
                        'palm_clearance_mm':round(float(nearest[0]),3),'three_finger_clearance_mm':[round(float(p),3) for p in pads]}

    rng=np.random.default_rng(177)
    limits=np.array([25.,26.,25.,32.,34.,34.])
    candidates=[(measure(zero)[0],zero)]
    for _ in range(68):
        state=np.clip(rng.normal(0.,12.,len(zero)),-limits,limits)
        candidates.append((measure(state)[0],state))
    refined=[]
    for best,v in sorted(candidates,key=lambda row:row[0])[:4]:
        v=v.copy()
        for dist,ang in ((6.,10.),(3.,5.),(1.4,2.5),(.6,1.)):
            for _ in range(3):
                for dim in range(6):
                    center=v[dim]
                    chosen=center
                    for sign in (-1.,1.):
                        v[dim]=np.clip(center+sign*(dist if dim<3 else ang),-limits[dim],limits[dim])
                        score,_=measure(v)
                        if score<best:
                            best,chosen=score,v[dim]
                    v[dim]=chosen
        refined.append((best,v))
    _,chosen=min(refined,key=lambda row:row[0])
    _,turn,shift=move(chosen)
    q=(MIRROR @ turn.to_matrix().to_4x4() @ MIRROR).to_quaternion()
    result={'position':[shift.x*100.,-shift.y*100.,shift.z*100.], 'rotation':[q.x,q.y,q.z,q.w],
            'baseline_bend':round(math.degrees(angle(wrist-elbow,palm)),2),'before_surface_fit':measure(zero)[1],
            'after_surface_fit':measure(chosen)[1]}
    print('FIT',name,result,flush=True)
    return result


def main():
    data=json.loads((WORK/'poses.json').read_text())
    result={}
    for family in ('MP38','MP40'):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(WORK/f'{family}_mesh.fbx'))
        mesh=next(obj for obj in bpy.context.scene.objects if obj.type=='MESH')
        groups={g.index:g.name.replace(' ','-') for g in mesh.vertex_groups}
        owners=[dominant(v,groups) for v in mesh.data.vertices]
        result[family]=fit(family,mesh,groups,owners,data[family])
    (WORK/'SMGWristFit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()

