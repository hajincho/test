"""Offline engine regression: moving blink, knee planes, and translation invariance."""
import unreal, os, json, math, traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={}
def key(name):return unreal.RigElementKey(type=unreal.RigElementType.BONE,name=name)
try:
    bp=unreal.load_asset('/Game/Furina/CR_FurinaSecondary')
    data=json.load(open(os.path.join(D,'ue_walk_tracks.json'),encoding='utf-8'))
    ref=json.load(open(os.path.join(D,'ue_ref.json'),encoding='utf-8'))
    names=['Hips','Left-leg','Left-knee','Left-ankle','Left-toe','Right-leg','Right-knee','Right-ankle','Right-toe']
    ids={n:data['bones'].index(n) for n in names}
    def run(offset):
        rig=bp.create_control_rig(); rig.set_delta_time(1/60); rig.execute('Forwards Solve')
        h=rig.get_hierarchy(); rows=[]; travel=offset; peak=0; windows=[]; was=False
        for frame in range(720):
            t=frame/60
            # walk -> sprint -> walk, repeated, including both transition directions.
            speed=120 if (int(t/2)%2==0) else 600
            travel+=speed/60
            k=int(frame/2)%data['frames']
            for n in names:
                p=list(data['hips'][k]) if n=='Hips' else list(ref[n]['p'])
                if n=='Hips':p[0]+=travel
                h.set_local_transform(key(n),unreal.Transform(location=unreal.Vector(*p),rotation=unreal.Quat(*data['rot'][k][ids[n]]).rotator()),False,True)
            h.set_curve_value(unreal.RigElementKey(type=unreal.RigElementType.CURVE,name='FurinaIdle'),0)
            rig.set_absolute_and_delta_time(t,1/60)
            assert rig.execute('Forwards Solve')
            blink=h.get_curve_value(unreal.RigElementKey(type=unreal.RigElementType.CURVE,name='IdleBlink'))
            peak=max(peak,blink)
            if blink>.05 and not was:windows.append(round(t,3))
            was=blink>.05
            row={'t':t,'speed':speed}
            for side,sg in (('Left',1),('Right',-1)):
                a=h.get_global_transform(key(side+'-leg')).translation
                b=h.get_global_transform(key(side+'-knee')).translation
                c=h.get_global_transform(key(side+'-ankle')).translation
                axis=c-a
                f=unreal.MathLibrary.dot_vector_vector(b-a,axis)/max(axis.length_squared(),1e-6)
                bend=b-(a+axis*f)
                row[side]={'p':[b.x-travel,b.y,b.z],'outward_cm':sg*bend.x,'forward_cm':bend.y,'thigh':(b-a).length(),'shin':(c-b).length()}
            rows.append(row)
        return {'peak_moving_blink':peak,'blink_starts':windows,'rows':rows}
    a=run(0);b=run(300)
    R['frames']=len(a['rows'])*2
    R['peak_moving_blink']=a['peak_moving_blink'];R['blink_starts']=a['blink_starts']
    R['position_invariance_error_cm']=max(abs(x[s]['p'][j]-y[s]['p'][j]) for x,y in zip(a['rows'][120:],b['rows'][120:]) for s in ('Left','Right') for j in range(3))
    R['min_outward_bend_cm']=min(x[s]['outward_cm'] for x in a['rows'][120:] for s in ('Left','Right'))
    R['min_forward_bend_cm']=min(x[s]['forward_cm'] for x in a['rows'][120:] for s in ('Left','Right'))
    R['bone_lengths']={k:[min(x[s][k] for x in a['rows']) ,max(x[s][k] for x in a['rows'])] for k in ('thigh','shin') for s in ('Left',)}
    R['samples']=a['rows'][::10]
    sk=unreal.load_asset('/Game/Furina/SK_Furina_Skeleton')
    R['blink_morph_flag']=unreal.AnimationLibrary.get_curve_meta_data_morph_target(sk,'IdleBlink')
except Exception:R['error']=traceback.format_exc()
with open(os.path.join(D,'character_fix_validation_latest.json'),'w',encoding='utf-8') as f:json.dump(R,f,ensure_ascii=False,indent=1,default=str)
