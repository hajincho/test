import json, sys
from PIL import Image, ImageDraw
tag=sys.argv[1]
d=json.load(open('lyra_pistol_grip_probe_%s.json'%tag))
b=d['bones']; fr=d['frame']; sl=d['slide']
fmin,fmax=fr['rifle_min'],fr['rifle_max']; smin,smax=sl['rifle_min'],sl['rifle_max']
print('frame',fmin,fmax,'slide',smin,smax)
chains={'R_idx':['IndexFinger1_R','IndexFinger3_R'],'R_mid':['MiddleFinger1_R','MiddleFinger3_R'],'R_ring':['RingFinger1_R','RingFinger3_R'],'R_lit':['LittleFinger1_R','LittleFinger3_R'],'R_th':['Thumb0_R','Thumb1_R','Thumb2_R'],
 'L_idx':['IndexFinger1_L','IndexFinger3_L'],'L_mid':['MiddleFinger1_L','MiddleFinger3_L'],'L_ring':['RingFinger1_L','RingFinger3_L'],'L_lit':['LittleFinger1_L','LittleFinger3_L'],'L_th':['Thumb0_L','Thumb1_L','Thumb2_L']}
S=22
def panel(i,j,xr,yr,title):
    W=int((xr[1]-xr[0])*S); H=int((yr[1]-yr[0])*S)
    im=Image.new('RGB',(W,H),'white'); dr=ImageDraw.Draw(im)
    px=lambda x:(x-xr[0])*S; py=lambda y:H-(y-yr[0])*S
    for g in range(int(xr[0]),int(xr[1])+1,2): dr.line([(px(g),0),(px(g),H)],fill=(225,225,225))
    for g in range(int(yr[0]),int(yr[1])+1,2): dr.line([(0,py(g)),(W,py(g))],fill=(225,225,225))
    dr.rectangle([px(fmin[i]),py(fmax[j]),px(fmax[i]),py(fmin[j])],outline='black',width=3)
    dr.rectangle([px(smin[i]),py(smax[j]),px(smax[i]),py(smin[j])],outline='gray',width=3)
    for nm,ch in chains.items():
        col=(220,40,40) if nm[0]=='R' else (40,60,220)
        pts=[(px(b[k][i]),py(b[k][j])) for k in ch]
        dr.line(pts,fill=col,width=4)
        for p in pts: dr.ellipse([p[0]-5,p[1]-5,p[0]+5,p[1]+5],fill=col)
    for w_,col in (('Right-wrist',(220,40,40)),('Left-wrist',(40,60,220))):
        p=(px(b[w_][i]),py(b[w_][j])); dr.rectangle([p[0]-8,p[1]-8,p[0]+8,p[1]+8],outline=col,width=3)
    dr.text((6,4),title,fill='black'); return im
a=panel(1,2,(-22,8),(-18,10),'side: x=Y fwd, y=Z up')
t=panel(0,1,(-10,6),(-22,8),'top: x=X left, y=Y fwd')
r=panel(0,2,(-10,6),(-18,10),'rear: x=X left, y=Z up')
H=max(a.size[1],t.size[1],r.size[1]); sheet=Image.new('RGB',(a.size[0]+t.size[0]+r.size[0]+20,H),'white')
x=0
for im in (a,t,r): sheet.paste(im,(x,0)); x+=im.size[0]+10
sheet.save('pistol_fit_plot_%s.png'%tag); print(sheet.size)
