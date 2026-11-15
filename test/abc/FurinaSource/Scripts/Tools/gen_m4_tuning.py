"""M4A1/.223 game tuning; preserve the user's existing base dispersion."""
import json,math,os
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'));p=os.path.join(D,'ballistics.json');B=json.load(open(p));B['rifle']='Colt M4A1 / supplied AR-15 visual';B['ammo']='.223 Remington 55 gr FMJ';B['magazine_capacity']=30;B['muzzle_ms']=910.;B['muzzle_cms']=91000;B['k_per_m']=math.log(988/920)/50;B['k_per_cm']=B['k_per_m']/100
B['velocity_note']='910 m/s gameplay estimate for 14.5-inch barrel; Hornady 988 m/s figure is from 24-inch test barrel.'
def fly(a,dist):
 x=y=t=0.;vx=910*math.cos(a);vy=910*math.sin(a);dt=.0002
 while x<dist:
  v=math.hypot(vx,vy);vx-=B['k_per_m']*v*vx*dt;vy+=(-9.81-B['k_per_m']*v*vy)*dt;x+=vx*dt;y+=vy*dt;t+=dt
 return y,t,math.hypot(vx,vy)
lo,hi=0,.01
for _ in range(36):
 mid=(lo+hi)/2
 if fly(mid,100)[0]<0:lo=mid
 else:hi=mid
B['zero_elev_rad']=(lo+hi)/2;B['zero_elev_deg']=math.degrees(B['zero_elev_rad']);B['table']=[]
for d in (25,50,100,150,200,250,300,400,500):
 y,t,v=fly(B['zero_elev_rad'],d);B['table'].append(dict(m=d,impact_cm=round(y*100,1),tof_s=round(t,3),v_ms=round(v)))
B['recoil'].update(vertical_deg=.45,horizontal_min_deg=-.2,horizontal_max_deg=.24,ads_gain=1.72,tp_gain=.3)
for k in ('impulse_ns','free_recoil_ms','energy_j','ratio_vs_m4','first_shot_rise_deg','ads_vertical_deg'):B['recoil'].pop(k,None)
B['recoil']['note']='Gameplay tuning for controlled recoil; not inferred from age, sex, or height.'
B['sources']=['https://static.hornady.media/presscenter/docs/2024-Hornady-International-Catalog-UK.pdf']
for k in ('check_sig_200yd_in','sig_published_200yd_in'):B.pop(k,None)
json.dump(B,open(p,'w'),indent=1)
FR=json.load(open(os.path.join(D,'fp_rig.json')));G=json.load(open(os.path.join(D,'m4_geometry.json')));q=FR['gun_q']
def qr(v):
 x,y,z,w=q;u=(x,y,z);dot=sum(a*b for a,b in zip(u,v));cross=(y*v[2]-z*v[1],z*v[0]-x*v[2],x*v[1]-y*v[0]);return [2*dot*u[i]+(w*w-sum(a*a for a in u))*v[i]+2*w*cross[i] for i in range(3)]
P=FR['poses'];butt=qr(G['stock_butt']);pocket=(-7.5,-8.3,-20);hip=[pocket[i]-butt[i] for i in range(3)];sh=[hip[0]-.5,hip[1],hip[2]+1.5];P['tp_hip_d']=[hip[i]-P['hip'][i] for i in range(3)];P['tp_sh_d']=[sh[i]-P['shoulder'][i] for i in range(3)];L=qr(FR['t_l']);back=0
while max(math.dist([g[i]+L[i]-(back if i==1 else 0) for i in range(3)],(10.25,-10.3,-21)) for g in (hip,sh))>37.8:back+=.5
P['tp_lback']=back;P['ads'][2]=-G['sight_z']-.288;FR['weapon']='M4A1';FR['muzzle_local']=G['muzzle'];FR['ejection_local']=G['case_port'];json.dump(FR,open(os.path.join(D,'fp_rig.json'),'w'),indent=1)
