"""50 m iron-sight zero for the measured M4 bore/sight geometry."""
import json,math,os
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'));path=os.path.join(D,'ballistics.json');B=json.load(open(path));FR=json.load(open(os.path.join(D,'fp_rig.json')));M=json.load(open(os.path.join(D,'m4_geometry.json')))
x,y,z,w=FR['poses']['ads_q'];v=M['muzzle'];u=(x,y,z);dot=sum(a*b for a,b in zip(u,v));cross=(y*v[2]-z*v[1],z*v[0]-x*v[2],x*v[1]-y*v[0]);r=[2*dot*u[i]+(w*w-sum(a*a for a in u))*v[i]+2*w*cross[i] for i in range(3)];offset=[a+b for a,b in zip(FR['poses']['ads'],r)];h=-offset[2]/100;start=offset[1]/100;zero=50.;rng=zero-start;V=B['muzzle_ms'];K=B['k_per_m']
def fly(angle,dist):
 xx=yy=tt=0.;vx=V*math.cos(angle);vy=V*math.sin(angle);dt=.0001
 while xx<dist:
  speed=math.hypot(vx,vy);vx-=K*speed*vx*dt;vy+=(-9.8-K*speed*vy)*dt;xx+=vx*dt;yy+=vy*dt;tt+=dt
 return yy,tt,math.hypot(vx,vy)
lo,hi=0,.01
for _ in range(38):
 mid=(lo+hi)/2
 if fly(mid,rng)[0]<0:lo=mid
 else:hi=mid
angle=(lo+hi)/2;B.update(zero_m=zero,zero_elev_rad=angle,zero_elev_deg=math.degrees(angle),sight_height_cm=h*100,muzzle_forward_cm=start*100,zero_note='Aim ray is always 50 m; muzzle-to-ray convergence supplies sight height, added elevation supplies drop compensation.')
B['table']=[]
for d in (10,25,50,75,100,150,200,300,400,500):
 yy,t,v=fly(angle+math.atan2(h,rng),d-start);B['table'].append(dict(m=d,impact_vs_sight_cm=round((yy-h)*100,2),tof_s=round(t,4),v_ms=round(v,1)))
B['recoil'].update(vertical_deg=.46,vertical_jitter=.12,horizontal_min_deg=-.18,horizontal_max_deg=.22,ads_gain=1.8,tp_gain=.3,reference='155 cm adult skilled-shooter gameplay tuning; age and sex do not uniquely determine physical recoil.')
json.dump(B,open(path,'w'),indent=1)
