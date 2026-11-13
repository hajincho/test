"""Engine regression for bounded, speed-proportional hair sway. Never saves assets."""
import unreal, os, json, math, traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={'cases':{},'checks':{}}
bp=unreal.load_asset('/Game/Furina/CR_FurinaSecondary')
c=bp.get_controller()
test_name='HairValidationSpeed_TEMP'
target='HairSpeedRatio.Value'
sources=[p.get_pin_path() for p in c.get_graph().find_pin(target).get_linked_source_pins()]
def key(n,typ=unreal.RigElementType.BONE):return unreal.RigElementKey(type=typ,name=n)
CHAINS=[['F_%d_1_%s'%(i,s) for i in range(18)] for s in ('L','R')]+[['CF_1_'+s,'CF_2_'+s] for s in ('L','R')]+[['DM_%d_1'%i for i in range(6)]]
TIPS=[a[-1] for a in CHAINS]
try:
    bp.set_auto_vm_recompile(False)
    for src in sources:c.break_link(src,target,False)
    assert c.add_unit_node_from_struct_path(unreal.RigUnit_GetCurveValue.static_struct().get_path_name(),'Execute',unreal.Vector2D(-550,-6200),test_name)
    assert c.set_pin_default_value(test_name+'.Curve','FurinaIdle',True,False)
    assert c.add_link(test_name+'.Value',target,False)
    bp.set_auto_vm_recompile(True);bp.recompile_vm()
    pose=unreal.load_asset('/Game/Furina/SK_Furina_Skeleton').get_reference_pose()
    mesh_rest={str(n):unreal.AnimPoseExtensions.get_bone_pose(pose,n,unreal.AnimPoseSpaces.LOCAL) for n in unreal.AnimPoseExtensions.get_bone_names(pose)}

    def simulate(label,fps,velocity,duration):
        rig=bp.create_control_rig();rig.set_delta_time(1/fps);rig.execute('Forwards Solve')
        h=rig.get_hierarchy()
        bones=[k for k in h.get_all_keys(True) if k.type==unreal.RigElementType.BONE]
        rest={str(k.name):mesh_rest.get(str(k.name),h.get_local_transform(k,True)) for k in bones}
        for k in bones:h.set_local_transform(k,rest[str(k.name)],False,True)
        head_ref=h.get_global_transform(key('Head'))
        reference={n:head_ref.inverse_transform_location(h.get_global_transform(key(n)).translation) for n in TIPS}
        rows=[];prev=None;max_step=0;max_length_error=0
        for i in range(int(duration*fps)):
            t=i/fps
            # Match AnimGraph input pose reset on each evaluation.
            for k in bones:h.set_local_transform(k,rest[str(k.name)],False,True)
            # Idle nodding must not turn into a false running-speed signal.
            hx=rest['Head'].copy()
            nod=unreal.Transform(rotation=unreal.Rotator(pitch=2*math.sin(t),yaw=2*math.sin(.6*t),roll=0)).rotation
            hx.set_editor_property('rotation',nod*hx.rotation)
            h.set_local_transform(key('Head'),hx,False,True)
            h.set_curve_value(key('FurinaIdle',unreal.RigElementType.CURVE),velocity(t))
            rig.set_absolute_and_delta_time(t,1/fps);assert rig.execute('Forwards Solve')
            head=h.get_global_transform(key('Head'))
            pts={n:list(head.inverse_transform_location(h.get_global_transform(key(n)).translation).to_tuple()) for n in TIPS}
            if prev:max_step=max(max_step,max(math.dist(pts[n],prev[n]) for n in TIPS))
            prev=pts
            for ch in CHAINS:
                for n in ch[1:]:
                    length=h.get_local_transform(key(n)).translation.length()
                    max_length_error=max(max_length_error,abs(length-rest[n].translation.length()))
            rows.append({'t':round(t,4),'speed':velocity(t),'flow':h.get_curve_value(key('HairFlow',unreal.RigElementType.CURVE)),**pts})
        steady=[r for r in rows if r['t']>=2]
        summary={'frames':len(rows),'fps':fps,'flow_range':[min(r['flow'] for r in rows),max(r['flow'] for r in rows)],'max_step_cm':max_step,'max_bone_length_error_cm':max_length_error,'tips':{}}
        for n in TIPS:
            mean=[sum(r[n][j] for r in steady)/len(steady) for j in range(3)]
            summary['tips'][n]={'sway_radius_cm':max(math.dist(r[n],mean) for r in steady),'max_rest_offset_cm':max(math.dist(r[n],reference[n].to_tuple()) for r in rows)}
        R['cases'][label]=summary
        if label=='transitions60':R['transition_samples']=rows[::3]
        return summary
    for label,speed in (('idle',0),('walk',120),('run',600)):
        simulate(label,60,lambda t,s=speed:s,9)
    schedule=lambda t:0 if t<1 or t>=7 else (120 if t<3 or t>=5 else 600)
    simulate('transitions60',60,schedule,10)
    simulate('transitions30',30,schedule,10)
    idle=R['cases']['idle'];run=R['cases']['run'];walk=R['cases']['walk']
    R['checks']['finite_bounded_flow']=all(0<=v['flow_range'][0] and v['flow_range'][1]<=1.00001 for v in R['cases'].values())
    R['checks']['no_stretch']=all(v['max_bone_length_error_cm']<.001 for v in R['cases'].values())
    R['checks']['quiet_idle']=all(idle['tips'][n]['sway_radius_cm']<(3 if n.startswith('F_') else 1) for n in TIPS)
    R['checks']['speed_proportional']=all(idle['tips'][n]['sway_radius_cm']<walk['tips'][n]['sway_radius_cm']<run['tips'][n]['sway_radius_cm'] for n in TIPS)
    R['checks']['gentle_running']=all(run['tips'][n]['sway_radius_cm']<(16 if n.startswith('F_') else 4) for n in TIPS)
    R['checks']['smooth_transitions']=R['cases']['transitions60']['max_step_cm']<1.5
    R['ok']=all(R['checks'].values())
except Exception:R['error']=traceback.format_exc()
finally:
    bp.set_auto_vm_recompile(False)
    for p in c.get_graph().find_pin(target).get_linked_source_pins():c.break_link(p.get_pin_path(),target,False)
    for src in sources:c.add_link(src,target,False)
    c.remove_node_by_name(test_name,False)
    bp.set_auto_vm_recompile(True);bp.recompile_vm()
with open(os.path.join(D,'soft_hair_validation.json'),'w',encoding='utf-8') as f:json.dump(R,f,indent=1,default=str)
print('SOFT_HAIR_VALIDATED',R.get('ok',False))
