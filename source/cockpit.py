"""Measured, reference-led Legacy Hornet cockpit reconstruction for Solidcraft RC3.
Original procedural meshes only. OpenHornet dimensional envelopes and the public
Eagle Dynamics cockpit guide inform dimensions/layout; no third-party paths,
meshes, textures or electronics design are embedded. See COCKPIT_REFERENCE.md.
Metres: +X aft, +Y starboard, +Z above deck.
"""
from __future__ import annotations
import math
from collections import defaultdict
from scene_api import Mesh,box,cylinder,sphere,torus,tube,prism,text,add,sub,mul,cross,unit,lerp

DDI_W, DDI_H = .1635125, .1727200
AMPCD_W, AMPCD_H = .1670050, .1826228
UFC_W, UFC_H = .1730375, .1143000
UPPER_W, UPPER_H = .5359400, .2301875
CONSOLE_W = .1444625
REFERENCE_COMMIT = "77c7b2c07240d9d6062c16ed6e533bf2ed8bfce6"

class Batch:
    def __init__(self,scene,component,prefix):
        self.scene,self.component,self.prefix=scene,component,prefix
        self.parts=defaultdict(list);self.counts=defaultdict(int)
    def put(self,material,mesh,detail_count=1):
        if mesh.vertices and mesh.faces:
            self.parts[material].append(mesh);self.counts[material]+=detail_count
    def flush(self):
        for mat,meshes in self.parts.items():
            self.scene.add(self.component,self.prefix+" "+mat,mat,Mesh.merged(meshes),self.counts[mat])
        self.parts.clear();self.counts.clear()

class Plane:
    def __init__(self,origin,right=(0,1,0),up=(0,0,1)):
        self.o=origin;self.u=unit(right);self.v=unit(up);self.n=unit(cross(self.u,self.v))
    def p(self,u=0,v=0,n=0):
        return add(self.o,add(mul(self.u,u),add(mul(self.v,v),mul(self.n,n))))
    def moved(self,u=0,v=0,n=0):
        return Plane(self.p(u,v,n),self.u,self.v)

def front_plane(x,y,z,tilt=12):
    a=math.radians(tilt);return Plane((x,y,z),(0,1,0),(-math.sin(a),0,math.cos(a)))

def rr_loop(w,h,r,steps=6):
    r=min(r,w*.49,h*.49);out=[]
    for cx,cy,a0 in ((w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)):
        for k in range(steps+1):
            a=math.radians(a0+k*90/steps);out.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return out

def plate(p,w,h,t=.004,r=.003,u=0,v=0,n=0):
    return prism([p.p(u+a,v+b,n) for a,b in rr_loop(w,h,r)],mul(p.n,-t))

def ring(p,w,h,iw,ih,t=.014,r=.011,ir=.004,n=.004):
    outer=rr_loop(w,h,r);inner=rr_loop(iw,ih,ir);count=len(outer);meshes=[]
    def quad(a,b,c,d):
        return Mesh([a,b,c,d],[(0,1,2),(0,2,3)],False)
    for i in range(count):
        j=(i+1)%count
        a,b=p.p(*outer[i],n),p.p(*outer[j],n)
        c,d=p.p(*inner[j],n),p.p(*inner[i],n)
        ab,bb=p.p(*outer[i],n-t),p.p(*outer[j],n-t)
        cb,db=p.p(*inner[j],n-t),p.p(*inner[i],n-t)
        meshes.extend((quad(a,b,c,d),quad(bb,ab,db,cb),quad(ab,bb,b,a),quad(d,c,cb,db)))
    return Mesh.merged(meshes)

def label(batch,p,value,u,v,height=.0035,n=.0012,material="label_white",center=False):
    if center:u-=len(value)*height*.43
    batch.put(material,text(value,p.p(u,v,n),height,right=p.u,up=p.v,depth=.00012))

def line(batch,p,points,material="label_white",radius=.00022,n=.0013):
    batch.put(material,tube([p.p(u,v,n) for u,v in points],radius,5))

def screw(batch,p,u,v,r=.0028,n=.0006):
    batch.put("metal",cylinder(p.p(u,v,n),p.p(u,v,n+.0012),r,16))
    line(batch,p,[(u-r*.62,v),(u+r*.62,v)],"black",r*.13,n+.0016)

def panel(scene,name,p,w,h,thickness=.0032,title=True):
    comp="Panel "+name;b=Batch(scene,comp,name)
    b.put("panel_black",plate(p,w,h,thickness,.004))
    b.put("cockpit_gray",ring(p,w+.0025,h+.0025,w-.002,h-.002,.0017,.004,.003,n=-.001))
    for u in (-w/2+.006,w/2-.006):
        for v in (-h/2+.006,h/2-.006):screw(b,p,u,v,r=.0023)
    if title:label(b,p,name,0,h/2-.008,.0031,center=True)
    scene.fixed("Mount "+name,"Cockpit fixed",comp)
    return b

def moving(scene,name,parent,origin,axis,limits,kind="revolute",default=0):
    comp="Control "+name
    scene.joint(name,parent,comp,origin,axis,limits,default,kind)
    return Batch(scene,comp,name)

def push(scene,b,p,name,u,v,w=.011,h=.011,caption=None,round_button=False,travel=.0025,n=.006):
    origin=p.p(u,v,.002)
    q=moving(scene,name,b.component,origin,mul(p.n,-1),(0,travel),"slider")
    if round_button:
        b.put("cockpit_gray",torus(origin,.008,.0017,axis=p.n,segments=24,sides=7))
        q.put("button_gray",cylinder(origin,p.p(u,v,n+.0005),w/2,20))
    else:
        b.put("black",plate(p,w+.002,h+.002,.002,.002,u,v,.001))
        q.put("button_gray",plate(p,w,h,.004,.0012,u,v,n))
    if caption:label(q,p,caption,u,v-.0015,min(.0031,w/max(1,len(caption))*.92),n=n+.0002,center=True)
    q.flush()
    return name

def knob(scene,b,p,name,u,v,r=.0075,caption=None,limits=(-135,135),color="button_gray"):
    origin=p.p(u,v,.003)
    b.put("black",cylinder(p.p(u,v,.0003),origin,r*1.16,24))
    q=moving(scene,name,b.component,origin,p.n,limits)
    q.put(color,cylinder(origin,p.p(u,v,.017),r,32))
    q.put(color,cylinder(p.p(u,v,.017),p.p(u,v,.020),r*.90,32))
    for i in range(16):
        a=i*math.tau/16;du,dv=math.cos(a)*r,math.sin(a)*r
        q.put("black",tube([p.p(u+du,v+dv,.006),p.p(u+du,v+dv,.017)],.00048,5))
    line(q,p,[(u,v+.002),(u,v+r*.70)],"label_white",.00065,n=.0204)
    if caption:label(b,p,caption,u,v-r-.007,.003,center=True)
    q.flush();return name

def toggle(scene,b,p,name,u,v,caption=None,limits=(-23,23),guard=False,color="metal"):
    origin=p.p(u,v,.005)
    b.put("metal",cylinder(p.p(u,v,.0005),origin,.0045,6))
    b.put("black",torus(p.p(u,v,.005),.0038,.001,axis=p.n,segments=16,sides=6))
    q=moving(scene,name,b.component,origin,p.u,limits)
    tip=p.p(u,v,.023)
    q.put(color,cylinder(origin,tip,.0017,14,.0022))
    q.put("button_gray",sphere(tip,.0032,16,8));q.flush()
    if caption:label(b,p,caption,u,v+.010,.003,center=True)
    if guard:
        g=moving(scene,name+" guard",b.component,p.p(u,v-.008,.002),p.u,(0,110))
        g.put("red",plate(p,.015,.027,.002,.002,u,v+.002,.026))
        g.put("red",tube([p.p(u-.006,v-.008,.003),p.p(u-.006,v-.008,.025),
                           p.p(u+.006,v-.008,.025),p.p(u+.006,v-.008,.003)],.0013,7))
        g.flush()
    return name

def dial(b,p,name,u,v,r=.026,needle=.8,material="instrument_glass",ticks=36):
    b.put("cockpit_gray",cylinder(p.p(u,v,-.035),p.p(u,v,.002),r+ .003,40))
    b.put("metal",torus(p.p(u,v,.002),r,.0016,axis=p.n,segments=40,sides=7))
    b.put(material,cylinder(p.p(u,v,.002),p.p(u,v,.003),r-.002,40))
    for j in range(ticks):
        a=j*math.tau/ticks;ri=r*(.72 if j%3==0 else .81);ro=r*.89
        line(b,p,[(u+ri*math.sin(a),v+ri*math.cos(a)),(u+ro*math.sin(a),v+ro*math.cos(a))],
             "label_white",.00035,n=.0036)
    for j in range(0,ticks,6):
        a=j*math.tau/ticks;label(b,p,str(j//3),u+r*.57*math.sin(a),v+r*.57*math.cos(a)-.0017,.0027,n=.0037,center=True)
    q=moving(b.scene,b.component+" "+name+" indicator",b.component,p.p(u,v,.004),p.n,(-180,180))
    line(q,p,[(u,v),(u+r*.72*math.sin(needle),v+r*.72*math.cos(needle))],"label_white",.00085,n=.004)
    q.put("metal",cylinder(p.p(u,v,.0038),p.p(u,v,.005),.0022,14));q.flush()
    label(b,p,name,u,v-r*.40,.0027,n=.0042,center=True)

def connector(b,p,u,v,r=.010,pins=7):
    b.put("metal",cylinder(p.p(u,v,0),p.p(u,v,.016),r,24))
    b.put("connector_blue",torus(p.p(u,v,.011),r*.94,.0022,axis=p.n,segments=24,sides=7))
    b.put("black",cylinder(p.p(u,v,.016),p.p(u,v,.018),r*.75,20))
    for j in range(pins):
        a=j*math.tau/pins
        b.put("metal",cylinder(p.p(u+r*.43*math.sin(a),v+r*.43*math.cos(a),.018),
                               p.p(u+r*.43*math.sin(a),v+r*.43*math.cos(a),.021),.00075,8))

def electronics(scene,parent,name,p,w,h,depth=.16):
    comp=name+" electronics";b=Batch(scene,comp,name+" casing")
    # Open-sided rail enclosure with rear connector face, fasteners and cooling fins.
    back=p.moved(0,0,-depth)
    b.put("aluminum",plate(back,w*.88,h*.90,.002,.004))
    for uu in (-w*.44,w*.44):
        b.put("aluminum",prism([p.p(uu,-h*.45,-.009),p.p(uu,h*.45,-.009),
                                 p.p(uu,h*.45,-depth),p.p(uu,-h*.45,-depth)],mul(p.u,.002)))
    for i in range(10):
        y=-w*.37+i*w*.074
        b.put("metal",tube([p.p(y,-h*.43,-.015),p.p(y,-h*.43,-depth+.01)],.0014,7))
    pcb=p.moved(0,0,-depth*.53)
    b.put("pcb_green",plate(pcb,w*.80,h*.78,.0018,.002))
    for k in range(8):
        uu=(-.25+(k%4)*.17)*w;vv=(-.22+(k//4)*.34)*h
        b.put("black",plate(pcb,w*.10,h*.13,.005,.001,uu,vv,.004))
        for j in range(4):
            b.put("metal",tube([pcb.p(uu-w*.055,vv-h*.05+j*h*.03,.003),
                                pcb.p(uu-w*.071,vv-h*.05+j*h*.03,.003)],.00055,6))
    rear=Plane(back.o,mul(p.u,-1),p.v)
    for j in range(3):
        u=(j-1)*w*.23;connector(b,rear,u,-h*.14,r=.010)
        start=rear.p(u,-h*.14,.024)
        route=[start,add(start,(-.035,0,-.045)),(4.43,start[1],2.48),(4.40,start[1]*1.3,2.25)]
        b.put("black",tube(route,.0055,10))
        for f in (.25,.5,.75):
            q=lerp(route[1],route[-1],f)
            b.put("cream",torus(q,.0059,.00085,axis=sub(route[-1],route[1]),segments=14,sides=5))
    label(b,rear,name+" UNIT",0,h*.24,.004,center=True)
    b.flush();scene.fixed("Install "+comp,parent,comp)

def capsule(a,b,r1,r2=None,segments=20):
    if r2 is None:r2=r1
    return Mesh.merged([cylinder(a,b,r1,segments,r2),sphere(a,r1,segments,10),sphere(b,r2,segments,10)])

def webbing(points,width=.035,thickness=.003):
    out=[]
    for a,b in zip(points,points[1:]):
        d=(0,width/2,0)
        out.append(prism([sub(a,d),add(a,d),add(b,d),sub(b,d)],(-thickness,0,0)))
    return Mesh.merged(out)

def ellipsoid_patch(center,radii,h_range=(-65,65),v_range=(-8,47),nh=32,nv=14):
    vs=[];fs=[]
    for j in range(nv+1):
        v=math.radians(v_range[0]+(v_range[1]-v_range[0])*j/nv)
        for i in range(nh+1):
            h=math.radians(h_range[0]+(h_range[1]-h_range[0])*i/nh)
            vs.append(add(center,(-radii[0]*math.cos(v)*math.cos(h),radii[1]*math.cos(v)*math.sin(h),radii[2]*math.sin(v))))
    for j in range(nv):
        for i in range(nh):
            a=j*(nh+1)+i;b,c,d=a+1,a+nh+2,a+nh+1;fs.extend([(a,c,b),(a,d,c)])
    return Mesh(vs,fs)

def ddi(scene,name,p,ampcd=False,page="FCS"):
    w,h=(AMPCD_W,AMPCD_H) if ampcd else (DDI_W,DDI_H)
    b=panel(scene,name,p,w,h,title=False)
    iw=.127;ih=.127
    b.put("button_gray",ring(p,w,h,iw,ih,.018,.012,.007,n=.010))
    b.put("display_dark",plate(p.moved(0,.004,.009),iw-.002,ih-.002,.002,.006))
    # Twenty pushbuttons numbered from the lower left clockwise, per DCS guide.
    for edge in range(4):
        for k in range(5):
            if edge==0:u,v=-w/2+.006,-.044+k*.022
            elif edge==1:u,v=-.044+k*.022,h/2-.015
            elif edge==2:u,v=w/2-.006,.044-k*.022
            else:u,v=.044-k*.022,-h/2+.016
            push(scene,b,p,name+" PB "+str(edge*5+k+1).zfill(2),u,v,
                 w=.008 if edge in (0,2) else .010,h=.010 if edge in(0,2) else .007,n=.014)
            if k<4:
                gu,gv=u,v
                if edge==0:gv+=.011
                elif edge==1:gu+=.011
                elif edge==2:gv-=.011
                else:gu-=.011
                b.put("cockpit_gray",plate(p,.012 if edge in(0,2) else .0018,
                                           .0018 if edge in(0,2) else .012,.006,.0008,gu,gv,.012))
    for su in (-1,1):
        for sv in (-1,1):screw(b,p,su*(w/2-.0045),sv*(h/2-.0045),r=.0018,n=.0103)
    if ampcd:
        for u,v,cap in ((-.067,.076,"DAY"),(.067,.076,"NGT"),(-.067,-.078,"GAIN"),(.067,-.078,"SYM")):
            push(scene,b,p,name+" "+cap+" rocker",u,v,w=.008,h=.012,caption=None,n=.014)
            label(b,p,cap,u,v-.011,.0025,n=.011,center=True)
        knob(scene,b,p,name+" brightness",-.061,-.045,r=.0055)
        label(b,p,"OFF",-.061,-.056,.0025,n=.011,center=True)
    else:
        knob(scene,b,p,name+" mode selector",-.066,h/2-.009,r=.0060,limits=(-45,45))
        knob(scene,b,p,name+" brightness",-.066,-h/2+.010,r=.0063)
        knob(scene,b,p,name+" contrast",.066,-h/2+.010,r=.0063)
        label(b,p,"BRT",-.066,-h/2+.020,.0023,n=.011,center=True)
        label(b,p,"CONT",.066,-h/2+.020,.0023,n=.011,center=True)
        label(b,p,"OFF NIGHT DAY",-.032,h/2-.004,.0023,n=.011)
    sp=p.moved(0,.004,.011)
    if page=="FCS":
        label(b,sp,"FCS",0,.049,.004,center=True,material="display_green")
        for row,(lab,val) in enumerate((("AIL","30"),("RUD","0"),("FLP","30"),("LEF","12"),("STAB","16"))):
            vv=.025-row*.013
            label(b,sp,lab,0,vv,.0032,center=True,material="display_green")
            label(b,sp,val,-.044,vv,.0035,center=True,material="display_green")
            label(b,sp,val,.044,vv,.0035,center=True,material="display_green")
        line(b,sp,[(-.018,.037),(0,.045),(.018,.037)],"display_green",.00045)
        for side in(-1,1):
            line(b,sp,[(side*.052,-.05),(side*.052,.047)],"display_green",.00025)
        label(b,sp,"BIT",-.046,-.054,.0028,material="display_green")
        label(b,sp,"MENU",0,-.054,.0028,center=True,material="display_green")
    elif page=="HUD":
        for z in(-.030,-.015,0,.015,.030):
            line(b,sp,[(-.026,z),(-.008,z)],"display_green",.00032)
            line(b,sp,[(.008,z),(.026,z)],"display_green",.00032)
        line(b,sp,[(-.012,-.003),(0,.003),(.012,-.003)],"display_green",.0004)
        for u,cap in ((-.047,"000"),(.047,"000")):
            label(b,sp,cap,u,.022,.004,center=True,material="display_green")
        label(b,sp,"090",0,.047,.004,center=True,material="display_green")
        label(b,sp,"W 0.0",-.043,-.044,.0033,material="display_green")
        label(b,sp,"HUD",0,-.054,.003,center=True,material="display_green")
    else:
        b.put("display_green",torus(sp.p(0,0,.001),.041,.00045,axis=sp.n,segments=72,sides=5))
        for k in range(36):
            a=k*math.tau/36
            line(b,sp,[(.037*math.sin(a),.037*math.cos(a)),(.041*math.sin(a),.041*math.cos(a))],
                 "display_green",.00035)
        for i,cap in enumerate(("N","E","S","W")):
            a=i*math.pi/2;label(b,sp,cap,.049*math.sin(a),.049*math.cos(a)-.002,.004,center=True,material="display_green")
        line(b,sp,[(0,-.018),(0,.018),(-.005,.010),(0,.018),(.005,.010)],"display_green",.0005)
        label(b,sp,"HSI",0,-.054,.003,center=True,material="display_green")
        label(b,sp,"TCN",-.046,.048,.0027,material="display_green")
    b.flush();electronics(scene,b.component,name,p,w,h,.175 if not ampcd else .125)

def ufc(scene):
    p=front_plane(4.747,0,2.893)
    b=panel(scene,"UFC",p,UFC_W,UFC_H,title=False)
    # Correct five option windows, five selectors, scratchpad and 3 x 4 keypad.
    b.put("black",plate(p,.100,.016,.003,.0015,-.028,.047,.003))
    b.put("display_dark",plate(p,.094,.011,.001,.001,-.028,.047,.004))
    label(b,p,"1  305.000",-.070,.044,.004,n=.005,material="display_green")
    for row,values in enumerate((("1","2","3"),("4","5","6"),("7","8","9"),("CLR","0","ENT"))):
        for col,val in enumerate(values):
            u=-.048+col*.021;v=.024-row*.019
            push(scene,b,p,"UFC keypad "+val,u,v,w=.016,h=.014,caption=val)
            if row<3:
                letter=(("A","N","B"),("W"," ","E"),("C","S","D"))[row][col]
                if letter.strip():label(b,p,letter,u,v+.005,.0021,n=.0063,center=True)
    for k,value in enumerate(("GRCV","SQCH","CPHR","RAM","MENU")):
        v=.038-k*.020
        push(scene,b,p,"UFC option "+str(k+1),.014,v,w=.0095,round_button=True)
        b.put("black",plate(p,.047,.015,.002,.001,.045,v,.002))
        b.put("display_dark",plate(p,.043,.011,.001,.0005,.045,v,.003))
        label(b,p,value,.045,v-.002,.0034,n=.004,material="display_green",center=True)
    toggle(scene,b,p,"UFC ADF selector",-.075,.024,caption="ADF")
    knob(scene,b,p,"UFC COMM1 volume",-.075,-.022,r=.0057,caption="VOL")
    knob(scene,b,p,"UFC COMM2 volume",.075,-.022,r=.0057,caption="VOL")
    knob(scene,b,p,"UFC brightness",.075,.025,r=.0055,caption="BRT")
    push(scene,b,p,"UFC EMCON",.075,.001,w=.011,h=.012,caption="EM")
    for u,cap in ((-.075,"1"),(.075,"2")):
        b.put("display_dark",plate(p,.016,.014,.001,.001,u,-.046,.003))
        label(b,p,"1",u,-.050,.007,n=.004,center=True,material="display_green")
        knob(scene,b,p,"UFC COMM"+cap+" channel",u,-.071,r=.008,limits=(-180,180))
    for i,cap in enumerate(("A/P","IFF","TCN","ILS","D/L","BCN","ON")):
        push(scene,b,p,"UFC function "+cap,-.054+i*.018,-.071,w=.015,h=.012,caption=cap)
    # Separate function strip and HUD-controls mounting fascia.
    b.put("panel_black",plate(p,.173,.032,.005,.003,0,-.072,-.002))
    b.flush();electronics(scene,b.component,"UFC",p,UFC_W,UFC_H,.115)
    h=front_plane(4.774,0,2.765)
    q=panel(scene,"HUD CONTROL",h,.173,.060,title=False)
    for u,v,cap in ((-.048,.010,"HUD BRT"),(.004,.010,"BLK LVL"),(.056,.010,"BAL"),(-.026,-.015,"AOA")):
        knob(scene,q,h,"HUD "+cap,u,v,r=.0065,caption=cap)
    toggle(scene,q,h,"HUD reject selector",-.073,.008,caption="REJ")
    toggle(scene,q,h,"HUD day night selector",-.021,.017,caption="DAY")
    toggle(scene,q,h,"HUD altitude source",.033,-.015,caption="ALT")
    toggle(scene,q,h,"HUD attitude source",.067,-.015,caption="ATT")
    q.flush()

def ifei(scene):
    p=front_plane(4.813,-.185,2.636,17)
    b=panel(scene,"IFEI",p,.166,.111,title=False)
    b.put("display_dark",plate(p,.148,.089,.002,.002,0,.002,.002))
    for i,(cap,l,r) in enumerate((("RPM","98","98"),("TEMP","720","720"),("FF","61","61"),("NOZ","10","10"),("OIL","110","110"))):
        v=.032-i*.015
        label(b,p,cap,-.015,v,.0032,n=.0035,center=True)
        label(b,p,l,-.048,v,.006,n=.0035,center=True)
        label(b,p,r,.017,v,.006,n=.0035,center=True)
    for v,val in ((.031,"10800 T"),(.014,"10800 I"),(-.004,"2500 B"),(-.025,"12:00")):
        label(b,p,val,.052,v,.0042,n=.0035,center=True)
    for i,cap in enumerate(("MODE","QTY","UP","DN","ZONE","ET")):
        push(scene,b,p,"IFEI "+cap,-.052+i*.021,-.048,w=.013,h=.007,caption=cap)
    knob(scene,b,p,"IFEI brightness",-.073,-.044,r=.005)
    b.flush();electronics(scene,b.component,"IFEI",p,.166,.111,.105)

def standby_group(scene):
    p=front_plane(4.814,.192,2.632,17)
    b=panel(scene,"STANDBY FLIGHT",p,.181,.146,title=False)
    dial(b,p,"SARI",-.040,.030,.029,needle=0,ticks=24)
    b.put("cockpit_gray",plate(p,.070,.068,.010,.008,.040,.030,.002))
    b.put("display_dark",cylinder(p.p(.040,.030,.003),p.p(.040,.030,.005),.028,40))
    for rad in (.010,.020,.027):
        b.put("display_green",torus(p.p(.040,.030,.0055),rad,.0004,axis=p.n,segments=48,sides=5))
    line(b,p,[(.015,.03),(.065,.03)],"display_green",.0003,n=.006)
    line(b,p,[(.04,.005),(.04,.055)],"display_green",.0003,n=.006)
    label(b,p,"RWR",.040,.013,.003,n=.006,center=True,material="display_green")
    for u,cap,angle in ((-.057,"KNOTS",-.7),(0,"ALT",.0),(.057,"VVI",1.57)):
        dial(b,p,cap,u,-.042,.023,needle=angle,ticks=30)
    b.flush()
    for name,yy in (("SARI",.152),("RWR",.232)):
        electronics(scene,b.component,name,front_plane(4.81,yy,2.662,17),.066,.068,.105)

def upper_warnings(scene):
    for side in(-1,1):
        name="LEFT EYEBROW" if side<0 else "RIGHT EYEBROW"
        p=front_plane(4.728,side*.184,2.982,10)
        b=panel(scene,name,p,.160,.050,title=False)
        caps=(("L BLEED","R BLEED","SPD BRK","STBY","L BAR","REC","XMIT","GO","NO GO")
              if side<0 else ("APU FIRE","R FIRE","READY","DISCH","LOCK","SHOOT","CK SEAT","FUEL LO","GEN TIE"))
        for k,cap in enumerate(caps):
            u=-.054+(k%3)*.054;v=.013-(k//3)*.014
            b.put("black",plate(p,.050,.011,.003,.001,u,v,.002))
            label(b,p,cap,u,v-.0015,.0024,n=.003,center=True,material="warning_dim")
        if side<0:
            push(scene,b,p,"Master caution reset",-.060,.036,w=.045,h=.015,caption="CAUTION")
            push(scene,b,p,"Left engine fire",.005,.036,w=.035,h=.015,caption="L FIRE")
        else:
            push(scene,b,p,"Right engine fire",.005,.036,w=.035,h=.015,caption="R FIRE")
            push(scene,b,p,"APU fire",.055,.036,w=.035,h=.015,caption="APU")
        b.flush()

def instrument_panel(scene):
    fixed=Batch(scene,"Cockpit fixed","Instrument support")
    p=front_plane(4.735,0,2.837)
    # Rail-and-web mounting face with genuine openings behind the three modules.
    # The bounding dimensions are reference facts; these clearance cutouts are authored.
    holes=[(-.1855,.023,DDI_W*.94,DDI_H*.96),
           (.1855,.023,DDI_W*.94,DDI_H*.96),(0,.003,.164,.208)]
    us=sorted(set([-UPPER_W/2,UPPER_W/2]+[a+sign*w/2 for a,v,w,h in holes for sign in(-1,1)]))
    vs=sorted(set([-UPPER_H/2,UPPER_H/2]+[v+sign*h/2 for a,v,w,h in holes for sign in(-1,1)]))
    for u0,u1 in zip(us,us[1:]):
        for v0,v1 in zip(vs,vs[1:]):
            uc,vc=(u0+u1)/2,(v0+v1)/2
            if any(abs(uc-a)<w/2 and abs(vc-v)<h/2 for a,v,w,h in holes):continue
            fixed.put("cockpit_gray",prism([p.p(u0,v0),p.p(u1,v0),p.p(u1,v1),p.p(u0,v1)],mul(p.n,-.012)))
    # Actual narrow core plus outboard cheek panels, not the previous wide wall.
    for side in(-1,1):
        pp=front_plane(4.755,side*.315,2.823,15)
        fixed.put("cockpit_gray",plate(pp,.094,.222,.010,.015))
    for y in(-.278,0,.278):
        fixed.put("metal",tube([(4.43,y,2.20),(4.49,y,2.54),(4.66,y,2.75),(4.71,y,2.97)],.010,12))
    # Sculpted glare-shield lip follows three separate instrument groups.
    for side in(-1,1):
        fixed.put("black",tube([(4.66,side*.365,2.91),(4.64,side*.298,3.01),
                                 (4.61,side*.180,3.055),(4.60,side*.100,3.057)],.018,20))
    fixed.put("black",box((4.59,0,3.057),(.24,.19,.040)))
    fixed.flush()
    ddi(scene,"LEFT DDI",front_plane(4.752,-.1855,2.864),page="FCS")
    ddi(scene,"RIGHT DDI",front_plane(4.752,.1855,2.864),page="HUD")
    ufc(scene);ifei(scene);standby_group(scene);upper_warnings(scene)
    ddi(scene,"AMPCD",front_plane(4.914,0,2.554,23),ampcd=True,page="HSI")
    p=front_plane(4.879,0,2.672,20);b=panel(scene,"HDG CRS",p,.173,.035,title=False)
    toggle(scene,b,p,"Heading set",-.069,0,caption="HDG")
    toggle(scene,b,p,"Course set",.069,0,caption="CRS")
    knob(scene,b,p,"AMPCD display mode",0,0,r=.0055,caption="DAY NGT")
    b.flush()

def guarded_push(scene,b,p,name,u,v,r=.012):
    q=moving(scene,name,b.component,p.p(u,v,.005),mul(p.n,-1),(0,.004),"slider")
    b.put("yellow",torus(p.p(u,v,.005),r+.004,.003,axis=p.n,segments=40,sides=7))
    for k in range(8):
        a=k*math.tau/8
        line(b,p,[(u+(r+.002)*math.cos(a),v+(r+.002)*math.sin(a)),
                   (u+(r+.006)*math.cos(a),v+(r+.006)*math.sin(a))],
             "black",.0014,n=.006)
    q.put("black",cylinder(p.p(u,v,.003),p.p(u,v,.009),r,28))
    label(q,p,"JETT",u,v-.0025,.004,n=.0095,center=True);q.flush()

def main_side_panels(scene):
    p=front_plane(4.777,-.325,2.845,15);b=panel(scene,"MASTER ARM",p,.087,.181,title=False)
    push(scene,b,p,"Air to air master mode",-.019,.063,w=.029,h=.016,caption="A/A")
    push(scene,b,p,"Air to ground master mode",.019,.063,w=.029,h=.016,caption="A/G")
    toggle(scene,b,p,"Master arm selector",0,.027,caption="MASTER ARM",limits=(-25,25))
    label(b,p,"ARM",.018,.030,.003);label(b,p,"SAFE",.018,.011,.003)
    guarded_push(scene,b,p,"Emergency jettison button",0,-.036)
    label(b,p,"EMERG JETT",0,-.062,.003,center=True)
    b.flush()
    p=front_plane(4.777,.326,2.846,15);b=panel(scene,"SPIN HMD",p,.086,.181,title=False)
    knob(scene,b,p,"HMD brightness",0,.049,r=.008,caption="HMD")
    toggle(scene,b,p,"IR cooling",0,.015,caption="IR COOL")
    toggle(scene,b,p,"Spin recovery",0,-.031,caption="SPIN",guard=True)
    label(b,p,"RCVY",0,-.062,.003,center=True);b.flush()
    # Forward sloping cheek panels sit beside the pilot's knees.
    p=front_plane(4.910,-.329,2.605,32);b=panel(scene,"SELECT JETT GEAR",p,.1651,.1326404,title=False)
    for i,cap in enumerate(("LO","LI","CTR","RI","RO")):
        push(scene,b,p,"Jettison station "+cap,-.060+i*.030,.044,w=.023,h=.014,caption=cap)
    for u,cap in ((-.050,"LEFT"),(0,"NOSE"),(.050,"RIGHT")):
        b.put("indicator_green",plate(p,.024,.009,.002,.001,u,.019,.003))
        label(b,p,cap,u,.018,.0027,n=.0033,center=True)
    knob(scene,b,p,"Selective jettison selector",-.042,-.030,r=.013,caption="SEL JETT",limits=(-90,90))
    push(scene,b,p,"Selective jettison press",-.042,-.030,w=.010,round_button=True)
    for v,cap in ((-.014,"HALF"),(-.033,"FULL"),(-.052,"FLAPS")):
        b.put("indicator_green" if cap=="HALF" else "warning_dim",plate(p,.026,.011,.002,.001,.046,v,.003))
        label(b,p,cap,.046,v-.0015,.0027,n=.0033,center=True)
    b.flush()
    p=front_plane(5.018,-.330,2.456,38);b=panel(scene,"LANDING GEAR",p,.08810625,.06429375,title=False)
    toggle(scene,b,p,"Flap selector cockpit handle motion",-.029,.008,caption="FLAP",limits=(-25,25))
    toggle(scene,b,p,"Anti skid",.030,.008,caption="ANTI SKID")
    toggle(scene,b,p,"Hook bypass",.030,-.016,caption="FIELD")
    pivot=p.p(0,-.003,.016);end=p.p(0,-.050,.040)
    q=moving(scene,"Landing gear cockpit handle motion",b.component,pivot,p.u,(-55,15))
    q.put("metal",cylinder(pivot,end,.0045,18))
    q.put("white",torus(end,.017,.006,axis=p.u,segments=32,sides=9))
    q.put("white",cylinder(sub(end,mul(p.u,.005)),add(end,mul(p.u,.005)),.009,20))
    q.flush();b.flush()
    p=front_plane(5.04,-.312,2.348,25);b=panel(scene,"BRAKE ACCUM",p,.115,.083,title=False)
    dial(b,p,"BRAKE PSI",.027,0,.024,needle=.8)
    q=moving(scene,"Parking brake pull",b.component,p.p(-.035,0,.010),p.n,(0,.035),"slider")
    q.put("black",plate(p,.033,.017,.011,.003,-.035,0,.023))
    label(q,p,"PARK",-.035,-.0025,.004,n=.0233,center=True);q.flush();b.flush()
    p=front_plane(4.970,.332,2.554,32);b=panel(scene,"HOOK HYDRAULIC",p,.142,.219,title=False)
    pivot=p.p(-.036,.067,.008);end=p.p(-.036,.105,.040)
    q=moving(scene,"Arresting hook cockpit handle motion",b.component,pivot,p.u,(-50,10))
    q.put("metal",cylinder(pivot,end,.005,18))
    q.put("white",plate(Plane(end,p.u,p.v),.035,.017,.015,.004,n=.004));q.flush()
    label(b,p,"HOOK",- .036,.043,.003,center=True)
    b.put("warning_dim",plate(p,.015,.010,.003,.001,-.036,.024,.003))
    dial(b,p,"RAD ALT",.020,.030,.027,needle=-.6)
    dial(b,p,"HYD",.016,-.046,.028,needle=.8)
    toggle(scene,b,p,"Avionics cooling",- .042,-.065,caption="AV COOL")
    b.flush()
    p=Plane((5.058,.417,2.620),(1,0,0),(0,0,1))
    b=panel(scene,"WING FOLD",p,.080,.070,title=False)
    pivot=p.p(0,0,.004)
    q=moving(scene,"Wing fold cockpit handle motion",b.component,pivot,p.n,(-90,90))
    end=p.p(0,.027,.028);q.put("metal",cylinder(pivot,end,.005,16))
    q.put("yellow",cylinder(sub(end,mul(p.u,.020)),add(end,mul(p.u,.020)),.007,18))
    q.put("black",cylinder(sub(end,mul(p.u,.004)),add(end,mul(p.u,.004)),.0074,18));q.flush()
    label(b,p,"FOLD HOLD",0,-.024,.0027,center=True);b.flush()
    p=front_plane(4.998,0,2.356,22);b=panel(scene,"ECM RWR",p,.167,.126,title=False)
    for i,cap in enumerate(("POWER","DISPLAY","SPECIAL","OFFSET","BIT")):
        push(scene,b,p,"RWR "+cap,-.064+i*.032,.041,w=.024,h=.014,caption=cap)
    for u,cap in ((-.052,"AUDIO"),(0,"DIM"),(.052,"MODE")):
        knob(scene,b,p,"ECM "+cap,u,.006,r=.0065,caption=cap)
    for j,cap in enumerate(("STBY","REC","XMIT","GO","NO GO")):
        b.put("warning_dim",plate(p,.022,.010,.001,.001,-.056+j*.028,-.029,.002))
        label(b,p,cap,-.056+j*.028,-.031,.0024,n=.003,center=True)
    toggle(scene,b,p,"ECM power",- .048,-.050,caption=None)
    toggle(scene,b,p,"ECM mode",.048,-.050,caption=None);b.flush()

def console_plane(x,side,z=2.526):
    pitch,roll=math.radians(6),math.radians(side*8)
    u=(0,math.cos(roll),math.sin(roll))
    v=(-math.cos(pitch),-math.sin(roll)*math.sin(pitch),math.cos(roll)*math.sin(pitch))
    return Plane((x,side*.342,z),u,v)

def small_console(scene,name,x,side,h,controls,width=CONSOLE_W,z=2.526,plane_override=None):
    p=plane_override or console_plane(x,side,z);b=panel(scene,name,p,width,h,title=False)
    for item in controls:
        kind,cap,u,v,*rest=item
        if kind=="knob":knob(scene,b,p,name+" "+cap,u,v,r=rest[0] if rest else .0065,caption=cap)
        elif kind=="toggle":toggle(scene,b,p,name+" "+cap,u,v,caption=cap,guard=bool(rest and rest[0]))
        elif kind=="push":push(scene,b,p,name+" "+cap,u,v,w=.010,h=.009,caption=cap)
        elif kind=="dial":dial(b,p,cap,u,v,rest[0] if rest else .019)
        elif kind=="text":label(b,p,cap,u,v,rest[0] if rest else .003,center=True)
    b.flush()
    # Instrument backs and service wiring are exposed when console skins are hidden.
    q=Batch(scene,name+" underside",name+" switches and loom")
    for k,item in enumerate(controls):
        kind,cap,u,v,*_=item
        if kind in("toggle","knob","push"):
            q.put("black",cylinder(p.p(u,v,-.006),p.p(u,v,-.030),.0055,14))
            for j in(-1,1):
                a=p.p(u+j*.002,v,-.033);c=p.p(u+j*.002,v+.012,-.050)
                q.put("metal",cylinder(p.p(u+j*.002,v,-.025),a,.0008,8))
                q.put("wire_blue" if j<0 else "wire_red",tube([a,c,p.p(u*.5,.025,-.080)],.0009,7))
    for i in range(3):
        q.put("black",tube([p.p(-width*.35+i*.012,-h*.45,-.079),
                             p.p(-width*.35+i*.012,h*.45,-.079)],.003,8))
    q.flush();scene.fixed("Mount "+name+" underside",b.component,name+" underside")

def side_consoles(scene):
    # Distinct measured face envelopes, with original placement and geometry.
    small_console(scene,"FIRE TEST",4.901,-1,.0543067,[
        ("toggle","TEST A B",0,0)],width=.0722116)
    small_console(scene,"EXT LIGHTS",5.007,-1,.061976,[
        ("knob","POSITION",-.044,0),("knob","FORMATION",0,0),("toggle","STROBE",.044,0)],width=.1412875,z=2.554,
        plane_override=Plane((5.135,-.418,2.554),(-1,0,0),(0,-math.cos(math.radians(8)),math.sin(math.radians(8)))))
    small_console(scene,"FUEL",5.306,-1,.0746125,[
        ("toggle","DUMP",-.045,.014),("toggle","EXT TANKS",0,.014),
        ("toggle","PROBE",.046,.014),("toggle","WING INHIBIT",-.030,-.017),
        ("toggle","TANK PRESS",.034,-.017)])
    small_console(scene,"APU CRANK",5.386,-1,.049784,[
        ("toggle","APU",-.032,0),("toggle","CRANK",.032,0),
        ("text","OFF",0,-.015,.0025)],width=.118745,z=2.548)
    small_console(scene,"FCS",5.456,-1,.0555625,[
        ("knob","RUD TRIM",-.047,0,.009),("push","T/O",-.047,0),
        ("toggle","GAIN",.004,0,True),("push","RESET",.048,0)])
    small_console(scene,"COMM",5.585,-1,.1793875,[
        ("knob","COMM1",-.043,.055),("knob","COMM2",.043,.055),
        ("knob","TCN",-.043,.013),("knob","WPN",.043,.013),
        ("knob","RWR",-.043,-.032),("knob","ICS",.043,-.032),
        ("toggle","VOX",0,-.064),("text","VOLUME",0,.078,.0035)])
    small_console(scene,"OBOGS",5.712,-1,.0508,[
        ("toggle","OBOGS",-.022,0),("knob","OXY FLOW",.024,0)],width=.090424)
    small_console(scene,"MC HYD ISOL",5.765,-1,.04064,[
        ("toggle","MC",-.027,0),("toggle","HYD ISOL",.027,0,True)],width=.11176)
    small_console(scene,"ANT SELECT",5.818,-1,.0523875,[
        ("toggle","COMM",-.025,0),("toggle","IFF",.025,0)],width=.0904875)
    small_console(scene,"GEN TIE",5.875,-1,.04572,[
        ("toggle","RESET",0,0,True)],width=.13081)
    # Right sequence: electrical -> ECS -> lights -> sensors -> crypto.
    small_console(scene,"ELECTRICAL",5.118,1,.0650779,[
        ("toggle","L GEN",-.050,.012),("toggle","R GEN",-.050,-.017),
        ("toggle","BATT",.005,.013),("dial","VOLTS",.043,-.006,.018)])
    small_console(scene,"ECS",5.205,1,.0936625,[
        ("knob","TEMP",-.043,.022),("knob","BLEED AIR",.040,.022),
        ("toggle","ENG ANTI ICE",-.044,-.025),("toggle","PITOT",.010,-.025),
        ("toggle","CABIN",.050,-.025)])
    small_console(scene,"INTERIOR LIGHTS",5.302,1,.0841375,[
        ("knob","CONSOLES",-.045,.018),("knob","INST PNL",.001,.018),
        ("knob","FLOOD",.045,.018),("knob","CHART",-.043,-.022),
        ("knob","WARN",.001,-.022),("toggle","MODE",.045,-.022)])
    small_console(scene,"SENSORS",5.389,1,.0746125,[
        ("knob","RADAR",-.043,.012),("knob","INS",.044,.012),
        ("toggle","FLIR",-.034,-.020),("toggle","LTD R",.035,-.020)])
    small_console(scene,"KY58",5.476,1,.08255,[
        ("knob","MODE",-.043,.019),("knob","FILL",.043,.019),
        ("knob","VOL",-.043,-.020),("knob","POWER",.043,-.020)],width=.144526)
    small_console(scene,"CRYPTO",5.544,1,.036576,[
        ("toggle","HOLD",-.035,0),("toggle","MODE 4",0,0),("toggle","MASTER",.035,0)],width=.127)
    small_console(scene,"DEFOG",5.590,1,.0381,[
        ("knob","DEFOG",0,0)],width=.15367)
    # Realistic sparse sidewall breaker row and distinct canopy switch.
    for side in(-1,1):
        p=Plane((5.66,side*.444,2.735),(side,0,0),(0,0,1))
        b=panel(scene,("LEFT" if side<0 else "RIGHT")+" CIRCUIT BREAKERS",p,.380,.067,title=False)
        names=(("FCS1","FCS2","SPD BRK","L BAR","MC1","MC2","DISP","COMM")
               if side<0 else ("FCS3","FCS4","OBOGS","BATT","INS","RADAR","ECS","LT"))
        for i,cap in enumerate(names):
            u=-.1575+i*.045
            b.put("metal",cylinder(p.p(u,0,0),p.p(u,0,.003),.006,16))
            q=moving(scene,("Left" if side<0 else "Right")+" breaker "+cap,b.component,p.p(u,0,.003),p.n,(0,.006),"slider")
            q.put("black",cylinder(p.p(u,0,.003),p.p(u,0,.014),.0045,20))
            q.put("label_white",cylinder(p.p(u,0,.014),p.p(u,0,.0145),.002,16));q.flush()
            label(b,p,cap,u,-.015,.0027,center=True)
        if side>0:toggle(scene,b,p,"Cockpit CANOPY toggle",-.145,.038,caption="CANOPY")
        else:push(scene,b,p,"Countermeasures dispense",.150,.038,w=.021,round_button=True)
        b.flush()

def hud(scene):
    b=Batch(scene,"HUD assembly","HUD projector and combiner")
    p=front_plane(4.588,0,3.052,0)
    b.put("black",box((4.493,0,3.048),(.228,.188,.072)))
    b.put("cockpit_gray",box((4.486,0,3.088),(.149,.151,.012)))
    b.put("instrument_glass",box((4.474,0,3.096),(.108,.112,.006)))
    for sy in(-1,1):
        b.put("metal",tube([(4.465,sy*.098,3.072),(4.509,sy*.098,3.172),
                             (4.567,sy*.094,3.251)],.007,16))
        b.put("black",tube([(4.465,sy*.098,3.076),(4.514,sy*.098,3.175),
                             (4.571,sy*.094,3.253)],.0048,14))
        b.put("metal",cylinder((4.57,sy*.102,3.245),(4.57,sy*.087,3.245),.009,20))
    outline=[(4.470,-.088,3.105),(4.470,.088,3.105),
             (4.570,.091,3.255),(4.570,-.091,3.255)]
    b.put("hud_glass",prism(outline,(.003,0,0)))
    b.put("black",tube(outline+[outline[0]],.0024,10))
    # Original HUD symbology. No simulator screen/texture is extracted.
    def hp(y,z):return(4.474+(z-3.105)*.100/.150,y,z)
    for i in(-2,-1,0,1,2):
        zz=3.18+i*.019;extent=.043 if i==0 else .024
        b.put("display_green",tube([hp(-extent,zz),hp(-.007,zz)],.00043,6))
        b.put("display_green",tube([hp(.007,zz),hp(extent,zz)],.00043,6))
    b.put("display_green",tube([hp(-.010,3.171),hp(0,3.178),hp(.010,3.171)],.0005,6))
    # AoA indexer and separate lock/shoot repeater housings.
    for sy,name in((-1,"AOA INDEXER"),(1,"LOCK SHOOT")):
        pp=front_plane(4.592,sy*.127,3.178,0)
        b.put("black",plate(pp,.026,.078,.019,.004))
        for k in range(3):
            z=.023-k*.023
            b.put(("red","yellow","indicator_green")[k],cylinder(pp.p(0,z,.001),pp.p(0,z,.002),.006,24))
    b.flush();scene.fixed("Mount HUD assembly","Cockpit fixed","HUD assembly")
    # Small standby magnetic compass on the right windscreen arch.
    p=front_plane(4.615,.292,3.050,10)
    q=Batch(scene,"Standby compass","Compass")
    q.put("black",plate(p,.054,.052,.048,.008))
    q.put("instrument_glass",plate(p,.042,.019,.001,.002,0,0,.001))
    label(q,p,"E  09  S",0,-.004,.004,n=.002,center=True)
    q.flush();scene.fixed("Mount standby compass","Cockpit fixed","Standby compass")

def seat(scene):
    b=Batch(scene,"Ejection seat","NACES shell and equipment")
    # Original formed side plates, bucket, survival pack and back frame.
    side_profile=[(5.215,2.270),(5.200,2.405),(5.275,2.520),(5.610,2.525),
                  (5.746,2.605),(5.895,3.020),(6.000,3.165),(6.085,3.165),
                  (6.068,2.340),(5.785,2.190),(5.350,2.190)]
    for sy in(-1,1):
        ps=[(x,sy*.226,z) for x,z in side_profile]
        b.put("seat_black",prism(ps,(0,sy*.013,0)))
        b.put("cockpit_gray",tube([(x,sy*.240,z) for x,z in side_profile]+[(side_profile[0][0],sy*.240,side_profile[0][1])],.0035,10))
        # Gussets, plate relief edges and individually modeled fasteners.
        for x,z in((5.30,2.30),(5.50,2.30),(5.72,2.34),(5.82,2.51),(5.90,2.72),(5.96,2.94),(6.02,3.12)):
            b.put("metal",cylinder((x,sy*.238,z),(x,sy*.245,z),.0042,18))
        for x,z,w,h in((5.45,2.30,.23,.095),(5.83,2.48,.11,.17),(5.97,2.89,.085,.24)):
            pl=Plane((x,sy*.243,z),(sy,0,0),(0,0,1))
            b.put("seat_black",plate(pl,w,h,.003,.008))
        # Visible seat-back fittings are exterior shells, not a functional firing system.
        b.put("metal",cylinder((6.026,sy*.212,2.27),(6.026,sy*.212,3.162),.019,24))
        b.put("black",cylinder((6.031,sy*.212,2.31),(6.031,sy*.212,3.105),.011,20))
        for z in(2.35,2.65,2.95,3.11):
            b.put("metal",box((6.035,sy*.217,z),(.055,.036,.022)))
        b.put("black",box((5.975,sy*.255,2.805),(.105,.040,.130)))
        for i in range(4):
            b.put("metal",cylinder((5.94,sy*.277,2.76+i*.027),(5.94,sy*.282,2.76+i*.027),.0035,16))
    b.put("seat_black",box((5.535,0,2.324),(.540,.430,.095)))
    b.put("seat_cushion",box((5.520,0,2.413),(.440,.390,.070)))
    b.put("fabric",sphere((5.505,0,2.447),(.225,.191,.024),36,12))
    for sy in(-1,1):
        b.put("seat_cushion",tube([(5.282,sy*.150,2.440),(5.350,sy*.178,2.466),
                                   (5.585,sy*.178,2.466),(5.707,sy*.138,2.452)],.024,16))
    # Reclined back-pad panel; 16-degree envelope matches the retained seat station.
    b.put("seat_black",prism([(5.736,-.171,2.458),(5.736,.171,2.458),
                               (5.897,.163,3.012),(5.897,-.163,3.012)],(.034,0,0)))
    for sy in(-1,1):
        b.put("black",tube([(5.733,sy*.169,2.46),(5.893,sy*.162,3.015)],.014,16))
        b.put("fabric",tube([(5.715,sy*.142,2.495),(5.868,sy*.138,2.990)],.002,7))
    # NACES parachute/headbox and upper padded face with shoulder-strap channels.
    h=Plane((5.894,0,3.079),(0,-1,0),(0,0,1))
    b.put("seat_black",plate(h,.337,.230,.188,.025))
    b.put("black",plate(h,.236,.186,.016,.016,n=.004))
    for sy in(-1,1):
        b.put("seat_black",box((5.915,sy*.160,3.173),(.172,.042,.034)))
        b.put("harness_olive",webbing([(5.879,sy*.093,3.176),(5.875,sy*.100,3.026),
                                      (5.821,sy*.122,2.872),(5.720,sy*.149,2.614)],.033,.0028))
        # Free shoulder fittings hang ahead of the seat for an unoccupied view.
        loop=[(5.725,sy*.145,2.688),(5.662,sy*.160,2.630),
              (5.671,sy*.164,2.577),(5.728,sy*.149,2.606)]
        b.put("harness_olive",webbing(loop,.028,.0025))
        b.put("metal",torus((5.671,sy*.159,2.620),.018,.0035,axis=(0,1,0),segments=32,sides=8))
        b.put("harness_olive",webbing([(5.73,sy*.213,2.46),(5.52,sy*.126,2.47),
                                      (5.345,sy*.048,2.467)],.040))
        b.put("metal",box((5.505,sy*.126,2.474),(.026,.047,.008)))
        # Seat stitching, restrained webbing and external service hose.
        for k in range(10):
            xx=5.34+k*.032
            b.put("cream",tube([(xx,sy*.168,2.473),(xx+.013,sy*.168,2.473)],.0007,5))
        hose=[(5.902,sy*.245,2.663),(5.847,sy*.252,2.515),(5.638,sy*.211,2.426),(5.280,sy*.205,2.304)]
        b.put("black",tube(hose,.008,10))
        for a,c in zip(hose,hose[1:]):
            for j in range(8):
                b.put("harness_olive",torus(lerp(a,c,(j+.5)/8),.0087,.0012,axis=sub(c,a),segments=12,sides=5))
    # Central lap buckle and one decorative striped initiation loop.
    b.put("metal",cylinder((5.340,0,2.467),(5.340,0,2.480),.024,28))
    b.put("black",cylinder((5.340,0,2.481),(5.340,0,2.483),.017,24))
    loop=[]
    for i in range(33):
        a=math.pi*i/32
        loop.append((5.245-.018*math.sin(a),-.046*math.cos(a),2.430+.078*math.sin(a)))
    for i in range(len(loop)-1):
        b.put("yellow" if (i//2)%2==0 else "black",tube(loop[i:i+2],.0065,10))
    # Headbox danger marking and identification plate are original lettering.
    pp=Plane((6.085,0,3.080),(0,1,0),(0,0,1))
    b.put("red",plate(pp,.168,.026,.001,.001,0,.032,.001))
    label(b,pp,"DANGER",0,.030,.008,n=.002,center=True)
    label(b,pp,"SJU-17 NACES",0,-.010,.007,n=.002,center=True)
    # Blue leg-restraint straps and side height-adjustment actuator envelope.
    for sy in(-1,1):
        b.put("blue",webbing([(5.55,sy*.190,2.282),(5.27,sy*.160,2.245),
                               (5.19,sy*.147,2.200)],.018,.002))
    b.put("metal",cylinder((5.97,.205,2.215),(6.04,.205,2.555),.016,24))
    b.put("black",cylinder((6.04,.205,2.555),(6.05,.205,2.635),.009,20))
    b.flush()
    scene.joint("Seat height adjustment","Cockpit fixed","Ejection seat",(5.60,0,2.35),(0,0,1),(-.06,.06),0,"slider")

def hotas_hat(scene,name,parent,p,w=.018):
    origin=p.p(0,0,0)
    stem=moving(scene,name+" fore aft",parent,origin,p.u,(-12,12))
    stem.put("metal",cylinder(origin,p.p(0,0,.007),.0032,16));stem.flush()
    cap=moving(scene,name+" left right",stem.component,origin,p.v,(-12,12))
    cap.put("button_gray",plate(p,w,w,.006,.004,n=.013))
    for points in(((-w*.25,0),(w*.25,0)),((0,-w*.25),(0,w*.25))):
        line(cap,p,points,"black",.0006,n=.0134)
    cap.flush()

def controls(scene):
    fixed=Batch(scene,"Cockpit fixed","Flight controls mountings")
    origin=(5.040,0,2.253)
    fixed.put("black",box((5.04,0,2.205),(.170,.165,.070)))
    for j in range(6):
        fixed.put("black",torus((5.04,0,2.237+j*.006),.076-j*.008,.005,segments=40,sides=8))
    cradle=Batch(scene,"Stick pitch cradle","Stick pitch bearing")
    cradle.put("metal",cylinder((5.04,-.060,2.253),(5.04,.060,2.253),.020,28));cradle.flush()
    scene.joint("Control stick pitch","Cockpit fixed","Stick pitch cradle",origin,(0,1,0),(-18,18),0)
    b=Batch(scene,"Control stick","Hornet HOTAS grip")
    b.put("metal",cylinder(origin,(5.009,0,2.650),.016,28,.013))
    b.put("black",tube([(5.01,0,2.652),(5.013,0,2.709),(5.005,0,2.760)],.030,24))
    b.put("black",sphere((5.002,0,2.751),(.043,.035,.056),32,18))
    b.put("black",box((5.004,0,2.784),(.075,.077,.028)))
    for k in range(5):
        b.put("cockpit_gray",tube([(4.985,-.023,2.675+k*.016),(4.976,0,2.675+k*.016),
                                    (4.985,.023,2.675+k*.016)],.0018,8))
    b.flush()
    scene.joint("Control stick roll","Stick pitch cradle","Control stick",origin,(1,0,0),(-18,18),0)
    hp=Plane((4.985,-.023,2.802),(0,1,0),(-1,0,0))
    hotas_hat(scene,"Stick trim hat","Control stick",hp,.018)
    hotas_hat(scene,"Sensor control hat","Control stick",Plane((5.024,.023,2.802),(0,1,0),(-1,0,0)),.016)
    hp=front_plane(5.039,-.022,2.771,0)
    q=Batch(scene,"Control stick","Stick fixed buttons")
    push(scene,q,hp,"Stick weapon release",0,0,w=.011,round_button=True)
    hotas_hat(scene,"Weapon select hat","Control stick",front_plane(4.967,-.030,2.759,0),.015)
    # Trigger and paddle each pivot independently with their grip.
    t=moving(scene,"Stick trigger","Control stick",(4.967,0,2.758),(0,1,0),(0,15))
    t.put("black",tube([(4.962,-.022,2.756),(4.944,-.024,2.716),
                         (4.945,.023,2.711),(4.966,.023,2.751)],.0055,12));t.flush()
    t=moving(scene,"Stick paddle disconnect","Control stick",(5.033,0,2.676),(0,1,0),(-12,12))
    t.put("black",prism([(5.034,-.031,2.676),(5.034,.031,2.676),
                          (5.061,.035,2.724),(5.061,-.035,2.724)],(.005,0,0)));t.flush()
    q.flush()
    for cap,yy in(("Left",-.350),("Right",-.282)):
        comp="Throttle "+cap;pivot=(5.190,yy,2.564)
        fixed.put("cockpit_gray",box((5.123,yy,2.549),(.300,.063,.026)))
        fixed.put("black",box((5.123,yy,2.567),(.274,.012,.008)))
        b=Batch(scene,comp,cap+" throttle")
        b.put("metal",cylinder(pivot,(4.995,yy,2.686),.011,24))
        b.put("black",box((4.995,yy,2.705),(.118,.055,.055)))
        b.put("button_gray",sphere((4.994,yy,2.731),(.057,.026,.015),28,12))
        for k in range(6):
            b.put("black",box((4.948+k*.018,yy,2.738),(.003,.047,.004)))
        b.put("metal",cylinder((5.190,yy-.028,2.564),(5.190,yy+.028,2.564),.026,32))
        b.flush();scene.joint(cap+" throttle travel","Cockpit fixed",comp,pivot,(0,1,0),(-25,40),0)
        pp=Plane((4.971,yy,2.746),(0,1,0),(-1,0,0))
        hotas_hat(scene,cap+" throttle TDC",comp,pp,.016)
        q=Batch(scene,comp,cap+" throttle switches")
        pp=Plane((4.986,yy-.029,2.704),(-1,0,0),(0,0,1))
        push(scene,q,pp,cap+" throttle dispense",0,0,w=.010,round_button=True)
        pp=Plane((5.037,yy,2.715),(0,1,0),(0,0,1))
        toggle(scene,q,pp,cap+" throttle speedbrake",0,0,limits=(-15,15))
        q.flush()
    # Friction adjuster and position marks beside the quadrant.
    p=Plane((5.185,-.263,2.571),(1,0,0),(0,0,1))
    q=Batch(scene,"Cockpit fixed","Throttle quadrant details")
    knob(scene,q,p,"Throttle friction",0,0,r=.018,limits=(-90,90))
    label(q,console_plane(5.12,-1),"IDLE   MIL   MAX",-.060,-.050,.003)
    q.flush()
    # Pedal carriages keep measured footwell spacing and actual seated-leg reach.
    for cap,yy in(("Left",-.157),("Right",.157)):
        origin=(4.575,yy,2.176);comp=cap+" rudder carriage"
        b=Batch(scene,comp,cap+" pedal carriage")
        for sy in(-1,1):
            b.put("metal",cylinder((4.302,yy+sy*.046,2.139),(4.675,yy+sy*.046,2.139),.0075,20))
            b.put("steel",box((4.575,yy+sy*.047,2.155),(.096,.020,.038)))
        b.put("metal",cylinder((4.575,yy-.060,2.176),(4.575,yy+.060,2.176),.012,24))
        b.flush();scene.joint(cap+" rudder input","Cockpit fixed",comp,origin,(1,0,0),(-.045,.045),0,"slider")
        ped=cap+" rudder pedal";b=Batch(scene,ped,cap+" toe brake")
        pp=front_plane(4.532,yy,2.248,19)
        b.put("metal",plate(pp,.112,.144,.007,.014))
        b.put("black",plate(pp,.091,.119,.003,.009,n=.001))
        for j in range(7):
            line(b,pp,[(-.043,-.051+j*.017),(.043,-.051+j*.017)],"cockpit_gray",.0021,n=.005)
        for u in(-.046,.046):
            b.put("metal",tube([pp.p(u,-.054,.004),pp.p(u,.056,.004)],.0045,12))
        b.flush();scene.joint(cap+" toe brake",comp,ped,origin,(0,1,0),(-4,18),0)
        fixed.put("black",tube([(4.41,yy,2.145),(4.26,yy,2.165),(4.23,yy*.9,2.24)],.004,10))
    # Canopy mechanical lock on the inboard right sill.
    origin=(5.615,.416,2.651);end=(5.462,.416,2.651)
    q=moving(scene,"Canopy manual lock lever","Cockpit fixed",origin,(0,1,0),(-35,35))
    q.put("metal",cylinder(origin,end,.007,18))
    q.put("yellow",cylinder((end[0],end[1]-.026,end[2]),(end[0],end[1]+.026,end[2]),.012,24))
    q.put("black",cylinder((end[0],end[1]-.005,end[2]),(end[0],end[1]+.005,end[2]),.0124,24));q.flush()
    fixed.flush()

def tub(scene):
    b=Batch(scene,"Cockpit fixed","Tub mounts and structure")
    b.put("cockpit_gray",box((5.22,0,2.083),(1.96,.535,.028)))
    for sy in(-1,1):
        # Inner rails, floor channels, seat tracks and control-console bearers.
        b.put("metal",tube([(4.23,sy*.250,2.115),(5.10,sy*.250,2.115),(6.18,sy*.250,2.115)],.009,14))
        b.put("cockpit_gray",tube([(4.78,sy*.267,2.485),(5.18,sy*.267,2.503),(6.03,sy*.267,2.503)],.008,14))
        b.put("cockpit_gray",tube([(4.83,sy*.420,2.529),(5.20,sy*.420,2.546),(6.07,sy*.420,2.546)],.008,14))
        for x in(4.88,5.16,5.48,5.80,6.06):
            b.put("metal",cylinder((x,sy*.412,2.13),(x,sy*.412,2.535),.0065,14))
            b.put("metal",cylinder((x,sy*.272,2.13),(x,sy*.272,2.495),.0055,14))
        for xx in(5.904,5.930):
            b.put("metal",tube([(xx,sy*.217,2.14),(xx+.188,sy*.217,3.157)],.008,18))
        for zz in(2.29,2.59,2.89,3.13):
            xx=5.90+(zz-2.14)*.185
            b.put("black",cylinder((xx,sy*.198,zz),(xx,sy*.224,zz),.018,24))
            b.put("metal",cylinder((xx,sy*.223,zz),(xx,sy*.229,zz),.0065,20))
        # Clipped electrical looms routed behind removable side lining.
        for k in range(4):
            pts=[(4.36,sy*(.384+k*.011),2.235),(4.85,sy*(.384+k*.011),2.207),
                 (5.55,sy*(.384+k*.011),2.250),(6.15,sy*.375,2.375+k*.012)]
            b.put("black",tube(pts,.004,9))
        for xx in(4.55,4.95,5.36,5.76):
            b.put("aluminum",box((xx,sy*.405,2.249),(.016,.066,.009)))
    # Forward bulkhead structure, ventilation ducts and rudder actuator envelope.
    b.put("cockpit_gray",box((4.225,0,2.331),(.020,.556,.465)))
    for sy in(-1,1):
        b.put("black",tube([(4.42,sy*.220,2.50),(4.48,sy*.247,2.35),(4.67,sy*.235,2.23)],.022,18))
        pp=front_plane(4.705,sy*.244,2.278,15)
        b.put("black",plate(pp,.052,.062,.025,.009))
        for k in range(6):
            b.put("cockpit_gray",tube([pp.p(-.022,-.025+k*.010,.002),pp.p(.022,-.025+k*.010,.002)],.0013,8))
    b.flush();scene.fixed("Cockpit installed in airframe","Airframe","Cockpit fixed")
    skin=Batch(scene,"Cockpit liners","Removable cockpit lining")
    # Thin removable trim panels, kept separate for inspection of backs/wiring.
    for sy in(-1,1):
        for i in range(5):
            x=4.63+i*.31
            ps=[(x,sy*.428,2.16),(x+.300,sy*.428,2.16),
                (x+.300,sy*.448,2.78),(x,sy*.448,2.78)]
            skin.put("cockpit_gray",prism(ps,(0,sy*.003,0)))
            for z in(2.22,2.70):
                for xx in(x+.025,x+.275):
                    skin.put("black",cylinder((xx,sy*.427,z),(xx,sy*.422,z),.0027,16))
    skin.put("cockpit_gray",box((6.225,0,2.459),(.020,.776,.730)))
    skin.put("black",box((5.01,0,2.101),(1.48,.485,.008)))
    for sy in(-1,1):
        skin.put("metal",box((4.59,sy*.155,2.108),(.53,.122,.003)))
        for k in range(10):
            skin.put("cockpit_gray",box((4.36+k*.045,sy*.155,2.111),(.0015,.112,.0015)))
    skin.flush();scene.fixed("Mount removable cockpit liners","Cockpit fixed","Cockpit liners")

def material_definitions(scene):
    choices={
      "cockpit_gray":("Aluminum",[96,102,103],0,.68),
      "panel_black":("Aluminum",[28,31,32],0,.74),
      "button_gray":("ABS Plastic",[105,111,112],0,.56),
      "label_white":("Aluminum",[220,217,202],0,.70),
      "warning_dim":("ABS Plastic",[99,83,41],0,.45),
      "indicator_green":("ABS Plastic",[44,109,54],0,.42),
      "display_dark":("Glass",[4,22,15],0,.20),
      "display_green":("Glass",[74,177,94],0,.25),
      "instrument_glass":("Glass",[12,20,20],.03,.16),
      "connector_blue":("Aluminum",[42,61,70],.63,.36),
      "pcb_green":("ABS Plastic",[40,80,53],0,.58),
      "wire_blue":("Nylon",[61,88,131],0,.71),
      "wire_red":("Nylon",[140,48,39],0,.71),
      "seat_black":("Aluminum",[37,42,43],0,.63),
      "seat_cushion":("Nylon",[139,132,64],0,.96),
      "harness_olive":("Nylon",[99,105,68],0,.93),
    }
    for key,(physical,color,metallic,roughness) in choices.items():
        scene.materials.setdefault(key,dict(physical=physical,color=color,metallic=metallic,roughness=roughness))

def build(scene):
    material_definitions(scene)
    tub(scene)
    instrument_panel(scene)
    main_side_panels(scene)
    side_consoles(scene)
    hud(scene)
    seat(scene)
    controls(scene)
    pilot(scene)
    scene.notes.append("RC3 cockpit rebuild: DDI 163.5125 x 172.72 mm, AMPCD 167.005 x 182.6228 mm, "
        "UFC main face 173.0375 x 114.3 mm, upper central face 535.94 x 230.1875 mm; "
        "dimensions measured from OpenHornet public manufacturing reference envelopes at commit "+REFERENCE_COMMIT+". "
        "All meshes, panel outlines, labels and symbology are original; no OpenHornet/DCS paths, meshes or textures imported. "
        "Instrument face relocated to x4.75 m for realistic seat-to-panel reach; authentic named console families replace generic repeated panels. "
        "Includes instrument backs, connector hardware, cable looms, removable lining, photo-informed NACES seat and poseable controls. "
        "Internal electronics are visible illustrative packaging; no avionics simulation or certified aircraft wiring schematic.")


def pilot(scene):
    scene.materials.setdefault("pilot_visor", dict(physical="Polycarbonate", color=[12, 22, 28],
                                                   metallic=.14, roughness=.115))
    b = Batch(scene, "Pilot", "Seated pilot")
    # Cloth-suited torso and seated legs, proportioned around the cockpit seat.
    b.put("olive", sphere((5.56, 0, 2.762), (.190, .193, .236), 32, 18))
    b.put("olive", sphere((5.575, 0, 2.525), (.198, .191, .118), 28, 14))
    for sy in (-1, 1):
        hip = (5.53, sy * .108, 2.527)
        knee = (5.081, sy * .160, 2.410)
        ankle = (4.649, sy * .158, 2.204)
        b.put("olive", capsule(hip, knee, .100, .080, 20))
        b.put("olive", capsule(knee, ankle, .075, .055, 20))
        b.put("fabric", sphere((5.085, sy * .160, 2.429), (.098, .080, .044), 20, 12))
        b.put("black", sphere((4.545, sy * .158, 2.180), (.139, .067, .060), 24, 12))
        b.put("black", cylinder((4.645, sy * .158, 2.193), (4.662, sy * .158, 2.319), .057, 18, .063))
        b.put("tire", box((4.544, sy * .158, 2.131), (.229, .113, .015)))
        for k in range(5):
            b.put("gray", tube([(4.524 + k * .018, sy * .158 - .037, 2.228),
                                 (4.538 + k * .018, sy * .158 + .037, 2.228)], .0017, 5))
        # Trouser thigh pockets, ankle cuffs and stitching.
        b.put("fabric", box((5.29, sy * .203, 2.495), (.174, .018, .069)))
        b.put("cream", tube([(5.35, sy * .184, 2.542), (5.13, sy * .202, 2.485),
                               (4.85, sy * .195, 2.342)], .0012, 5))

    shoulders = {"Left": (5.55, -.197, 2.898), "Right": (5.55, .197, 2.898)}
    elbows = {"Left": (5.30, -.266, 2.746), "Right": (5.29, .239, 2.734)}
    wrists = {"Left": (5.02, -.348, 2.735), "Right": (5.025, .032, 2.775)}
    for label in ("Left", "Right"):
        shoulder, elbow, wrist = shoulders[label], elbows[label], wrists[label]
        b.put("olive", capsule(shoulder, elbow, .077, .061, 20))
        b.put("olive", capsule(elbow, wrist, .059, .039, 20))
        b.put("fabric", sphere(wrist, (.060, .052, .028), 20, 10))
        palm = add(wrist, (-.027, 0, .003))
        b.put("cream", sphere(palm, (.055, .047, .026), 20, 12))
        # Four curled fingers and a separate thumb identify a glove at close range.
        for k in range(4):
            yy = palm[1] - .032 + k * .020
            a, c, d = (palm[0] - .018, yy, palm[2] + .007), (palm[0] - .048, yy, palm[2] - .006), (palm[0] - .039, yy, palm[2] - .030)
            b.put("cream", tube([a, c, d], .0090, 9))
            b.put("fabric", tube([a, c], .0009, 5))
        side = 1 if label == "Left" else -1
        b.put("cream", capsule((palm[0] + .014, palm[1] + side * .033, palm[2]),
                               (palm[0] - .018, palm[1] + side * .054, palm[2] - .024), .012, .010, 12))

    # Flight vest and shoulder harness. No personal identity or borrowed badges.
    b.put("fabric", prism([(5.361, -.147, 2.570), (5.361, .147, 2.570),
                            (5.401, .151, 2.921), (5.401, -.151, 2.921)], (.019, 0, 0)))
    for sy in (-1, 1):
        b.put("olive", box((5.351, sy * .078, 2.746), (.026, .112, .126)))
        b.put("cream", webbing([(5.57, sy * .144, 2.976), (5.397, sy * .151, 2.882),
                                 (5.357, sy * .125, 2.702), (5.344, sy * .045, 2.591)], .038))
        b.put("metal", box((5.340, sy * .130, 2.762), (.012, .047, .034)))
        b.put("cream", webbing([(5.52, sy * .180, 2.548), (5.348, sy * .099, 2.571),
                                 (5.339, 0, 2.590)], .037))
    b.put("steel", cylinder((5.326, 0, 2.592), (5.340, 0, 2.592), .031, 22))
    b.put("black", cylinder((5.322, 0, 2.592), (5.325, 0, 2.592), .019, 18))
    b.put("black", tube([(5.340, -.005, 2.600), (5.374, -.005, 2.916)], .002, 6))
    b.put("white", text("NAVY", (5.330, .128, 2.830), .012, right=(0, -1, 0), up=(0, 0, 1), depth=.0004))
    # Collar, flight helmet shell, ear covers, curved visor, oxygen mask.
    b.put("fabric", cylinder((5.555, 0, 2.960), (5.555, 0, 3.012), .072, 24))
    hc = (5.556, 0, 3.095)
    b.put("white", sphere(hc, (.150, .141, .145), 36, 20))
    b.put("pilot_visor", ellipsoid_patch(hc, (.154, .146, .151)))
    b.put("black", tube([(5.488, -.126, 3.159), (5.416, -.072, 3.192),
                           (5.403, 0, 3.202), (5.416, .072, 3.192), (5.488, .126, 3.159)], .0045, 8))
    for sy in (-1, 1):
        b.put("black", cylinder((5.555, sy * .134, 3.068), (5.555, sy * .151, 3.068), .053, 22))
        b.put("white", cylinder((5.555, sy * .152, 3.068), (5.555, sy * .157, 3.068), .045, 22))
        b.put("gray", tube([(5.409, sy * .050, 3.045), (5.485, sy * .124, 3.055),
                              (5.558, sy * .154, 3.071)], .009, 8))
    b.put("black", sphere((5.411, 0, 3.036), (.063, .076, .056), 28, 15))
    b.put("gray", cylinder((5.354, 0, 3.020), (5.342, 0, 3.020), .026, 20))
    b.put("metal", torus((5.343, 0, 3.020), .022, .003, axis=(1, 0, 0), segments=24, sides=7))
    hose = [(5.342, 0, 3.020), (5.306, -.031, 2.975), (5.305, -.087, 2.887),
            (5.344, -.137, 2.794), (5.431, -.183, 2.672), (5.602, -.221, 2.566)]
    b.put("black", tube(hose, .018, 12))
    # Corrugated oxygen hose rings follow the hose tangent.
    for a, c in zip(hose, hose[1:]):
        length = math.sqrt(sum((u - v) ** 2 for u, v in zip(a, c)))
        count = max(2, int(length / .013))
        axis = sub(c, a)
        for j in range(count):
            p = lerp(a, c, (j + .5) / count)
            b.put("cockpit", torus(p, .0185, .0028, axis=axis, segments=16, sides=6))
    b.put("steel", cylinder(hose[-1], add(hose[-1], (.025, 0, 0)), .023, 16))
    b.flush()
    scene.fixed("Pilot harnessed to seat", "Ejection seat", "Pilot")


