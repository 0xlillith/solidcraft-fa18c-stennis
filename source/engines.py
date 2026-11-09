"""Original articulated F404-family visual engines for the F/A-18C showcase.

GE overall dimensions and publicly described F404 architecture are respected.
Blade profiles/counts, internal stations, small hardware, clearances, and the
nozzle linkage schedule are authored visualization geometry, not GE CAD or
engineering data. See ../research/F404_REFERENCE_AND_MODELING_NOTES.md.
Units metres, X aft. Stainless Steel is the nearest available material proxy
for unavailable nickel hot-section alloys. This module performs no rendering.
"""
from __future__ import annotations
import math
from scene_api import (Mesh, box, cylinder, sphere, torus, tube, prism, text,
                       add, sub, mul, cross, dot, unit, triangulate)

TAU=math.tau
LENGTH=154*.0254
INLET_DIAMETER=28*.0254
MAX_DIAMETER=35*.0254
DEFAULT_EXIT_X=16.68
DEFAULT_CENTRES=((- .71,1.98),(.71,1.98))
# Repeated blade counts below are authored details, not production GE counts.
FAN_STAGES=(
    dict(u=.205,hub=.105,tip=.3515,chord=.157,count=28,twist=(53,27)),
    dict(u=.405,hub=.132,tip=.347,chord=.133,count=34,twist=(49,25)),
    dict(u=.585,hub=.158,tip=.340,chord=.115,count=40,twist=(46,22)),
)
HPC_STAGES=tuple(dict(u=.865+.093*i,hub=.164+.0038*i,tip=.254-.0061*i,
    chord=.074-.0036*i,count=(36,38,40,42,46,48,50)[i],
    twist=(47-1.3*i,28-1.2*i)) for i in range(7))
TURBINE_STAGES=(
    dict(name='HPT',u=2.045,hub=.164,tip=.251,chord=.087,count=58,twist=(-48,-26)),
    dict(name='LPT',u=2.233,hub=.139,tip=.286,chord=.108,count=72,twist=(-44,-23)),
)
ENGINE_MATERIALS={
 'engine_titanium':dict(physical='Titanium',color=[146,151,156],metallic=.82,roughness=.33),
 'engine_titanium_case':dict(physical='Titanium',color=[118,128,134],metallic=.72,roughness=.43),
 'engine_steel':dict(physical='Stainless Steel',color=[161,167,170],metallic=.88,roughness=.29),
 'engine_nickel_proxy':dict(physical='Stainless Steel',color=[137,128,108],metallic=.78,roughness=.43),
 'engine_hot_inner':dict(physical='Stainless Steel',color=[99,91,78],metallic=.63,roughness=.66),
 'engine_hot_dark':dict(physical='Stainless Steel',color=[66,65,61],metallic=.58,roughness=.72),
 'engine_heat_bronze':dict(physical='Stainless Steel',color=[126,106,76],metallic=.72,roughness=.48),
 'engine_heat_blue':dict(physical='Stainless Steel',color=[80,94,116],metallic=.71,roughness=.48),
 'engine_gearbox':dict(physical='Aluminum',color=[100,115,116],metallic=.55,roughness=.50),
 'engine_hose':dict(physical='ABS Plastic',color=[41,43,44],metallic=.12,roughness=.76),
 'engine_copper':dict(physical='Copper',color=[148,107,78],metallic=.70,roughness=.44),
}

def polar(u,radius,theta):
    return (u,radius*math.cos(theta),radius*math.sin(theta))
def radial(theta):return (0.,math.cos(theta),math.sin(theta))
def tangent(theta):return (0.,-math.sin(theta),math.cos(theta))

def annulus(profile,theta0=0.,theta1=TAU,segments=96):
    """Closed hollow volume, from (x,inner radius,outer radius) stations."""
    profile=list(profile)
    n=max(3,int(round(segments*(theta1-theta0)/TAU)))
    complete=abs(theta1-theta0-TAU)<1e-8
    ringn=n if complete else n+1
    vs=[];fs=[]
    for x,ri,ro in profile:
        for r in (ri,ro):
            vs.extend(polar(x,r,theta0+(theta1-theta0)*i/n) for i in range(ringn))
    def ix(s,o,j):return s*2*ringn+o*ringn+j
    def face(a,b,c,d,desired):
        f=(a,b,c,d)
        if dot(cross(sub(vs[b],vs[a]),sub(vs[c],vs[a])),desired)<0:f=(d,c,b,a)
        fs.extend(((f[0],f[1],f[2]),(f[0],f[2],f[3])))
    for s in range(len(profile)-1):
        for j in range(n):
            k=(j+1)%ringn;th=theta0+(theta1-theta0)*(j+.5)/n
            face(ix(s,1,j),ix(s,1,k),ix(s+1,1,k),ix(s+1,1,j),radial(th))
            face(ix(s,0,j),ix(s,0,k),ix(s+1,0,k),ix(s+1,0,j),mul(radial(th),-1))
        if not complete:
            face(ix(s,0,0),ix(s,1,0),ix(s+1,1,0),ix(s+1,0,0),mul(tangent(theta0),-1))
            face(ix(s,0,n),ix(s,1,n),ix(s+1,1,n),ix(s+1,0,n),tangent(theta1))
    for s,d in ((0,(-1,0,0)),(len(profile)-1,(1,0,0))):
        for j in range(n):
            k=(j+1)%ringn
            face(ix(s,0,j),ix(s,0,k),ix(s,1,k),ix(s,1,j),d)
    return Mesh(vs,fs)

def ring(u,ri,ro,width=.015,theta0=0.,theta1=TAU,segments=96):
    return annulus([(u-width/2,ri,ro),(u+width/2,ri,ro)],theta0,theta1,segments)

def bolt_circle(u,radius,count,head=.006,length=.014,theta0=0.,theta1=TAU,phase=0.):
    meshes=[]
    for i in range(count):
        th=TAU*(i+.5)/count+phase
        if theta0-1e-8<=th%TAU<theta1-1e-8:
            p=polar(u,radius,th)
            meshes.extend((cylinder(add(p,(-length/2,0,0)),add(p,(length/2,0,0)),head*.72,12),
              cylinder(add(p,(length/2,0,0)),add(p,(length/2+.004,0,0)),head,6)))
    return Mesh.merged(meshes)

def blade(u,root,tip,chord,twist=(48,24),theta=0.,camber=.025,
          thickness=.075,sweep=.018,lean=.03,spans=6,samples=17):
    """Original twisted cambered blade, cylindrical tips, closed root/end faces."""
    qs=[.5*(1-math.cos(math.pi*i/(samples-1))) for i in range(samples)]
    outline=[(q,1) for q in qs]+[(q,-1) for q in qs[-2:0:-1]]
    vs=[];fs=[];capcoords=[]
    for s in range(spans):
        f=s/(spans-1);r=root+(tip-root)*f
        beta=math.radians(twist[0]+(twist[1]-twist[0])*f)
        c=chord*(1-.20*f+.025*math.sin(math.pi*f));section=[]
        for q,side in outline:
            yt=5*thickness*c*(.2969*math.sqrt(q)-.1260*q-.3516*q*q+.2843*q**3-.1036*q**4)
            yc=camber*c*4*q*(1-q);a=(q-.45)*c;b=yc+side*yt
            axial=a*math.cos(beta)-b*math.sin(beta)
            circum=a*math.sin(beta)+b*math.cos(beta)
            vs.append(polar(u+axial+sweep*f*f,r,theta+circum/r+lean*f*f))
            section.append((a,b,0.))
        if s==0:capcoords=section
    n=len(outline)
    for s in range(spans-1):
        for j in range(n):
            a=s*n+j;b=s*n+(j+1)%n;c=b+n;d=a+n
            fs.extend(((a,b,c),(a,c,d)))
    caps=triangulate(capcoords)
    fs.extend((c,b,a) for a,b,c in caps)
    off=(spans-1)*n
    fs.extend((a+off,b+off,c+off) for a,b,c in caps)
    mesh=Mesh(vs,fs)
    if sum(dot(vs[a],cross(vs[b],vs[c])) for a,b,c in fs)<0:
        mesh.faces=[(a,c,b) for a,b,c in fs]
    return mesh

def blade_row(u,root,tip,chord,count,twist=(48,24),phase=0.,**kw):
    base=blade(u,root,tip,chord,twist=twist,theta=phase,**kw)
    return Mesh.merged(base.rotated((0,0,0),(1,0,0),360*i/count) for i in range(count))

def perforated_liner(x0,x1,r0,r1,thickness,rows=16,cells=72,
                     theta0=0.,theta1=TAU,hole_fraction=(.36,.34)):
    """Real open elliptical holes and bore walls, with welded tile perimeters."""
    n=max(1,round(cells*(theta1-theta0)/TAU));dx=(x1-x0)/rows;dt=(theta1-theta0)/n
    vs=[];fs=[];lookup={}
    def vertex(x,t,r):
        p=polar(x,r,t);key=tuple(round(a,11) for a in p)
        if key not in lookup:lookup[key]=len(vs);vs.append(p)
        return lookup[key]
    def face(ids,normal):
        a,b,c,d=ids
        if dot(cross(sub(vs[b],vs[a]),sub(vs[c],vs[a])),normal)<0:a,b,c,d=d,c,b,a
        fs.extend(((a,b,c),(a,c,d)))
    outer=[(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]
    for j in range(rows):
        xc=x0+(j+.5)*dx
        for k in range(n):
            tc=theta0+(k+.5)*dt;ids=[]
            for layer in (0,1):
                level=[]
                for is_hole in (False,True):
                    loop=[]
                    for a,b in outer:
                        if is_hole:
                            norm=math.hypot(a,b);a=a/norm*hole_fraction[0];b=b/norm*hole_fraction[1]
                        x=xc+a*dx/2;t=tc+b*dt/2
                        r=r0+(r1-r0)*(x-x0)/(x1-x0)+layer*thickness
                        loop.append(vertex(x,t,r))
                    level.append(loop)
                ids.append(level)
            for s in range(8):
                q=(s+1)%8
                for layer in (0,1):
                    face((ids[layer][0][s],ids[layer][0][q],ids[layer][1][q],ids[layer][1][s]),
                         mul(radial(tc),1 if layer else -1))
                a,b=outer[s];c,d=outer[q];xm=(a+c)/2;tm=(b+d)/2
                face((ids[0][1][s],ids[0][1][q],ids[1][1][q],ids[1][1][s]),
                     add((-xm,0,0),mul(tangent(tc),-tm)))
                edge=(j==0 and s in (6,7)) or (j==rows-1 and s in (2,3))
                edge=edge or (theta1-theta0<TAU-1e-8 and
                    ((k==0 and s in (0,1)) or (k==n-1 and s in (4,5))))
                if edge:
                    face((ids[0][0][s],ids[0][0][q],ids[1][0][q],ids[1][0][s]),
                         add((xm,0,0),mul(tangent(tc),tm)))
    return Mesh(vs,fs)

def curved_plate(profile,theta,width,thickness=.004,columns=4):
    return annulus([(x,r-thickness/2,r+thickness/2) for x,r in profile],
        theta-width/2,theta+width/2,max(12,round(columns*TAU/width)))

def chamfer_box(center,size,chamfer=.012):
    x,y,z=center;dx,dy,dz=[s/2 for s in size];c=min(chamfer,dx*.4,dy*.4)
    pts=[(x-dx+c,y-dy,z-dz),(x+dx-c,y-dy,z-dz),(x+dx,y-dy+c,z-dz),
         (x+dx,y+dy-c,z-dz),(x+dx-c,y+dy,z-dz),(x-dx+c,y+dy,z-dz),
         (x-dx,y+dy-c,z-dz),(x-dx,y-dy+c,z-dz)]
    return prism(pts,(0,0,2*dz))

class Engine:
    def __init__(self,scene,side,y,z,exit_x,parent):
        self.scene=scene;self.side=side;self.origin=(exit_x-LENGTH,y,z)
        self.prefix=side+' F404';self.parent=parent;self.mounts=self.comp('mounts')
    def comp(self,label):return self.prefix+' '+label
    def world(self,p):return add(p,self.origin)
    def put(self,label,name,mat,mesh,count=1):
        return self.scene.add(self.comp(label),name,mat,mesh.translated(self.origin),count)
    def fixed(self,label):
        self.scene.fixed(self.comp(label+' attachment'),self.mounts,self.comp(label))
    def spin(self,label,joint):
        self.scene.joint(self.comp(joint),self.mounts,self.comp(label),self.origin,(1,0,0),(-36000,36000),0)
    def slide(self,label,direction,limit=.6):
        self.scene.joint(self.comp(label+' inspection extraction'),self.mounts,self.comp(label),
                         self.origin,direction,(0,limit),0,'slider')

def build_mounts(e):
    frames=[];hardware=[]
    for u,r in ((.735,.350),(2.298,.365)):
        frames.append(ring(u,r-.009,r+.013,.021))
        for th in (math.radians(38),math.radians(142),math.radians(270)):
            p=polar(u,r+.013,th);q=polar(u,r+.055,th)
            frames.append(cylinder(p,q,.018,16))
            hardware.append(cylinder(add(q,(-.035,0,0)),add(q,(.035,0,0)),.015,16))
            hardware.append(cylinder(add(q,(-.039,0,0)),add(q,(-.035,0,0)),.021,6))
    e.put('mounts','Front and rear mounting frame rings and trunnions','engine_titanium_case',Mesh.merged(frames),8)
    e.put('mounts','Mounting pin heads','engine_steel',Mesh.merged(hardware),12)
    e.scene.fixed(e.comp('airframe engine mount'),e.parent,e.mounts)

def build_spools(e):
    lp='LP spool';hp='HP spool'
    e.put(lp,'Continuous N1 inner shaft','engine_steel',cylinder((.09,0,0),(2.325,0,0),.0305,48))
    e.put(hp,'Hollow N2 concentric shaft','engine_steel',
          annulus([(.775,.038,.055),(1.96,.038,.055),(2.05,.038,.049)],segments=64))
    e.put(lp,'Fan inlet ogive and hub drum','engine_titanium',
          annulus([(.002,.001,.004),(.040,.001,.047),(.105,.028,.086),(.15,.031,.102),
                   (.27,.031,.108),(.34,.031,.129),(.47,.031,.139),(.53,.031,.154),
                   (.68,.031,.166)],segments=96))
    e.put(lp,'Spinner retaining fasteners','engine_steel',bolt_circle(.151,.089,12,.0035,.009),12)
    for idx,st in enumerate(FAN_STAGES,1):
        u=st['u'];root=st['hub'];cnt=st['count']
        e.put(lp,f'Fan stage {idx:02d} twisted titanium blades','engine_titanium',
              blade_row(u,root,st['tip'],st['chord'],cnt,st['twist'],phase=idx*.10,
                        thickness=.072,camber=.020,sweep=.018,lean=.052),cnt)
        e.put(lp,f'Fan stage {idx:02d} disk web and root platforms','engine_titanium',
              Mesh.merged([annulus([(u-.036,.031,root-.019),(u-.015,.031,root+.003),
                                   (u+.025,.031,root+.003),(u+.043,.031,root-.018)],segments=96),
                           bolt_circle(u-.037,root-.024,24,.0035,.010)]),25)
    for idx,st in enumerate(HPC_STAGES,1):
        u=st['u'];root=st['hub'];cnt=st['count'];mat='engine_titanium' if idx<5 else 'engine_nickel_proxy'
        e.put(hp,f'HPC stage {idx:02d} twisted compressor blades',mat,
              blade_row(u,root,st['tip'],st['chord'],cnt,st['twist'],phase=idx*.078,
                        thickness=.070,camber=.027,sweep=.010,lean=.035),cnt)
        e.put(hp,f'HPC stage {idx:02d} annular disk and stepped drum',mat,
              annulus([(u-.038,.056,root-.018),(u-.018,.056,root+.003),
                       (u+.025,.056,root+.003),(u+.045,.056,root-.012)],segments=72))
    for st in TURBINE_STAGES:
        label=hp if st['name']=='HPT' else lp;u=st['u'];hub=st['hub'];ri=.050 if label==hp else .031
        e.put(label,st['name']+' single turbine rotor curved airfoils','engine_nickel_proxy',
              blade_row(u,hub,st['tip'],st['chord'],st['count'],st['twist'],
                        phase=.035,camber=-.030,thickness=.105,sweep=-.009,lean=-.030),st['count'])
        e.put(label,st['name']+' disk web rim root platforms and fasteners','engine_nickel_proxy',
              Mesh.merged([annulus([(u-.032,ri,hub-.029),(u-.015,ri,hub+.003),
                                   (u+.022,ri,hub+.003),(u+.038,ri,hub-.023)],segments=96),
                           bolt_circle(u-.035,hub-.040,30,.0033,.010)]),31)
    e.put(lp,'Aft shaft drum and turbine tail cone','engine_hot_inner',
          annulus([(2.27,.031,.132),(2.35,.031,.125),(2.46,.020,.088),
                   (2.58,.006,.033),(2.64,.002,.007)],segments=96))
    e.put(lp,'LP shaft splined coupling collars','engine_steel',Mesh.merged([
        ring(.720,.0305,.046,.039,segments=64),ring(2.303,.0305,.044,.035,segments=64)]),2)
    e.put(hp,'HP shaft coupling splines','engine_steel',Mesh.merged(
        tube([polar(.777,.056,i*TAU/24),polar(.827,.056,i*TAU/24)],.0025,6) for i in range(24)),24)
    e.spin(lp,'N1 shaft rotation');e.spin(hp,'N2 shaft rotation')

def build_stators_and_bearings(e):
    label='stators';frames=[];struts=[];controllers={}
    if not hasattr(e.scene,'motion_links'):e.scene.motion_links=[]
    variable_rows={
      'Fan inlet guide vanes':('Fan inlet guide vane','fan variable guide control'),
      'HPC inlet guide vanes':('HPC inlet guide vane','HPC variable guide control'),
      'HPC stage 01 stators':('HPC stage 01 variable stator','HPC variable guide control'),
      'HPC stage 02 stators':('HPC stage 02 variable stator','HPC variable guide control'),
    }
    defs=[('Fan inlet guide vanes',.082,.090,.352,.071,24,(9,5),.0),
          ('Fan stage 1 stators',.318,.120,.350,.072,36,(-36,-16),.03),
          ('Fan stage 2 stators',.503,.149,.344,.064,40,(-35,-14),.06),
          ('Fan outlet guide vanes',.702,.171,.333,.071,44,(-28,-10),.09),
          ('HPC inlet guide vanes',.797,.164,.260,.041,34,(-30,-17),.01)]
    for i,st in enumerate(HPC_STAGES):
        defs.append((f'HPC stage {i+1:02d} stators',st['u']+.048,st['hub']+.003,
                     st['tip']-.002,st['chord']*.62,40+i*2,(-38+i,-21+i),.05*i))
    defs.extend([('HPT nozzle guide vanes',1.969,.161,.253,.061,40,(48,28),.05),
                 ('LPT nozzle guide vanes',2.142,.147,.283,.075,48,(46,25),.0)])
    for name,u,root,tip,chord,cnt,twist,phase in defs:
        mat='engine_titanium' if u<1.18 else 'engine_nickel_proxy'
        kw=dict(thickness=.095,camber=.022 if twist[0]>0 else -.022,
                sweep=0,lean=.008,spans=5,samples=15)
        if name in variable_rows:
            stem,controller=variable_rows[name];arm=(tip+.022)/12
            controllers[controller]=True
            e.put(controller,name+' moving control ring','engine_steel',
                  torus((u+arm,0,0),tip+.022,.0035,axis=(1,0,0),segments=96,sides=8))
            for vi in range(cnt):
                th=phase+TAU*vi/cnt;vlabel=f'{stem} {vi+1:02d}'
                e.put(vlabel,'Individually pitchable cambered airfoil',mat,
                      blade(u,root,tip,chord,twist,theta=th,**kw))
                shaft=cylinder(polar(u,tip-.006,th),polar(u,tip+.022,th),.004,12)
                lever=tube([polar(u,tip+.022,th),polar(u+arm,tip+.022,th)],.0035,8)
                e.put(vlabel,'Radial spindle and pitch lever','engine_steel',Mesh.merged([shaft,lever]),2)
                e.scene.joint(e.comp(vlabel+' pitch'),e.comp(label),e.comp(vlabel),
                              e.world(polar(u,root,th)),radial(th),(-9,9),0)
                e.scene.motion_links.append(dict(a=e.comp(controller+' drive'),
                    b=e.comp(vlabel+' pitch'),ratio=12.,offset=0.))
        else:
            e.put(label,name+' cambered airfoils',mat,
                  blade_row(u,root,tip,chord,cnt,twist,phase=phase,**kw),cnt)
        frames.extend((ring(u,tip-.003,tip+.0035,.009,segments=96),
                       ring(u,root-.003,root+.003,.008,segments=72)))
    for u,inner,outer,cnt in ((.747,.075,.340,8),(2.322,.070,.320,10)):
        struts.append(blade_row(u,inner,outer,.083,cnt,(0,0),thickness=.16,
                               camber=0,sweep=0,lean=0,spans=4,samples=13))
        frames.extend((ring(u,.061,.078,.038,segments=64),
                       ring(u,outer-.004,outer+.008,.025,segments=96)))
    e.put(label,'Thin vane shroud rings and frame hubs','engine_nickel_proxy',Mesh.merged(frames),len(frames))
    e.put(label,'Fan frame and turbine exit frame aerodynamic struts','engine_titanium',Mesh.merged(struts),18)
    e.fixed(label)
    for controller in controllers:
        e.scene.joint(e.comp(controller+' drive'),e.comp(label),e.comp(controller),
                      e.origin,(1,0,0),(-.75,.75),0)
    races=[];balls=[];cages=[]
    # No bearing/sump is placed between the combustor and turbines.
    for u,ri,ro,count in ((.748,.0315,.068,18),(.806,.056,.083,22),
                         (1.495,.056,.082,22),(2.322,.0315,.065,18)):
        ballr=(ro-ri)*.22;mid=(ri+ro)/2
        races.extend((annulus([(u-.014,ri,ri+.006),(u+.014,ri,ri+.006)],segments=72),
                      annulus([(u-.014,ro-.006,ro),(u+.014,ro-.006,ro)],segments=72)))
        for k in range(count):balls.append(sphere(polar(u,mid,TAU*k/count),ballr,12,7))
        cages.extend((torus((u-.009,0,0),mid,.0025,axis=(1,0,0),segments=72,sides=6),
                      torus((u+.009,0,0),mid,.0025,axis=(1,0,0),segments=72,sides=6)))
    e.put('bearing supports','Concentric bearing inner and outer races','engine_steel',Mesh.merged(races),8)
    e.put('bearing supports','Visible rolling elements','engine_steel',Mesh.merged(balls),80)
    e.put('bearing supports','Bearing cages and separators','engine_copper',Mesh.merged(cages),8)
    e.fixed('bearing supports')


def build_combustor(e):
    injectors=[];feeds=[];swirl=[];hardware=[]
    injector_count=18  # authored repetition; no exact -402 injector count claimed
    # Map an actually perforated cylinder to a flat annular dome. The coordinate
    # exchange reverses handedness, so reverse triangle winding after mapping.
    d=perforated_liner(.134,.257,.001,.001,.005,rows=1,cells=injector_count,
                       hole_fraction=(.21,.53))
    dome=Mesh([(1.538+math.hypot(y,z)-.001,x*math.cos(math.atan2(z,y)),
                x*math.sin(math.atan2(z,y))) for x,y,z in d.vertices],
              [(a,c,b) for a,b,c in d.faces])
    e.put('combustor injectors','Annular dome with real injector apertures',
          'engine_nickel_proxy',dome,injector_count)
    diffuser=annulus([(1.475,.188,.193),(1.510,.160,.165),(1.538,.134,.139)],segments=96)
    outerdiff=annulus([(1.475,.215,.220),(1.510,.244,.249),(1.538,.257,.262)],segments=96)
    e.put('combustor injectors','Open annular inner and outer diffuser walls',
          'engine_nickel_proxy',Mesh.merged([diffuser,outerdiff]),2)
    for i in range(injector_count):
        th=TAU*(i+.5)/injector_count;p=polar(1.538,.1955,th)
        injectors.extend((cylinder(add(p,(-.032,0,0)),add(p,(.020,0,0)),.009,16),
                          annulus([(1.538,.004,.014),(1.555,.005,.012)],segments=32).translated((0,p[1],p[2]))))
        hardware.append(torus((1.535,p[1],p[2]),.015,.0027,axis=(1,0,0),segments=24,sides=6))
        # Open swirl-cup vanes; appearance only, without nozzle drilling/flow data.
        for k in range(8):
            a=TAU*k/8
            q1=(1.552,p[1]+.005*math.cos(a),p[2]+.005*math.sin(a))
            q2=(1.554,p[1]+.011*math.cos(a+.3),p[2]+.011*math.sin(a+.3))
            swirl.append(cylinder(q1,q2,.00125,6))
        feeds.append(tube([polar(1.50,.282,th),polar(1.50,.235,th),
                           polar(1.508,.208,th),add(p,(-.029,0,0))],.0035,8))
    e.put('combustor injectors','Fuel injector external cups and stems','engine_steel',Mesh.merged(injectors),36)
    e.put('combustor injectors','Injector swirl cup visible vanes','engine_nickel_proxy',Mesh.merged(swirl),144)
    e.put('combustor injectors','Injector retaining collars','engine_heat_bronze',Mesh.merged(hardware),18)
    e.put('combustor injectors','Fuel distribution ring and individual feed tubes','engine_steel',
          Mesh.merged(feeds+[torus((1.50,0,0),.282,.006,axis=(1,0,0),segments=96,sides=8)]),19)
    e.fixed('combustor injectors')
    for q in range(4):
        t0=q*math.pi/2;t1=(q+1)*math.pi/2;label=f'combustor liner Q{q+1}'
        outer=perforated_liner(1.553,1.913,.255,.249,.0025,rows=12,cells=72,theta0=t0,theta1=t1,
                              hole_fraction=(.46,.45))
        inner=perforated_liner(1.553,1.913,.135,.158,.0025,rows=12,cells=60,theta0=t0,theta1=t1,
                              hole_fraction=(.40,.40))
        e.put(label,'Outer perforated liner with machined open dilution holes','engine_hot_inner',outer,216)
        e.put(label,'Inner perforated liner with open cooling holes','engine_nickel_proxy',inner,180)
        lips=[]
        for j in range(7):
            u=1.552+j*.0596;r=.255-(u-1.553)/.36*.006
            lips.append(ring(u,r+.0025,r+.006,.007,t0,t1,96))
            ri=.135+(u-1.553)/.36*.023
            lips.append(ring(u,ri-.003,ri,.006,t0,t1,96))
        e.put(label,'Lapped cooling lips and annular reinforcement ribs','engine_heat_bronze',Mesh.merged(lips),14)
        e.slide(label,radial((t0+t1)/2),.48)
    igniters=[];leads=[]
    for th in (math.radians(42),math.radians(138)):
        igniters.extend((cylinder(polar(1.65,.251,th),polar(1.65,.304,th),.011,16),
                         cylinder(polar(1.65,.304,th),polar(1.65,.328,th),.016,6)))
        leads.append(tube([polar(1.65,.331,th),polar(1.70,.351,th),polar(1.84,.355,th),
                           polar(1.91,.353,th+.07)],.0045,10))
    e.put('combustor injectors','Opposed igniter bodies and connector nuts','engine_steel',Mesh.merged(igniters),4)
    e.put('combustor injectors','Igniter shielded lead exteriors','engine_hose',Mesh.merged(leads),2)


def build_afterburner(e):
    label='afterburner internals';bars=[];pilots=[];braces=[];manifolds=[];clips=[]
    # NASA TM 88273 describes 24 main and six pilot bars for the public -400;
    # adopted as a family visualization reference, not a -402 part catalogue.
    for i in range(24):
        th=TAU*i/24
        bars.append(cylinder(polar(2.455,.322,th),polar(2.455,.186,th),.0048,10))
        bars.append(cylinder(polar(2.456,.188,th),polar(2.473,.175,th),.0055,10))
        clips.append(cylinder(polar(2.455,.323,th),polar(2.455,.338,th),.010,6))
    for i in range(6):
        th=TAU*(i+.5)/6
        pilots.append(tube([polar(2.480,.335,th),polar(2.490,.273,th),
                            polar(2.545,.224,th),polar(2.588,.220,th)],.0057,10))
        braces.append(curved_plate([(2.577,.076),(2.620,.076),(2.620,.306),(2.577,.306)],
                                  th,.018,.004,columns=3))
    e.put(label,'Twenty four main afterburner spraybar external forms','engine_nickel_proxy',Mesh.merged(bars),24)
    e.put(label,'Six pilot spraybar external forms','engine_nickel_proxy',Mesh.merged(pilots),6)
    # Annular V-section flameholder, open aft, with swept radial supports.
    vg=Mesh.merged([
        annulus([(2.580,.218,.222),(2.620,.196,.200)],segments=144),
        annulus([(2.580,.218,.222),(2.620,.240,.244)],segments=144)])
    e.put(label,'Open V section annular flameholder','engine_hot_dark',vg)
    supports=[]
    for i in range(6):
        th=TAU*(i+.5)/6
        a=polar(2.594,.082,th);b=polar(2.594,.314,th)
        supports.append(cylinder(a,b,.0065,10))
        supports.append(tube([polar(2.575,.218,th-.025),polar(2.619,.218,th),
                              polar(2.575,.218,th+.025)],.005,8))
    e.put(label,'Flameholder radial stays and V gutter joints','engine_hot_dark',Mesh.merged(supports),12)
    e.put(label,'Spraybar mounting nuts','engine_steel',Mesh.merged(clips),24)
    for u,r in ((2.432,.345),(2.486,.348)):
        manifolds.append(torus((u,0,0),r,.006,axis=(1,0,0),segments=96,sides=8))
    e.put(label,'Separate main and pilot external manifolds','engine_steel',Mesh.merged(manifolds),2)
    # Short serrated mixer lip separates the bypass path from the hot core.
    mixers=[]
    for i in range(36):
        th=TAU*i/36
        mixers.append(curved_plate([(2.295,.317),(2.354,.321),(2.395,.307)],th,TAU/36*.72,.003,3))
    e.put(label,'Bypass mixer cooling lip sectors','engine_nickel_proxy',Mesh.merged(mixers),36)
    e.fixed(label)
    for q in range(4):
        t0=q*math.pi/2;t1=(q+1)*math.pi/2;label=f'afterburner liner Q{q+1}'
        e.put(label,'Open perforated augmentor cooling liner','engine_hot_inner',
              perforated_liner(2.405,3.205,.329,.332,.0028,rows=18,cells=96,theta0=t0,theta1=t1,
                                hole_fraction=(.31,.31)),432)
        ribs=[]
        for i in range(16):
            u=2.409+i*.0525
            ribs.append(ring(u,.332,.337,.004,t0,t1,128))
        e.put(label,'Augmentor liner circumferential stiffening beads','engine_heat_bronze',Mesh.merged(ribs),16)
        e.slide(label,radial((t0+t1)/2),.55)


def build_casings(e):
    # Each quadrant is separately moveable. Inner pressure-shell sectors live
    # with their corresponding outer quadrant so hiding Q1/Q2 opens a true
    # continuous top-half view of rotor rows and bypass passages.
    sections=[
      ('Fan casing',[(0.,.3556,.366),(.15,.355,.367),(.40,.351,.363),(.65,.345,.356),(.739,.338,.350)]),
      ('Outer titanium bypass duct',[(.746,.341,.349),(.86,.340,.348),(1.55,.343,.351),(2.12,.350,.358),(2.302,.354,.364)]),
      ('Core compressor pressure shell',[(.780,.261,.269),(.90,.257,.265),(1.10,.242,.250),(1.30,.229,.237),(1.49,.217,.225)]),
      ('Combustor pressure shell',[(1.50,.278,.285),(1.65,.280,.287),(1.86,.273,.280),(1.932,.261,.270)]),
      ('Turbine containment shell',[(1.94,.255,.272),(2.076,.255,.272),(2.13,.286,.300),(2.28,.291,.308),(2.318,.317,.325)]),
      ('Titanium augmentor outer case',[(2.31,.355,.365),(2.55,.350,.360),(2.95,.345,.354),(3.215,.341,.351)]),
    ]
    flange_specs=[(.022,.368),(.738,.354),(.788,.352),(1.496,.355),(1.934,.361),(2.305,.368),(3.205,.357)]
    for q in range(4):
        t0=q*math.pi/2+.0008;t1=(q+1)*math.pi/2-.0008;label=f'casing Q{q+1}'
        for name,profile in sections:
            e.put(label,name+' hollow removable sector','engine_titanium_case',
                  annulus(profile,t0,t1,144))
        flanges=[];bolts=[];seams=[]
        for u,r in flange_specs:
            flanges.append(ring(u,r-.008,r+.010,.015,t0,t1,144))
            bolts.append(bolt_circle(u-.011,r+.003,48,.005,.021,t0,t1))
        for th in (t0,t1):
            seams.append(tube([polar(.02,.371,th),polar(.74,.355,th)],.004,8))
            seams.append(tube([polar(.79,.353,th),polar(1.50,.357,th),polar(2.30,.369,th)],.004,8))
            seams.append(tube([polar(2.33,.366,th),polar(3.19,.356,th)],.0035,8))
        e.put(label,'Raised joining flanges and seam rails','engine_titanium',Mesh.merged(flanges+seams),13)
        e.put(label,'Flange hex bolts washers and retaining studs','engine_steel',Mesh.merged(bolts),84)
        # Twelve shallow inspection bosses per quadrant stay with their shell.
        bosses=[];fasteners=[]
        for u in (.30,.59,1.03,1.35,1.73,2.04,2.55,2.87,3.10):
            th=(t0+t1)/2;radius=.368 if u<.7 else (.360 if u<2.3 else .362)
            a=polar(u,radius,th);b=polar(u,radius+.006,th)
            bosses.append(cylinder(a,b,.020,24))
            fasteners.append(cylinder(b,add(b,mul(radial(th),.004)),.006,6))
        e.put(label,'External inspection port bosses','engine_titanium',Mesh.merged(bosses),9)
        e.put(label,'Inspection port fastener heads','engine_steel',Mesh.merged(fasteners),9)
        e.slide(label,radial((t0+t1)/2),.85)
    # Data plate belongs to the removable port-side upper case, visible in an
    # engine display. It intentionally contains no invented serial number.
    th=math.radians(136);p=polar(.96,.358,th)
    plate=curved_plate([(.935,.357), (1.17,.357)],th,.29,.002,columns=4)
    e.put('casing Q2','Manufacturer family identification plate','engine_hot_dark',plate)
    e.put('casing Q2','F404 GE 402 identification lettering','white',
          text('F404-GE-402',add(p,(0,-.018,-.018)),.012,right=(1,0,0),up=mul(tangent(th),-1),depth=.0004))
    # Unpainted rolled lips provide distinct thickness at both open ends.
    e.put('mounts','Fan open inlet rolled lip','engine_titanium',
          torus((.008,0,0),.3605,.005,axis=(1,0,0),segments=144,sides=10))


def build_accessories(e):
    label='accessories';housings=[];covers=[];fasteners=[];pipes=[];hoses=[];clamps=[]
    # Bottom-mounted gearbox and accessory external forms; no speculative
    # internal controls or pump engineering is represented.
    housings.append(chamfer_box((1.02,0,-.365),(.45,.22,.112),.025))
    covers.append(chamfer_box((1.02,0,-.423),(.365,.174,.009),.018))
    for u in (.87,1.17):
        for y in (-.073,.073):
            fasteners.append(cylinder((u,y,-.428),(u,y,-.434),.006,6))
    for u,th,length,r in ((1.28,math.radians(252),.20,.033),
                          (.77,math.radians(284),.19,.030),
                          (1.44,math.radians(280),.15,.035),
                          (.93,math.radians(234),.13,.034)):
        a=polar(u,.393,th);b=add(a,(length,0,0))
        housings.append(cylinder(a,b,r,32))
        covers.append(cylinder(add(a,(-.006,0,0)),a,r+.006,32))
        covers.append(cylinder(b,add(b,(.007,0,0)),r+.006,32))
        for k in range(6):
            t=TAU*k/6
            p=add(b,(.009,(r*.72)*math.cos(t),(r*.72)*math.sin(t)))
            fasteners.append(cylinder(p,add(p,(.005,0,0)),.0035,6))
    # Cable/pipe routes are authored readable visual routing and are not a fuel,
    # oil, hydraulic, or electrical installation drawing.
    routes=[
      [(1.01,-.07,-.412),(1.01,-.16,-.367),(1.28,-.22,-.302),(1.51,-.23,-.299)],
      [(1.14,.08,-.408),(1.25,.18,-.354),(1.53,.26,-.270),(1.53,.278,-.05)],
      [(.82,-.06,-.404),(.66,-.14,-.353),(.42,-.20,-.309),(.22,-.19,-.322)],
      [(1.37,.12,-.367),(1.72,.13,-.350),(2.10,.16,-.331),(2.43,.18,-.309)],
      [(1.18,-.12,-.376),(1.51,-.19,-.322),(2.03,-.20,-.321),(2.45,-.19,-.315)],
      [(1.43,.08,-.406),(1.66,.05,-.365),(2.02,.04,-.370),(2.45,.04,-.370),(2.82,.04,-.360)],
    ]
    for i,points in enumerate(routes):
        (pipes if i%2==0 else hoses).append(tube(points,.006 if i<4 else .008,10))
        for p in points[1:-1]:
            clamps.append(torus(p,.009,.0015,axis=(1,0,0),segments=16,sides=6))
    e.put(label,'Bottom accessory gearbox pump and generator external housings','engine_gearbox',Mesh.merged(housings),9)
    e.put(label,'Accessory covers end plates and mounting flanges','engine_steel',Mesh.merged(covers),9)
    e.put(label,'Accessory cover hex fasteners','engine_steel',Mesh.merged(fasteners),28)
    e.put(label,'Formed external metal service pipes','engine_steel',Mesh.merged(pipes),3)
    e.put(label,'Shielded service harness and flexible hose exteriors','engine_hose',Mesh.merged(hoses),3)
    e.put(label,'Harness and tube retaining clamps','engine_steel',Mesh.merged(clamps),len(clamps))
    # A small service cap and bolted inspection cover provide scale at close view.
    e.put(label,'Oil service cap and retaining chain','engine_heat_bronze',Mesh.merged([
        cylinder((1.13,.072,-.397),(1.13,.072,-.421),.017,12),
        tube([(1.13,.09,-.420),(1.155,.105,-.413),(1.182,.099,-.406)],.0018,6)]),2)
    e.fixed(label)


def nozzle_link_records(side):
    """RC3 native coupling units: input slider mm, output hinge degrees."""
    prefix=side+' F404';out=[]
    for i in range(1,13):
        for kind,ratio in (('primary flap',.28),('secondary flap',-.22),
                           ('primary seal',.28),('secondary seal',-.22)):
            out.append(dict(a=prefix+' nozzle actuator travel',
                            b=f'{prefix} {kind} {i:02d} hinge',ratio=ratio,offset=0.))
    return out

def motion_links(sides=('Port','Starboard')):
    links=[link for side in sides for link in nozzle_link_records(side)]
    for side in sides:
        prefix=side+' F404'
        for stem,count,controller in (
          ('Fan inlet guide vane',24,'fan variable guide control'),
          ('HPC inlet guide vane',34,'HPC variable guide control'),
          ('HPC stage 01 variable stator',40,'HPC variable guide control'),
          ('HPC stage 02 variable stator',42,'HPC variable guide control')):
            for i in range(1,count+1):
                links.append(dict(a=prefix+' '+controller+' drive',
                                  b=f'{prefix} {stem} {i:02d} pitch',ratio=12.,offset=0.))
    return links


def build_nozzle(e):
    ringlabel='nozzle actuator ring';stationary='nozzle mechanism'
    # An actually annular moving ring leaves the entire hot gas path open.
    e.put(ringlabel,'Annular nozzle synchronization ring','engine_titanium',
          annulus([(3.120,.365,.387),(3.153,.365,.387)],segments=144))
    e.put(ringlabel,'Synchronization ring flange bolts','engine_steel',
          bolt_circle(3.118,.378,36,.004,.012),36)
    fixedcyl=[];movingrods=[];ends=[];cams=[];guides=[]
    for th in (math.radians(30),math.radians(150),math.radians(270)):
        a=polar(2.830,.381,th);b=polar(3.035,.381,th)
        fixedcyl.extend((cylinder(a,b,.020,24),
                         cylinder(add(a,(-.013,0,0)),a,.025,24)))
        movingrods.extend((cylinder(polar(2.98,.381,th),polar(3.147,.381,th),.009,20),
                           cylinder(polar(3.135,.373,th),polar(3.135,.397,th),.012,16)))
        ends.append(sphere(a,.022,16,9))
    for i in range(12):
        th=TAU*i/12
        # These cam rails exactly follow the authored primary-flap demonstration
        # relation: translating the ring moves its rail under the hinged roller.
        for side in (-1,1):
            path=[]
            for k in range(17):
                travel=-.025+.050*k/16
                angle=math.radians(280*travel)
                dx=.085;dr=.032
                u=3.200+dx*math.cos(angle)-dr*math.sin(angle)-travel
                r=.333+dx*math.sin(angle)+dr*math.cos(angle)
                path.append(polar(u,r,th+side*.025))
            cams.append(tube(path,.004,8))
        guides.append(tube([polar(3.117,.386,th),polar(3.19,.386,th),
                            polar(3.30,.378,th)],.0055,8))
    e.put(stationary,'Three fixed nozzle actuator cylinder bodies','engine_steel',Mesh.merged(fixedcyl+ends),9)
    e.put(ringlabel,'Three telescoping actuator piston rods','engine_steel',Mesh.merged(movingrods),6)
    e.put(ringlabel,'Twelve paired curved follower cam rails','engine_steel',Mesh.merged(cams),24)
    e.put(ringlabel,'Synchronization ring guide fingers','engine_titanium',Mesh.merged(guides),12)
    e.put(stationary,'Nozzle fixed hinge support annulus','engine_nickel_proxy',
          ring(3.200,.329,.350,.027,segments=144))
    e.fixed(stationary)
    e.scene.joint(e.comp('nozzle actuator travel'),e.mounts,e.comp(ringlabel),
                  e.world((3.135,0,0)),(1,0,0),(-.025,.025),0,'slider')
    for i in range(12):
        for is_seal in (False,True):
            th=TAU*(i+.5*is_seal)/12
            typ='seal' if is_seal else 'flap'
            n=i+1;prim=f'primary {typ} {n:02d}';sec=f'secondary {typ} {n:02d}'
            offset=-.006 if is_seal else 0.
            width=math.radians(13.0 if is_seal else 22.0)
            r0=.333+offset;r1=.285+offset;r2=.345+offset
            thick=.0028 if is_seal else .0050
            primary=[(3.200,r0),(3.215,r0-.002),(3.39,r0-.026),(3.540,r1)]
            secondary=[(3.540,r1),(3.56,r1+.0015),(3.80,r2-.019),(LENGTH,r2)]
            e.put(prim,'Convergent articulated plate','engine_hot_inner',
                  curved_plate(primary,th,width,thick,columns=6))
            e.put(sec,'Divergent articulated exterior plate',
                  'engine_heat_bronze' if not is_seal else 'engine_hot_dark',
                  curved_plate(secondary,th,width,thick,columns=7))
            # Separate thin visible hot-face panels are real three-dimensional
            # inserts, with their own thickness, not a dark decal.
            if not is_seal:
                e.put(sec,'Interior heat shield panel','engine_hot_inner',
                      curved_plate([(3.563,r1-.003),(3.79,r2-.024),(LENGTH-.008,r2-.004)],
                                   th,width*.89,.0018,columns=6))
            pins=[];ribs=[];rivets=[]
            pivot=polar(3.200,r0,th);aft=polar(3.540,r1,th)
            half=.023 if is_seal else .042
            pins.append(cylinder(add(pivot,mul(tangent(th),-half)),
                                 add(pivot,mul(tangent(th),half)),.006 if is_seal else .009,16))
            pins.append(cylinder(add(aft,mul(tangent(th),-half)),
                                 add(aft,mul(tangent(th),half)),.0055 if is_seal else .008,16))
            if not is_seal:
                for t in (th-width*.32,th+width*.32):
                    ribs.append(tube([polar(3.58,r1+.012,t),polar(3.78,r2-.012,t),
                                      polar(LENGTH-.016,r2+.007,t)],.004,8))
                    for u,r in ((3.60,r1+.014),(3.72,r1+.032),(3.85,r2-.004),(LENGTH-.026,r2+.007)):
                        a=polar(u,r,t);rivets.append(cylinder(a,add(a,mul(radial(t),.003)),.003,10))
                roller=polar(3.285,.365,th)
                arm=Mesh.merged([cylinder(polar(3.235,r0+.003,th),roller,.007,12),
                    cylinder(add(roller,mul(tangent(th),-.014)),
                             add(roller,mul(tangent(th),.014)),.008,20)])
                e.put(prim,'Hinge follower lever and cam roller','engine_steel',arm,2)
            e.put(prim,'Forward and throat hinge pin hardware','engine_steel',Mesh.merged(pins),2)
            if ribs:e.put(sec,'Longitudinal raised stiffening ribs','engine_nickel_proxy',Mesh.merged(ribs),2)
            if rivets:e.put(sec,'Heat shield retaining rivets','engine_steel',Mesh.merged(rivets),8)
            # Narrow heat tint bands have actual shallow thickness. Alternating
            # warm/cool panels avoid the old uniform painted exhaust look.
            e.put(sec,'Subtle trailing heat tint band',
                  'engine_heat_blue' if n%3==0 else 'engine_nickel_proxy',
                  curved_plate([(LENGTH-.045,r2-.0067),(LENGTH-.012,r2-.0001)],
                               th,width*.94,.0012,columns=6))
            e.scene.joint(e.comp(prim+' hinge'),e.mounts,e.comp(prim),
                          e.world(pivot),tangent(th),(-7,7),0)
            e.scene.joint(e.comp(sec+' hinge'),e.comp(prim),e.comp(sec),
                          e.world(aft),tangent(th),(-5.5,5.5),0)
    if not hasattr(e.scene,'motion_links'):e.scene.motion_links=[]
    e.scene.motion_links.extend(nozzle_link_records(e.side))


def build(scene,parent='Airframe',centres=DEFAULT_CENTRES,exit_x=DEFAULT_EXIT_X):
    """Build both complete engines; append real native joint/motion-link records."""
    for key,value in ENGINE_MATERIALS.items():scene.materials.setdefault(key,value)
    sides=('Port','Starboard')
    for side,(y,z) in zip(sides,centres):
        e=Engine(scene,side,y,z,exit_x,parent)
        build_mounts(e)
        build_spools(e)
        build_stators_and_bearings(e)
        build_combustor(e)
        build_afterburner(e)
        build_casings(e)
        build_accessories(e)
        build_nozzle(e)
    scene.notes.extend([
      'F404 geometry: GE family datasheet -402 overall 154 in length, 28 in inlet diameter, 35 in maximum envelope; source inches converted to metres.',
      'Both F404 assemblies contain three fan stages, seven HPC stages, one HPT and one LPT; N1 fan/LPT and N2 HPC/HPT are separate concentric native revolute assemblies.',
      'Engine blade counts, profiles, internal stations, bearings, accessory routing and small hardware are original visual approximations; not production drawings or engineering tolerances.',
      'The 12-sector nozzle uses primary/divergent flap hinges and interleaved seals, mechanically coupled in native RC3 to a common slider; its ±25 mm demonstration stroke and linear ratios are authored, not an engine operating schedule.',
      'Engine combustor and afterburner liner holes are open three-dimensional bores. Casing and liner quadrant sliders permit physical inspection cutaways.',
      'Fan inlet and HPC inlet/first two stator rows contain individually pitchable guide vanes, coupled to fan and HPC control-ring drives. Vane counts and the 12:1 demonstration ratio are authored visual parameters.',
      'Titanium is assigned where public family references support it. Built-in Stainless Steel is the closest available hot-section alloy proxy; no Nickel or Inconel built-in material exists in verified RC3.',
      'This is an articulated visual engine assembly. Rotation and nozzle kinematics do not simulate combustion, thrust, gas dynamics, engine controls, or engineering performance.',
    ])
    return {'length_m':LENGTH,'front_x_m':exit_x-LENGTH,'exit_x_m':exit_x,
            'maximum_envelope_diameter_m':MAX_DIAMETER,'centres':centres,
            'fan_stages':3,'hpc_stages':7,'hpt_stages':1,'lpt_stages':1,
            'nozzle_sectors':12,'motion_links':motion_links()}
