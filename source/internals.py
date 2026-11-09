"""Original Legacy Hornet structural and equipment reconstruction, revision 2.

Metres; +X aft, +Y starboard, +Z up. Architecture is reference based; unpublished
station dimensions, wall gauges, equipment routing and fastener counts are authored
visual estimates. Nothing here is an aircraft manufacturing or servicing drawing.
"""
from __future__ import annotations
import math
from scene_api import *
from aircraft import stations, body_loft, airfoil, fastener

PI=math.pi
CENTRE=[(6.95,.84,2.18,.67,.65),(8.1,1.,2.14,.66,.65),
        (9.7,1.08,2.10,.62,.62),(11.5,1.04,2.10,.52,.62),
        (13.4,1.03,2.10,.43,.59),(14.6,1.05,2.08,.34,.55),
        (15.7,.92,2.07,.30,.50),(16.05,.80,2.06,.26,.44)]
NACELLE=[(6.15,.38,1.97,.40,.46),(6.6,.49,1.96,.46,.48),
         (8.,.57,1.93,.56,.56),(10.8,.58,1.93,.54,.56),
         (13.6,.54,1.96,.49,.50),(15.6,.51,1.99,.46,.46),
         (16.06,.465,1.98,.465,.465)]
NOSE=[(1.855,.54,2.24,.44,.36),(2.5,.58,2.29,.49,.41),(3.35,.65,2.32,.57,.49)]
COCKPIT=[(3.35,.65,2.32,.57,.49),(3.65,.67,2.32,.61,.50),
         (4.2,.70,2.31,.64,.51),(5.,.71,2.28,.68,.55),
         (6.1,.74,2.24,.69,.59),(6.6,.79,2.21,.68,.63),(6.95,.84,2.18,.67,.65)]
DUCT=[(6.08,.422,1.98,.402,1.),(6.5,.405,2.00,.39,.80),
      (7.4,.367,2.055,.345,.30),(8.4,.335,2.11,.32,0.),
      (9.7,.323,2.12,.315,0.),(10.06,.324,2.12,.316,0.),
      (10.25,.324,2.17,.266,0.),(10.55,.325,2.17,.266,0.),
      (10.74,.326,2.12,.318,0.),(11.45,.328,2.12,.32,0.),
      (12.7684,.3556,1.98,.3556,0.)]

def sample(rows,x):
    if x<=rows[0][0]:return rows[0]
    if x>=rows[-1][0]:return rows[-1]
    for a,b in zip(rows,rows[1:]):
        if a[0]<=x<=b[0]:
            t=(x-a[0])/(b[0]-a[0]);return tuple(aa+(bb-aa)*t for aa,bb in zip(a,b))
    raise ValueError(x)

def ellipse_point(rows,x,t,inset=0,cy=0):
    _,w,z,hu,hd=sample(rows,x)[:5];c=math.cos(t)
    return (x,cy+(w-inset)*math.sin(t),z+((hu if c>=0 else hd)-inset)*c)

def envelope(x,t,inset=0):
    """Outer boundary of the union of centre body and twin nacelles.

    A single skin replaces the old mutually intersecting solid lofts. This leaves
    clear, continuous space for both engines instead of skins through their cores.
    """
    _,w,z,hu,hd=sample(CENTRE,x);_,nw,nz,nu,nd=sample(NACELLE,x)
    dy,dz=math.sin(t),math.cos(t);hits=[]
    for cy,cz,rw,up,down in ((0,z,w,hu,hd),(-.71,nz,nw,nu,nd),(.71,nz,nw,nu,nd)):
        for rh,sgn in ((up,1),(down,-1)):
            A=dy*dy/(rw*rw)+dz*dz/(rh*rh)
            B=-2*dy*cy/(rw*rw)+2*dz*(z-cz)/(rh*rh)
            C=cy*cy/(rw*rw)+(z-cz)**2/(rh*rh)-1
            disc=B*B-4*A*C
            if disc>=0:
                r=(-B+math.sqrt(disc))/(2*A)
                if r>0 and sgn*(z+r*dz-cz)>=-1e-9:hits.append(r)
    r=max(hits)-inset
    return (x,r*dy,z+r*dz)

def parametric_shell(xs,ts,point,thickness=.006,mask=None):
    """Closed thin shell with real openings and flat-shaded opening edges."""
    nx,nt=len(xs),len(ts);v=[];f=[];active=set()
    for inner in (False,True):
        for x in xs:
            for t in ts:v.append(point(x,t,thickness if inner else 0))
    n=nx*nt
    for i in range(nx-1):
        for j in range(nt-1):
            if mask and mask((xs[i]+xs[i+1])/2,(ts[j]+ts[j+1])/2):continue
            active.add((i,j));a=i*nt+j;b=(i+1)*nt+j;c=b+1;d=a+1
            # X tangent cross increasing-theta tangent points outward.
            f.extend([(a,b,c),(a,c,d),(a+n,c+n,b+n),(a+n,d+n,c+n)])
    edges={}
    for i,j in active:
        a=i*nt+j;b=(i+1)*nt+j;c=b+1;d=a+1
        for e in ((a,b),(b,c),(c,d),(d,a)):
            key=tuple(sorted(e))
            if key in edges:del edges[key]
            else:edges[key]=e
    for a,b in edges.values():
        o=len(v);v.extend((v[a],v[a+n],v[b+n],v[b]));f.extend([(o,o+1,o+2),(o,o+2,o+3)])
    return Mesh(v,f)

def sequence(a,b,step):
    n=max(1,math.ceil(abs(b-a)/step));return [a+(b-a)*i/n for i in range(n+1)]

def remove_bodies(s,predicate):
    dead=[b for b in s.bodies if predicate(b)]
    names={b['name'] for b in dead};s.bodies=[b for b in s.bodies if b['name'] not in names]
    for c in s.components.values():c['parts']=[b for b in c['parts'] if b['name'] not in names]
    s._names-=names

def move_body(s,b,component):
    s.components[b['component']]['parts'].remove(b)
    if component not in s.components:s.components[component]={'name':component,'slug':slug(component),'category':'aircraft','parts':[]}
    b['component']=component;s.components[component]['parts'].append(b)

def mount(s,component,parent='Airframe'):
    if component in s.components and component!=parent and not any(j['child']==component for j in s.joints):
        s.fixed(component+' attachment',parent,component)

def flat_ring(center,normal,outer,inner,depth=.006,segments=64):
    u,v,w=basis(normal);ps=[];fs=[]
    for offset in (-depth/2,depth/2):
        for r in (outer,inner):
            for j in range(segments):
                a=2*PI*j/segments;ps.append(add(center,add(mul(w,offset),add(mul(u,r*math.cos(a)),mul(v,r*math.sin(a))))))
    n=segments
    for j in range(n):
        k=(j+1)%n
        for a,b,c,d in ((j,k,2*n+k,2*n+j),(n+j,3*n+j,3*n+k,n+k),
                         (j,n+j,n+k,k),(2*n+j,2*n+k,3*n+k,3*n+j)):
            fs.extend(((a,b,c),(a,c,d)))
    return Mesh(ps,fs)

def rect_hole_cell(center,u,v,width,height,hole_w,hole_h,thick=.004):
    """A closed rectangular web cell with an elliptical through-lightening hole."""
    u=unit(u);v=unit(v);w=unit(cross(u,v));verts=[];faces=[];n=32
    for side in (-1,1):
        for inner in (False,True):
            for i in range(n):
                t=2*PI*i/n;c,ss=math.cos(t),math.sin(t)
                if inner:a,b=hole_w/2*c,hole_h/2*ss
                else:
                    k=min(width/2/max(1e-12,abs(c)),height/2/max(1e-12,abs(ss)));a,b=k*c,k*ss
                verts.append(add(center,add(add(mul(u,a),mul(v,b)),mul(w,side*thick/2))))
    for i in range(n):
        j=(i+1)%n
        for a,b,c,d in ((i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                         (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)):
            faces.extend(((a,b,c),(a,c,d)))
    return Mesh(verts,[(a,c,b) for a,b,c in faces])

def perforated_beam(a,b,height=.085,thickness=.004,holes=6,flange=.026):
    d=sub(b,a);u=unit(d);w=unit(cross(u,(0,0,1)));v=unit(cross(w,u));L=length(d)
    parts=[]
    for i in range(holes):
        c=add(a,mul(d,(i+.5)/holes));width=L/holes
        parts.append(rect_hole_cell(c,u,v,width,height,width*.65,height*.56,thickness))
    for sign in (-1,1):
        c=add(a,mul(v,sign*height/2));ps=[add(c,mul(w,-flange/2)),add(add(c,d),mul(w,-flange/2)),add(add(c,d),mul(w,flange/2)),add(c,mul(w,flange/2))]
        parts.append(prism(ps,mul(v,.004*sign)))
    return Mesh.merged(parts)

def replace_skins(s):
    targets={'Forward nose skin','Cockpit aperture skin','Aft spine and centre fuselage',
             'Port lower engine fairing','Starboard lower engine fairing',
             'Port dark recessed intake duct','Starboard dark recessed intake duct',
             'Port intake shadow','Starboard intake shadow','Nose gear bay dark cavity',
             'Port main bay recess','Starboard main bay recess'}
    remove_bodies(s,lambda b:b['label'] in targets)
    # Radome is a removable dielectric shell, not a filled cone.
    rr=[(.03,.015,1.78,.018,.016),(.35,.22,1.86,.20,.18),(.9,.42,2.05,.35,.28),(1.7,.53,2.21,.43,.35),(1.85,.54,2.24,.44,.36)]
    for b in s.bodies:
        if b['label']=='Radome composite shell':
            b['mesh']=parametric_shell(sequence(.03,1.85,.045),sequence(0,2*PI,.065),lambda x,t,o:ellipse_point(rr,x,t,min(o,.005)),.005)
    for label,a,b in [('upper',-PI/2,PI/2),('port lower',PI,1.5*PI),('starboard lower',PI/2,PI)]:
        comp='Nose '+label+' skins'
        s.add(comp,'Removable forward shell','skin',parametric_shell(sequence(1.855,3.35,.06),sequence(a,b,.075),lambda x,t,o:ellipse_point(NOSE,x,t,o)))
        mount(s,comp)
    # Cabin shell has both the canopy aperture and an open nose-wheel bay.
    gaps=[(3.35,.01),(3.65,.50),(4.2,.66),(5.,.68),(6.1,.65),(6.6,.48),(6.95,.01)]
    for side,label in ((-1,'Port'),(1,'Starboard')):
        a,b=(PI,2*PI) if side<0 else (0,PI)
        def cabin_point(x,t,o):
            g=sample(gaps,x)[1]
            theta=PI+(PI-g)*(t-PI)/PI if side<0 else g+(PI-g)*t/PI
            return ellipse_point(COCKPIT,x,theta,o)
        def cabin_mask(x,t):
            p=cabin_point(x,t,0)
            return (3.35<x<5.66 and abs(p[1])<.295 and p[2]<(2.42 if x<4.10 else 2.065))
        comp=label+' cabin skins'
        s.add(comp,'Thin cockpit lower and side shell','skin',parametric_shell(sequence(3.35,6.95,.065),sequence(a,b,.055),cabin_point,.006,cabin_mask));mount(s,comp)
    # One continuous double-lobed aft envelope, split into removable panels.
    panels=[(6.95,8.35),(8.35,9.95),(9.95,11.75),(11.75,12.77),(12.77,14.08),(14.08,15.20),(15.20,16.055)]
    for label,a,b,mat in [('Dorsal',-PI/2,PI/2,'skin'),('Port lower',PI,1.5*PI,'skin_lower'),('Starboard lower',PI/2,PI,'skin_lower')]:
        comp='Fuselage '+label+' skins'
        for k,(xa,xb) in enumerate(panels):
            def baymask(x,t):
                p=envelope(x,t)
                return 10.02<x<11.74 and .35<abs(p[1])<1.20 and p[2]<1.78
            s.add(comp,f'Removable panel {k+1:02d}','skin' if label=='Dorsal' else mat,
                  parametric_shell(sequence(xa,xb,.07),sequence(a,b,.055),envelope,.006,baymask))
        mount(s,comp)
    # Short inlet fairing sleeves have no caps across the air passages.
    for side,label in ((-1,'Port'),(1,'Starboard')):
        comp=label+' inlet fairing skins'
        s.add(comp,'Inlet transition sleeve','skin_lower',parametric_shell(sequence(6.15,6.95,.05),sequence(0,2*PI,.065),lambda x,t,o:ellipse_point(NACELLE,x,t,o,side*.71),.006));mount(s,comp)
    # Hide exterior annotation together with skin in structural inspection files.
    exterior_words=('Skin panel','Skin flush','stencil','modex','RESCUE','placard','slime light','Cooling louvers')
    for b in list(s.bodies):
        if b['component']=='Airframe' and any(w in b['label'] for w in exterior_words):move_body(s,b,'Exterior markings and skin fasteners')
    mount(s,'Exterior markings and skin fasteners')

def build_ducts(s):
    for side,label in ((-1,'Port'),(1,'Starboard')):
        comp=label+' intake duct'
        def point(x,t,inset):
            _,r,z,h,flat=sample(DUCT,x);ss=math.sin(t)
            yy=side*(.71+(r-inset)*ss)
            if flat>0:yy=side*((1-flat)*(.71+(r-inset)*ss)+flat*max(.356+inset,.71+(r-inset)*ss))
            return (x,yy,z+(h-inset)*math.cos(t))
        # Inner wall remains pale and shaded geometrically; no fake black blocking plate.
        for k,(xa,xb) in enumerate(zip([6.08,7.4,9.7,11.45],[7.4,9.7,11.45,12.7684])):
            m=parametric_shell(sequence(xa,xb,.075),sequence(0,2*PI,.075),lambda x,t,o:point(x,t,o-.005),.005)
            if side<0:m.faces=[(a,c,b) for a,b,c in m.faces]
            s.add(comp,f'Continuous hollow duct segment {k+1}','duct_liner',m)
        ribs=[]
        for x in (6.48,7.20,8.05,9.05,10.10,11.2,12.25,12.755):
            pts=[point(x,2*PI*i/72,-.012) for i in range(73)];ribs.append(tube(pts,.009,8))
        s.add(comp,'Duct exterior stiffening hoops','aluminum',Mesh.merged(ribs),detail_count=len(ribs))
        # Engine-face sleeve leaves a clean open interface of 28 inches diameter.
        s.add(comp,'Fan flange gasket','rubber_seal',torus((12.762,side*.71,1.98),.3605,.006,axis=(1,0,0),segments=80,sides=8))
        mount(s,comp)

def build_frames(s):
    comp='Fuselage frames and longerons';bolts=[]
    for k,x in enumerate([6.98,7.43,7.90,8.38,8.86,9.34,9.82,10.30,10.78,11.26,11.74,12.23,12.75,13.18,13.64,14.10,14.55,15.02,15.50,15.91]):
        rows=sequence(x-.006,x+.006,.02)
        def p(xx,t,o):return envelope(xx,t,.018+o)
        s.add(comp,f'Open circumferential frame {k+1:02d}','primer',parametric_shell(rows,sequence(0,2*PI,.055),p,.042))
        edges=[]
        for inset in (.018,.060):edges.append(tube([envelope(x,2*PI*i/100,inset) for i in range(101)],.008,8))
        s.add(comp,f'Frame {k+1:02d} return flanges','primer',Mesh.merged(edges),detail_count=2)
        for j in range(32):
            t=2*PI*j/32;pp=envelope(x,t,.024);bolts.append(fastener(pp,(1,0,0),.004))
    for j in range(14):
        t=2*PI*j/14;ps=[envelope(x,t,.026) for x in sequence(6.97,15.99,.11)]
        s.add(comp,f'Continuous longeron {j+1:02d}','primer',tube(ps,.016,8))
    s.add(comp,'Frame and longeron attachment fasteners','aluminum',Mesh.merged(bolts),detail_count=len(bolts));mount(s,comp)
    # Open cabin frames stop at the cockpit sill instead of crossing the pilot.
    comp='Forward fuselage structure'
    for k,x in enumerate((1.91,2.42,2.96,3.53,4.13,4.68,5.26,5.84,6.40,6.86)):
        rows=NOSE if x<3.35 else COCKPIT;start,end=(0,2*PI) if x<3.35 else (.72,2*PI-.72)
        p=lambda xx,t,o,rr=rows:ellipse_point(rr,xx,t,.025+o)
        def cut_well(xx,t):
            q=ellipse_point(rows,xx,t,.025)
            return 3.35<xx<5.66 and abs(q[1])<.32 and q[2]<(2.42 if xx<4.10 else 2.065)
        s.add(comp,f'Forward frame {k+1:02d}','primer',parametric_shell([x-.006,x+.006],sequence(start,end,.06),p,.038,cut_well))
    for side in (-1,1):
        for z in (1.96,2.25):
            s.add(comp,f'Cabin rail {side} {z}','primer',tube([(3.45,side*.52,z),(4.4,side*.59,z),(5.5,side*.60,z),(6.7,side*.63,z)],.018,8))
    mount(s,comp)
    # Centre barrel contains the wing attachments and main landing-gear trunnions.
    comp='Center barrel load structure'
    for x in (9.02,9.70,10.42,11.22):
        s.add(comp,f'Dorsal transverse beam {x}','aluminum',perforated_beam((x,-.96,2.50),(x,.96,2.50),.10,.008,8,.042))
        s.add(comp,f'Keel cross member {x}','aluminum',perforated_beam((x,-.92,1.54),(x,.92,1.54),.085,.008,7,.035))
    for side,label in ((-1,'Port'),(1,'Starboard')):
        for x in (9.07,9.75,10.43,11.21):
            c=(x,side*1.08,2.49)
            s.add(comp,f'{label} wing attachment lug {x}','aluminum',flat_ring(c,(1,0,0),.074,.028,.06,32))
            s.add(comp,f'{label} wing attachment bolt {x}','steel',cylinder(add(c,(-.046,0,0)),add(c,(.046,0,0)),.025,16))
        s.add(comp,label+' main gear trunnion block','aluminum',box((10.40,side*.74,1.78),(.22,.30,.14)))
    mount(s,comp)

def wing_sections(side,outer=False):
    return [(side*3.77,10.25,11.72,2.46,.051),(side*5.715,11.26,12.23,2.40,.047)] if outer else [(side*1.10,8.86,11.47,2.54,.054),(side*3.74,10.24,11.72,2.46,.051)]

def wing_value(rows,y,u):
    t=(y-rows[0][0])/(rows[-1][0]-rows[0][0]);r=[a+(b-a)*t for a,b in zip(rows[0],rows[-1])]
    yy,le,te,z,tr=r;c=te-le;h=5*tr*c*(.2969*math.sqrt(max(0,u))-.126*u-.3516*u*u+.2843*u**3-.1036*u**4)
    return le+c*u,yy,z,h

def wing_skin(rows,upper=True):
    # A real 3 mm composite shell, with no solid interior blocking ribs.
    vs=[];fs=[];ny=35;nc=36;sgn=1 if upper else -1
    for layer in (0,1):
        for j in range(ny+1):
            y=rows[0][0]+(rows[-1][0]-rows[0][0])*j/ny
            for i in range(nc+1):
                u=.006+.988*(.5-.5*math.cos(PI*i/nc));x,yy,z,h=wing_value(rows,y,u)
                outer=max(.001,h);inner=max(.00010,outer-.003)
                vs.append((x,yy,z+sgn*(inner if layer else outer)))
    n=(ny+1)*(nc+1);edges={}
    for j in range(ny):
        for i in range(nc):
            a=j*(nc+1)+i;b=a+1;c=b+nc+1;d=a+nc+1
            # Chord X cross span Y = Z; port span runs negative.
            if (rows[-1][0]-rows[0][0])*sgn>0:face=(a,b,c,d)
            else:face=(a,d,c,b)
            aa,bb,cc,dd=face;fs.extend(((aa,bb,cc),(aa,cc,dd),(aa+n,cc+n,bb+n),(aa+n,dd+n,cc+n)))
            for e in ((aa,bb),(bb,cc),(cc,dd),(dd,aa)):
                key=tuple(sorted(e))
                if key in edges:del edges[key]
                else:edges[key]=e
    for a,b in edges.values():
        o=len(vs);vs.extend((vs[a],vs[a+n],vs[b+n],vs[b]));fs.extend(((o,o+1,o+2),(o,o+2,o+3)))
    return Mesh(vs,fs)

def build_wing_structure(s):
    for side,label in ((-1,'Port'),(1,'Starboard')):
        for outer in (False,True):
            rows=wing_sections(side,outer);parent=label+' outer wing' if outer else 'Airframe'
            prefix=label+(' outer wing' if outer else ' inner wing')
            remove_bodies(s,lambda b:b['label']==prefix)
            for upper in (False,True):
                comp=prefix+(' upper skin' if upper else ' lower skin')
                s.add(comp,'Composite skin with finite wall','composite',wing_skin(rows,upper));mount(s,comp,parent)
            comp=prefix+' internal structure';n=9 if outer else 12
            y0,y1=rows[0][0],rows[-1][0]
            for k in range(n):
                y=y0+(y1-y0)*(.03+.94*k/(n-1));a=wing_value(rows,y,.06);b=wing_value(rows,y,.94)
                # Ribs follow taper; each has through-holes and upper/lower flanges.
                cells=[];num=6 if outer else 9
                for cell in range(num):
                    ua=.06+.88*cell/num;ub=.06+.88*(cell+1)/num
                    ca=wing_value(rows,y,ua);cb=wing_value(rows,y,ub)
                    height=max(.006,2*min(ca[3],cb[3])-.013)
                    cells.append(perforated_beam(ca[:3],cb[:3],height,.0025,1,.014))
                s.add(comp,f'Lightened rib {k+1:02d}','primer',Mesh.merged(cells),detail_count=num)
            for k,u in enumerate((.12,.29,.46,.63,.80,.92)):
                aa=wing_value(rows,y0,u);bb=wing_value(rows,y1,u)
                # Spanwise spar webs use station heights so they do not pierce skins.
                pieces=[]
                for j in range(n-1):
                    ya=y0+(y1-y0)*j/(n-1);yb=y0+(y1-y0)*(j+1)/(n-1)
                    a=wing_value(rows,ya,u);b=wing_value(rows,yb,u);h=max(.012,2*min(a[3],b[3])-.014)
                    pieces.append(perforated_beam(a[:3],b[:3],h,.004,1,.022))
                s.add(comp,f'Spar {k+1:02d} web and caps','aluminum',Mesh.merged(pieces),detail_count=n-1)
            for u in (.20,.38,.55,.72):
                for sign in (-1,1):
                    points=[]
                    for j in range(31):
                        y=y0+(y1-y0)*j/30;x,yy,z,h=wing_value(rows,y,u);points.append((x,yy,z+sign*max(.001,h-.009)))
                    s.add(comp,f'Skin stringer {u} {sign}','primer',tube(points,.0055,6))
            # Separate wet-wing perimeter and pipe runs, no opaque solid fuel volume.
            for j,u in enumerate((.34,.69)):
                pts=[]
                for q in range(21):
                    y=y0+(y1-y0)*(.06+.88*q/20);x,yy,z,h=wing_value(rows,y,u);pts.append((x,yy,z))
                s.add(comp,f'Fuel transfer pipe {j+1}','fuel_pipe',tube(pts,.009,10))
            # Rib end brackets, spar fasteners and removable inspection-panel screws.
            hardware=[]
            for k in range(n):
                y=y0+(y1-y0)*(.03+.94*k/(n-1))
                for u in (.12,.29,.46,.63,.80,.92):
                    x,yy,z,h=wing_value(rows,y,u);hardware.append(fastener((x,yy,z+h-.006),(0,0,1),.0038))
            s.add(comp,'Rib-spar joint fasteners','steel',Mesh.merged(hardware),detail_count=len(hardware));mount(s,comp,parent)
            if outer:
                s.add(comp,'Wing-fold hydraulic swivel couplings','steel',Mesh.merged([flat_ring((10.47+i*.15,side*3.785,2.455),(0,1,0),.017,.008,.034,20) for i in range(3)]),detail_count=3)
            # Exterior seams and fixings disappear with the upper inspection skin.
            for b in list(s.bodies):
                if b['label'] in (prefix+' seams',prefix+' fasteners'):move_body(s,b,prefix+' upper skin')

def add_materials(s):
    s.materials.update({
      'primer':dict(physical='Aluminum',color=[151,163,113],metallic=0,roughness=.72),
      'duct_liner':dict(physical='Aluminum',color=[184,190,180],metallic=0,roughness=.55),
      'fuel_bladder':dict(physical='ABS Plastic',color=[68,61,48],metallic=0,roughness=.88),
      'fuel_pipe':dict(physical='Stainless Steel',color=[158,143,92],metallic=.65,roughness=.35),
      'hydraulic_pipe':dict(physical='Titanium',color=[139,151,161],metallic=.72,roughness=.30),
      'wire_copper':dict(physical='Copper',color=[179,111,57],metallic=.85,roughness=.27),
      'electrical_insulator':dict(physical='Nylon',color=[180,176,156],metallic=0,roughness=.72),
      'avionics_face':dict(physical='Aluminum',color=[79,83,78],metallic=0,roughness=.66),
    })

def connector(s,comp,name,p,direction,r=.013,pins=7):
    axis=unit(direction);u,v,w=basis(axis)
    s.add(comp,name+' shell','stainless',flat_ring(add(p,mul(axis,.010)),axis,r,r*.66,.025,24))
    s.add(comp,name+' insulator','electrical_insulator',cylinder(p,add(p,mul(axis,.016)),r*.64,24))
    pinmesh=[]
    for i in range(pins):
        a=2*PI*i/max(1,pins-1);q=p if i==0 else add(p,add(mul(u,r*.40*math.cos(a)),mul(v,r*.40*math.sin(a))))
        pinmesh.append(cylinder(add(q,mul(axis,.012)),add(q,mul(axis,.022)),.0013,6))
    s.add(comp,name+' contacts','wire_copper',Mesh.merged(pinmesh),detail_count=pins)

def avionics_lru(s,comp,name,center,size):
    x,y,z=center;dx,dy,dz=size
    # Six separate walls leave an authentic openable, empty electronic chassis.
    walls=[box((x,y,z-dz/2),(dx,dy,.006)),box((x-dx/2,y,z),(.006,dy,dz)),
           box((x+dx/2,y,z),(.006,dy,dz)),box((x,y-dy/2,z),(dx,.006,dz)),box((x,y+dy/2,z),(dx,.006,dz))]
    s.add(comp,name+' chassis','aluminum',Mesh.merged(walls),detail_count=5)
    lid=comp+' '+name+' lid'
    s.add(lid,name+' removable cover','avionics_face',box((x,y,z+dz/2),(dx+.008,dy+.008,.006)))
    s.joint(lid+' lift',comp,lid,(x,y,z),(0,0,1),(0,.28),0,'slider')
    fins=[]
    for i in range(max(4,int(dx/.019))):fins.append(box((x-dx/2+.012+i*.019,y+dy/2+.009,z),(.004,.018,dz*.79)))
    s.add(comp,name+' heat-sink fins','aluminum',Mesh.merged(fins),detail_count=len(fins))
    boards=[];chips=[]
    for j in range(3):
        yy=y-dy*.30+j*dy*.30;boards.append(box((x,yy,z),(dx*.82,.0016,dz*.72)))
        for k in range(4):chips.append(box((x-dx*.30+k*dx*.20,yy+.004,z),(.026,.006,dz*.25)))
    s.add(comp,name+' board cards','circuit_board',Mesh.merged(boards),detail_count=3)
    s.add(comp,name+' electronic packages','black',Mesh.merged(chips),detail_count=12)
    for j in range(3):connector(s,comp,name+f' connector {j+1}',(x-dx/2-.018,y-dy*.30+j*dy*.30,z),( -1,0,0),.012,7)
    handles=[]
    for yy in (y-dy*.33,y+dy*.33):handles.append(tube([(x-dx/2-.007,yy,z-.035),(x-dx/2-.035,yy,z-.035),(x-dx/2-.035,yy,z+.035),(x-dx/2-.007,yy,z+.035)],.004,8))
    s.add(comp,name+' extraction handles','steel',Mesh.merged(handles),detail_count=2)
    s.add(comp,name+' identification plate','white',box((x-dx/2-.005,y,z+dz*.30),(.002,dy*.46,.022)))

def build_equipment(s):
    s.materials['circuit_board']=dict(physical='ABS Plastic',color=[40,89,58],metallic=0,roughness=.56)
    # Publicly visible mechanically scanned planar antenna, original surface detail.
    comp='Radar pedestal';s.add(comp,'Forward avionics bulkhead','primer',flat_ring((1.93,0,2.24),(1,0,0),.405,.285,.018,64).transformed([[1,0,0,0],[0,1,0,0],[0,0,.85,2.24*.15]]))
    s.add(comp,'Pedestal support casting','aluminum',box((1.91,0,2.07),(.23,.30,.18)))
    s.add(comp,'Azimuth bearing','steel',flat_ring((1.78,0,2.15),(0,0,1),.12,.064,.035,40));mount(s,comp)
    az='Radar azimuth gimbal'
    s.add(az,'Gimbal yoke','aluminum',Mesh.merged([box((1.72,-.255,2.22),(.12,.026,.33)),box((1.72,.255,2.22),(.12,.026,.33)),box((1.72,0,2.07),(.12,.51,.03))]))
    s.joint('Radar azimuth','Radar pedestal',az,(1.78,0,2.24),(0,0,1),(-42,42),0)
    el='Radar elevation antenna'
    s.add(el,'Elliptical planar antenna backing','aluminum',cylinder((1.565,0,2.24),(1.595,0,2.24),.342,80).transformed([[1,0,0,0],[0,1.10,0,0],[0,0,1,0]]))
    # Slot lengths/spacing are artistic surface detail, not RF design data.
    slots=[]
    for row in range(-11,12):
        z=row*.025
        for col in range(-10,11):
            y=col*.031+(.009 if row%2 else 0)
            if (y/.358)**2+(z/.326)**2<.94:slots.append(box((1.562,y,2.24+z),(.002,.019,.0035)))
    s.add(el,'Representative slotted antenna face','steel_dark',Mesh.merged(slots),detail_count=len(slots))
    s.add(el,'Antenna edge frame','aluminum',torus((1.574,0,2.24),.342,.008,axis=(1,0,0),segments=80,sides=8).transformed([[1,0,0,0],[0,1.10,0,0],[0,0,1,0]]))
    s.add(el,'Elevation axle and bearing pins','steel',cylinder((1.72,-.28,2.24),(1.72,.28,2.24),.032,28))
    s.add(el,'Rear antenna stiffeners','aluminum',Mesh.merged([box((1.63,y,2.24),(.05,.012,.48)) for y in (-.19,0,.19)]),detail_count=3)
    s.joint('Radar elevation',az,el,(1.72,0,2.24),(0,1,0),(-30,30),0)
    s.add(az,'Gimbal flexible cable loop','black',tube([(1.92,.1,2.17),(1.91,.2,2.30),(1.84,.25,2.47),(1.73,.21,2.49),(1.64,.17,2.38)],.011,10))
    # Separate slide-out trays inside the forward electronics bays.
    for side,label in ((-1,'Port'),(1,'Starboard')):
        comp=label+' forward avionics tray';y=side*.22
        s.add(comp,'Rack tray and edge rails','primer',Mesh.merged([box((2.69,y,2.065),(1.16,.38,.022)),box((2.69,y-side*.19,2.165),(1.16,.025,.20)),box((2.69,y+side*.19,2.165),(1.16,.025,.20))]))
        avionics_lru(s,comp,'Signal processor',(2.29,y,2.245),(.30,.27,.26))
        avionics_lru(s,comp,'Power supply',(2.65,y,2.265),(.27,.28,.30))
        avionics_lru(s,comp,'Receiver assembly',(3.00,y,2.265),(.30,.28,.30))
        s.joint(label+' avionics tray withdrawal','Airframe',comp,(2.69,y,2.165),(0,side,0),(0,.52),0,'slider')
        # Tray channels fixed to the airframe; articulated chassis retains connectors.
        rail='Forward avionics support rails'
        s.add(rail,label+' rack cross members','primer',Mesh.merged([box((x,y,2.07),(.026,.43,.03)) for x in (2.12,2.49,2.87,3.19)]),detail_count=4)
    mount(s,'Forward avionics support rails')
    # Conditioning and oxygen equipment occupies the volume aft/below the tub.
    comp='Environmental control bay'
    for x,label in ((6.55,'Primary heat exchanger'),(6.88,'Secondary heat exchanger')):
        s.add(comp,label+' manifold','aluminum',box((x,0,1.93),(.26,.36,.15)))
        fins=[box((x-.11+i*.009,0,1.93),(.002,.33,.19)) for i in range(25)]
        s.add(comp,label+' fin pack','aluminum',Mesh.merged(fins),detail_count=len(fins))
    s.add(comp,'Air-cycle machine external housing','aluminum',cylinder((6.43,-.17,2.10),(6.95,-.17,2.10),.105,40))
    s.add(comp,'Conditioned-air distribution duct','duct_liner',tube([(6.90,-.12,2.10),(6.62,-.25,2.16),(6.30,-.28,2.20),(6.10,-.30,2.21)],.040,20))
    s.add(comp,'Oxygen regulator canister','gear_white',cylinder((6.54,.21,1.82),(6.54,.21,2.14),.076,32))
    s.add(comp,'Oxygen hose to cockpit','olive',tube([(6.54,.20,2.15),(6.30,.23,2.22),(6.05,.25,2.29)],.009,10));mount(s,comp)
    # Engine-mounted drive exterior representations sit ahead of each engine.
    comp='Airframe accessory drives'
    for side,label in ((-1,'Port'),(1,'Starboard')):
        y=side*.72
        s.add(comp,label+' AMAD gearbox casing','aluminum',box((12.30,y,1.54),(.37,.26,.19)))
        s.add(comp,label+' generator housing','aluminum',cylinder((12.08,y,1.53),(11.84,y,1.53),.095,32))
        s.add(comp,label+' hydraulic pump housing','steel',cylinder((12.32,y+side*.32,1.62),(12.32,y+side*.12,1.62),.065,28))
        fins=[box((12.10-i*.021,y,1.53),(.004,.194,.194)) for i in range(12)]
        s.add(comp,label+' generator cooling fins','aluminum',Mesh.merged(fins),detail_count=12)
        s.add(comp,label+' drive shaft coupling','steel',cylinder((12.49,y+side*.24,1.60),(12.73,y+side*.24,1.63),.026,24))
        connector(s,comp,label+' generator output',(11.82,y,1.53),(-1,0,0),.022,10)
    mount(s,comp)
    comp='APU and starting equipment'
    s.add(comp,'APU cylindrical shroud','hot_metal',cylinder((11.83,0,1.64),(12.30,0,1.64),.125,48))
    s.add(comp,'APU intake bell','aluminum',flat_ring((11.82,0,1.64),(1,0,0),.127,.080,.025,48))
    s.add(comp,'Starter air manifold','stainless',tube([(12.12,0,1.67),(12.38,0,1.72),(12.44,-.32,1.73),(12.40,-.55,1.64)],.024,14))
    s.add(comp,'Starboard starter-air branch','stainless',tube([(12.38,0,1.72),(12.44,.32,1.73),(12.40,.55,1.64)],.024,14))
    s.add(comp,'APU exhaust elbow','hot_metal',tube([(12.18,0,1.64),(12.24,0,1.57),(12.24,0,1.49)],.045,24));mount(s,comp)

def profile_loft(xs,profile,scale=None):
    verts=[];faces=[];n=len(profile)
    for x in xs:
        for y,z in profile:
            if scale:y,z=scale(x,y,z)
            verts.append((x,y,z))
    for j in range(len(xs)-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;c=b+n;d=a+n;faces.extend(((a,b,c),(a,c,d)))
    for j,reverse in ((0,True),(len(xs)-1,False)):
        offset=len(verts);points=verts[j*n:(j+1)*n];verts.extend(points)
        ff=triangulate(points)
        faces.extend((offset+a,offset+c,offset+b) if reverse else (offset+a,offset+b,offset+c) for a,b,c in ff)
    return Mesh(verts,faces)

def build_fuel(s):
    # The public references establish tank count/function, not these station shapes.
    profiles=[
      ('Fuselage fuel cell 1',6.98,8.42,[(-.26,2.05),(.26,2.05),(.27,2.43),(.76,2.52),(.54,2.69),(0,2.72),(-.54,2.69),(-.76,2.52),(-.27,2.43)]),
      ('Fuselage fuel cell 2 left feed',8.47,10.30,[(-.28,1.72),(-.035,1.72),(-.035,2.61),(-.28,2.60)]),
      ('Fuselage fuel cell 3 right feed',8.47,10.30,[(.035,1.72),(.28,1.72),(.28,2.60),(.035,2.61)]),
      ('Fuselage fuel cell 4',10.35,12.66,[(-.29,1.72),(.29,1.72),(.29,2.44),(.53,2.47),(.43,2.49),(0,2.52),(-.43,2.49),(-.53,2.47),(-.29,2.44)]),
    ]
    for name,xa,xb,profile in profiles:
        comp=name
        def scallop(x,y,z):
            t=(x-xa)/(xb-xa);fac=.96+.04*math.sin(PI*t)
            y,z=y*fac,2.2+(z-2.2)*fac
            # The flexible cells sit below transverse beam flanges at these
            # stations; locally recessed roofs avoid bars emerging through rubber.
            beam_stations=(9.02,9.70) if 'feed' in name else (10.42,11.22) if name.endswith('4') else ()
            weight=max([max(0,min(1,(.075-abs(x-bx))/.040)) for bx in beam_stations]+[0])
            if weight:
                top=2.2+(max(q[1] for q in profile)-2.2)*fac
                shrink=(2.430-1.72)/(top-1.72)
                z=1.72+(z-1.72)*(1-weight+weight*shrink)
                if name.endswith('4'):y*=1-.50*weight
            return y,z
        special=[]
        for bx in (9.02,9.70,10.42,11.22):
            special.extend(x for x in (bx-.075,bx-.035,bx+.035,bx+.075) if xa<x<xb)
        axial=sorted(set(sequence(xa,xb,.12)+special))
        s.add(comp,'Shaped rubber bladder envelope','fuel_bladder',profile_loft(axial,profile,scallop))
        # Seams, access flange, feed/vent fittings and sensor bosses are actual geometry.
        seams=[]
        for x in (xa+.045,xb-.045):
            ps=[(x,*scallop(x,y,z)) for y,z in profile];ps.append(ps[0]);seams.append(tube(ps,.0045,8))
        s.add(comp,'Bladder seam beads','rubber_seal',Mesh.merged(seams),detail_count=2)
        xx=(xa+xb)/2;zz=max(z for y,z in profile)+.008;yy=-.15 if 'left' in name else .15 if 'right' in name else 0
        s.add(comp,'Service hatch flange','aluminum',flat_ring((xx,yy,zz),(0,0,1),.107,.081,.011,48))
        s.add(comp,'Hatch lid','fuel_bladder',cylinder((xx,yy,zz-.003),(xx,yy,zz+.004),.079,48))
        hardware=[]
        for j in range(12):
            a=2*PI*j/12;hardware.append(fastener((xx+.095*math.cos(a),yy+.095*math.sin(a),zz+.009),(0,0,1),.005))
        s.add(comp,'Service flange captive bolts','steel',Mesh.merged(hardware),detail_count=12)
        s.add(comp,'Fuel quantity sender head','steel',cylinder((xa+.16,yy,zz-.012),(xa+.16,yy,zz+.028),.026,24))
        s.add(comp,'Feed outlet flange','steel',flat_ring((xb-.11,yy,1.75 if 'feed' in name or name.endswith('4') else 2.07),(0,0,1),.036,.015,.018,24));mount(s,comp)
    comp='Fuel vent cell'
    s.add(comp,'Dorsal vent and overflow envelope','fuel_bladder',box((12.95,0,2.43),(.45,.33,.16)))
    s.add(comp,'Vent line manifold','fuel_pipe',tube([(12.95,0,2.49),(13.22,0,2.48),(13.42,0,2.43),(14.20,0,2.39)],.014,12));mount(s,comp)
    comp='Fuel pumps valves and distribution'
    for side,label in ((-1,'Port'),(1,'Starboard')):
        y=side*.20
        s.add(comp,label+' feed pump body','aluminum',cylinder((10.05,y,1.63),(10.26,y,1.63),.064,32))
        s.add(comp,label+' pump end cap','steel',cylinder((10.25,y,1.63),(10.28,y,1.63),.068,32))
        pts=[(8.56,y,1.73),(9.1,y,1.64),(10.06,y,1.63),(10.9,y,1.64),(11.55,side*.28,1.67),(12.6,side*.37,1.68),(13.15,side*.39,1.76)]
        s.add(comp,label+' feed line routed outside engine','fuel_pipe',tube(pts,.017,12))
        s.add(comp,label+' shutoff valve housing','steel',box((12.54,side*.36,1.68),(.078,.075,.072)))
        valve=label+' fuel shutoff valve'
        s.add(valve,'Valve actuator spindle','steel',cylinder((12.54,side*.36,1.69),(12.54,side*.36,1.77),.012,16))
        s.add(valve,'Valve position lever','aluminum',box((12.54,side*.39,1.77),(.023,.09,.012)))
        s.joint(label+' fuel valve rotation',comp,valve,(12.54,side*.36,1.74),(0,0,1),(0,90),0)
    s.add(comp,'Crossfeed manifold','fuel_pipe',tube([(10.65,-.20,1.64),(10.65,0,1.64),(10.65,.20,1.64)],.015,12))
    s.add(comp,'Tank vent collector','fuel_pipe',tube([(7.25,0,2.74),(8.22,0,2.71),(9.10,0,2.67),(10.4,0,2.65),(11.8,0,2.56),(12.95,0,2.52)],.010,10))
    for side,label in ((-1,'Port'),(1,'Starboard')):
        s.add(comp,label+' wing transfer feed','fuel_pipe',tube([(10.45,side*.20,2.53),(10.45,side*.66,2.53),(10.45,side*1.15,2.53),(10.57,side*1.55,2.51)],.014,12))
    # Coupling nut flats and clamp saddles along accessible trunk runs.
    nuts=[]
    for side in (-1,1):
        for x in (8.66,9.15,9.86,10.72,11.4):
            nuts.append(cylinder((x-.014,side*.20,1.64),(x+.014,side*.20,1.64),.026,6))
    s.add(comp,'Pipe coupling union nuts','stainless',Mesh.merged(nuts),detail_count=len(nuts));mount(s,comp)

def build_systems(s):
    comp='Hydraulic supply and service lines'
    for side,label in ((-1,'Port'),(1,'Starboard')):
        y=side*.21
        s.add(comp,label+' hydraulic reservoir cylinder','aluminum',cylinder((12.76,y,1.82),(13.05,y,1.82),.082,32))
        s.add(comp,label+' reservoir spherical end','aluminum',sphere((13.05,y,1.82),(.045,.082,.082),24,12))
        s.add(comp,label+' valve manifold block','steel',box((12.65,y,1.79),(.14,.14,.12)))
        # Separate pressure and return paths pass between structure and equipment.
        for k in range(2):
            yy=side*(1.12+k*.025)
            points=[(12.60,side*.38,1.70),(12.15,side*1.05,1.73),(11.55,yy,1.82),(10.45,yy,1.91),(9.48,yy,2.00),(8.50,side*1.06,2.02),(7.22,side*.91,2.04)]
            s.add(comp,label+f' hydraulic trunk {k+1}','hydraulic_pipe',tube(points,.008,10))
        s.add(comp,label+' main-gear branch','hydraulic_pipe',tube([(10.45,side*1.12,1.91),(10.35,side*1.05,1.81),(10.48,side*.83,1.76)],.008,10))
        s.add(comp,label+' wing-control branch','hydraulic_pipe',tube([(10.45,side*1.12,1.91),(10.40,side*1.22,2.33),(10.85,side*1.7,2.51),(11.12,side*2.7,2.48),(11.4,side*3.62,2.45)],.007,10))
        s.add(comp,label+' stabilator branch','hydraulic_pipe',tube([(12.63,side*.38,1.73),(13.25,side*1.1,1.80),(14.30,side*1.1,1.84),(14.67,side*.93,2.0)],.008,10))
        collars=[]
        for x in (7.4,8.1,8.8,9.5,10.2,10.9,11.6):
            yy=side*(.96 if x<8.5 else 1.12);collars.append(box((x,yy,2.01 if x<9 else 1.91),(.028,.065,.032)))
        s.add(comp,label+' line support clamps','electrical_insulator',Mesh.merged(collars),detail_count=len(collars))
    mount(s,comp)
    comp='Electrical harnesses and junction boxes'
    for side,label in ((-1,'Port'),(1,'Starboard')):
        pts=[(2.35,side*.40,2.07),(3.25,side*.47,2.03),(4.20,side*.54,2.03),(5.25,side*.56,2.02),(6.25,side*.58,2.02),(7.30,side*.91,2.32),(9.1,side*1.12,2.36),(11.5,side*1.11,2.34),(13.2,side*1.04,2.34),(14.7,side*1.03,2.30)]
        s.add(comp,label+' shielded main harness','black',tube(pts,.014,12))
        for k in range(3):s.add(comp,label+f' branch conductor bundle {k+1}','electrical_insulator',tube([add(p,(0,side*(.019+k*.007),0)) for p in pts],.0035,6))
        clips=[]
        for i in range(45):
            x=2.5+i*.27;nearest=min(pts,key=lambda p:abs(p[0]-x));clips.append(torus((x,nearest[1],nearest[2]),.017,.0025,axis=(1,0,0),segments=16,sides=6))
        s.add(comp,label+' harness clamp bands','zinc',Mesh.merged(clips),detail_count=len(clips))
        for k,(x,y,z) in enumerate(((3.32,side*.41,2.10),(7.22,side*.88,2.32),(12.30,side*1.03,2.32))):
            s.add(comp,label+f' junction box {k+1}','avionics_face',box((x,y,z),(.15,.08,.10)))
            connector(s,comp,label+f' junction {k+1} plug',(x-.09,y,z),(-1,0,0),.016,9)
    mount(s,comp)
    comp='Engine bay firewalls and mounts'
    for side,label in ((-1,'Port'),(1,'Starboard')):
        y=side*.71
        # Open firewall collars surround the intake interface; none obstruct the fan.
        s.add(comp,label+' forward engine firewall collar','titanium',flat_ring((12.77,y,1.98),(1,0,0),.433,.381,.016,80))
        for x in (13.15,14.18,15.52):
            for a in (.45*PI,1.55*PI):
                p=(x,y+.43*math.sin(a),1.98+.43*math.cos(a));q=add(p,(0,.065*math.sin(a),.065*math.cos(a)))
                s.add(comp,label+f' engine mount strut {x} {a}','titanium',cylinder(p,q,.030,20))
                s.add(comp,label+f' mount clevis {x} {a}','steel',flat_ring(q,(1,0,0),.045,.017,.035,28))
        s.add(comp,label+' firewall cable feedthrough','steel',flat_ring((12.77,y-side*.37,2.10),(1,0,0),.024,.011,.035,24))
    # Thin central heat shield separates the two engine bays.
    s.add(comp,'Central longitudinal fire barrier','titanium',box((14.35,0,1.96),(3.15,.012,.68)))
    mount(s,comp)

def build_gear_bays(s):
    comp='Nose landing gear bay'
    walls=[box((3.725,0,2.41),(.75,.58,.016)),box((4.88,0,2.054),(1.56,.58,.016)),
           box((3.35,0,2.10),(.016,.58,.62)),box((5.66,0,1.94),(.016,.58,.23)),
           box((4.10,0,2.232),(.012,.58,.34))]
    for side in (-1,1):
        walls.append(box((3.725,side*.29,2.10),(.75,.014,.62)))
        walls.append(box((4.88,side*.29,1.94),(1.56,.014,.23)))
    s.add(comp,'Open wheel-well liners','gear_white',Mesh.merged(walls),detail_count=5)
    ribs=[]
    for x in (3.48,3.73,3.98,4.30,4.65,5.00,5.40):
        roof=2.388 if x<4.1 else 2.033;low=1.82;mid=(roof+low)/2
        ribs.extend([box((x,-.278,mid),(.018,.022,roof-low)),box((x,.278,mid),(.018,.022,roof-low)),box((x,0,roof),(.022,.54,.024))])
    s.add(comp,'Well frames and ceiling channels','gear_white',Mesh.merged(ribs),detail_count=len(ribs))
    s.add(comp,'Nose trunnion ceiling support','aluminum',box((5.45,0,2.040),(.18,.35,.035)))
    for i in range(4):
        s.add(comp,f'Ceiling pipe run {i+1}','hydraulic_pipe',tube([(4.22,-.22+i*.07,2.030),(4.75,-.22+i*.07,2.030),(5.26,-.22+i*.07,2.030),(5.55,-.22+i*.07,1.90)],.006,8))
    s.add(comp,'Door sequence manifold','steel',box((5.48,-.25,1.99),(.15,.055,.10)));mount(s,comp)
    for side,label in ((-1,'Port'),(1,'Starboard')):
        comp=label+' main landing gear bay';y=side*.78
        walls=[box((10.88,y,1.79),(1.70,.79,.014)),box((10.03,y,1.59),(.014,.79,.4)),box((11.73,y,1.59),(.014,.79,.4)),box((10.88,side*.38,1.59),(1.70,.014,.4))]
        s.add(comp,'Open main-wheel well walls','gear_white',Mesh.merged(walls),detail_count=4)
        ribs=[]
        for x in (10.12,10.40,10.70,11.02,11.32,11.62):
            ribs.extend([box((x,y,1.784),(.022,.76,.016)),box((x,side*.395,1.60),(.022,.022,.34))])
        s.add(comp,'Well reinforcement channels','gear_white',Mesh.merged(ribs),detail_count=len(ribs))
        for k in range(3):s.add(comp,f'Gear bay pipe {k+1}','hydraulic_pipe',tube([(10.2,side*(.47+.075*k),1.779),(11.55,side*(.47+.075*k),1.779),(11.66,side*(.47+.075*k),1.57)],.004,8))
        s.add(comp,'Gear uplock hook housing','steel',box((11.54,side*.70,1.71),(.14,.12,.09)))
        s.add(comp,'Uplock roller','steel',cylinder((11.52,side*.63,1.67),(11.52,side*.77,1.67),.028,24));mount(s,comp)

def add_actuator(s,name,parent,moving,A,B,hinge_axis,r=.025):
    """Three passive native joints close a real telescoping actuator loop."""
    axis=unit(sub(B,A));L=length(sub(B,A));bar=name+' barrel';rod=name+' piston rod'
    s.add(bar,'Hollow hydraulic cylinder body','steel',flat_ring(add(A,mul(axis,L*.38)),axis,r,r*.49,L*.76,32))
    s.add(bar,'Cylinder closed base','steel',cylinder(A,add(A,mul(axis,.018)),r,24))
    s.add(bar,'End gland and rod wiper','stainless',flat_ring(add(A,mul(axis,L*.76)),axis,r*1.10,r*.44,.015,28))
    s.add(bar,'Fixed clevis eye','steel',flat_ring(A,hinge_axis,r*1.24,r*.48,r*1.4,28))
    s.add(rod,'Polished working piston rod','stainless',cylinder(add(A,mul(axis,L*.06)),B,r*.43,24))
    s.add(rod,'Moving clevis eye','steel',flat_ring(B,hinge_axis,r*1.15,r*.42,r*1.2,28))
    # The pin joints and telescope are solved together with the moving surface.
    s.joint(name+' base pin',parent,bar,A,hinge_axis,(-179,179),0)
    s.joints[-1]['passive']=True
    s.joint(name+' telescope',bar,rod,A,axis,(-L*.65,max(1.0,L*2)),0,'slider')
    s.joints[-1]['passive']=True
    s.joint(name+' moving pin',moving,rod,B,hinge_axis,(-179,179),0)
    s.joints[-1]['passive']=True
    return [name+' base pin',name+' telescope',name+' moving pin']

def build_actuators(s):
    # Replace the old fixed decorative canopy ram with a solved pin/slider/pin loop.
    remove_bodies(s,lambda b:b['component']=='Canopy actuator')
    s.joints=[j for j in s.joints if j['name']!='Canopy actuator mount']
    if 'Canopy actuator' in s.components:del s.components['Canopy actuator']
    add_actuator(s,'Canopy hydraulic lift','Airframe','Canopy',(6.62,0,2.10),(6.40,0,2.78),(0,1,0),.028)
    # Speedbrake actuator rod follows the actual opened panel, without linear travel guess.
    add_actuator(s,'Speedbrake hydraulic lift','Airframe','Speedbrake',(7.30,0,2.36),(8.40,0,2.77),(0,-1,0),.031)
    for side,label in ((-1,'Port'),(1,'Starboard')):
        # Stabilator hinge axis is Y. Both actuator pins share its rotation plane.
        y=side*.81
        add_actuator(s,label+' stabilator actuator','Airframe',label+' stabilator',(13.92,y,1.78),(14.95,y,1.99),(0,1,0),.025)
        # Flap hinges are swept; use points offset along a plane normal to that axis.
        for kind,suffix in [('TE flap',' trailing flap'),('inner LE flap',' inner leading flap')]:
            joint=next(j for j in s.joints if j['name']==label+' '+kind);H=joint['origin'];ax=joint['axis']
            # Centre of hinge segment along authored span direction, in world coordinates.
            midpoint=add(H,mul(ax,side*.95 if kind=='TE flap' else -side*.95))
            normal=unit(cross(ax,(0,0,1)))
            up=unit(sub((0,0,1),mul(ax,ax[2])))
            A=add(add(midpoint,mul(normal,-.33)),mul(up,-.075))
            B=add(add(midpoint,mul(normal,.15)),mul(up,-.025))
            add_actuator(s,label+' '+kind+' actuator','Airframe',label+suffix,A,B,ax,.014)
    # Radome latches are individually modeled, but not represented as load-rated hardware.
    for i,t in enumerate((.6,1.8,3.0,4.2,5.4)):
        pp=ellipse_point(NOSE,1.86,t,.018)
        s.add('Radome',f'Radome latch {i+1}','steel',box(pp,(.065,.022,.038)))

def build(s):
    add_materials(s);replace_skins(s);build_ducts(s);build_frames(s);build_wing_structure(s)
    build_equipment(s);build_fuel(s);build_systems(s);build_gear_bays(s);build_actuators(s)
    s.notes.extend([
      'Revision 2 replaces opaque intake blockers and intersecting filled fuselage lofts with continuous hollow ducts and segmented finite-thickness outer skins.',
      'Primary Legacy-family structure references support metal spars/ribs, composite wing skins, center-barrel wing/main-gear load paths, dorsal decks and keel longerons. Exact station spacing and gauges are original visual reconstruction.',
      'Four fuselage fuel-cell envelopes, one vent cell and wet-wing pipework follow publicly documented architecture; capacity, exact routing, fittings and bay subdivisions are not certified dimensions.',
      'Inspectable skin, duct, fuel-cell, equipment and structure groups are independently named; inspection variants preserve the complete closed model in the master.',
    ])
