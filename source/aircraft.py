"""Original visual reconstruction of a Legacy Hornet; public-reference dimensions.

The source deliberately describes an appearance/animation model, not structural
or flightworthy engineering. Small dimensions and hinge ranges are authored.
"""
from scene_api import *
import math,bisect

def stations(rows,step=.08):
    out=[]
    for i in range(len(rows)-1):
        a,b=rows[i:i+2];n=max(2,math.ceil((b[0]-a[0])/step))
        for k in range(n):
            t=k/n;v=[a[0]+(b[0]-a[0])*t]
            for d in range(1,len(a)):
                prev=rows[max(0,i-1)];nxt=rows[min(len(rows)-1,i+2)]
                m0=(b[d]-prev[d])/(b[0]-prev[0]);m1=(nxt[d]-a[d])/(nxt[0]-a[0])
                value=(2*t**3-3*t**2+1)*a[d]+(t**3-2*t**2+t)*(b[0]-a[0])*m0+(-2*t**3+3*t**2)*b[d]+(t**3-t*t)*(b[0]-a[0])*m1
                v.append(value)
            out.append(v)
    out.append(list(rows[-1]));return out

def body_loft(rows,segments=80,gap=False,center_y=0):
    """Rows x, halfwidth, axisZ, upperRadius, lowerRadius[, topOpeningAngle]."""
    rr=stations(rows);vs=[];fs=[];count=segments+1
    for row in rr:
        x,w,z,hu,hd=row[:5];a=row[5] if gap else 0
        for j in range(count):
            t=a+(2*math.pi-2*a)*j/segments;c=math.cos(t)
            vs.append((x,center_y+w*math.sin(t),z+(hu if c>=0 else hd)*c))
    for i in range(len(rr)-1):
        for j in range(segments):
            a=i*count+j;b=a+count;fs.extend([(a,b,b+1),(a,b+1,a+1)])
    if gap:
        block=len(vs)
        inner=[]
        for i,row in enumerate(rr):
            for j in range(count):
                x,y,z=vs[i*count+j]
                inner.append((x,center_y+(y-center_y)*.982,row[2]+(z-row[2])*.982))
        vs.extend(inner)
        fs.extend((a+block,c+block,b+block) for a,b,c in list(fs))
        edges=[(j+1,j) for j in range(segments)]
        edges.extend(((len(rr)-1)*count+j,(len(rr)-1)*count+j+1) for j in range(segments))
        edges.extend((i*count,(i+1)*count) for i in range(len(rr)-1))
        edges.extend(((i+1)*count+segments,i*count+segments) for i in range(len(rr)-1))
        for a,b in edges:
            off=len(vs);vs.extend([vs[b],vs[a],vs[a+block],vs[b+block]])
            fs.extend([(off,off+1,off+2),(off,off+2,off+3)])
        return Mesh(vs,fs)
    # Cap axial ends, closing the imported part at its seams.
    for end,reverse in ((0,False),(len(rr)-1,True)):
        row=rr[end];ci=len(vs);vs.append((row[0],center_y,row[2]));off=end*count
        for j in range(segments):
            f=(ci,off+j,off+j+1);fs.append((f[0],f[2],f[1]) if reverse else f)
    return Mesh(vs,fs)

def blister(rows,segments=64,thickness=.009):
    """Closed canopy glazing: curved outer and inner skins joined at every rim."""
    rr=stations(rows,.045);ns=segments+1;vs=[];fs=[]
    for inner in (False,True):
        for x,w,base,h in rr:
            w=max(.001,w-(thickness if inner else 0));h=max(.001,h-(thickness if inner else 0))
            for j in range(ns):
                t=-math.pi/2+math.pi*j/segments
                vs.append((x,w*math.sin(t),base+h*math.cos(t)))
    block=len(rr)*ns
    for inside in (0,1):
        off=inside*block
        for i in range(len(rr)-1):
            for j in range(segments):
                a=off+i*ns+j;b=a+ns;f1=(a,a+1,b+1);f2=(a,b+1,b)
                fs.extend([(f1[0],f1[2],f1[1]),(f2[0],f2[2],f2[1])] if inside else [f1,f2])
    # Four perimeter strips. Orient using signed volume correction below.
    edges=[]
    edges.extend((j,j+1) for j in range(segments))
    edges.extend(((len(rr)-1)*ns+j+1,(len(rr)-1)*ns+j) for j in range(segments))
    edges.extend(((i+1)*ns,i*ns) for i in range(len(rr)-1))
    edges.extend((i*ns+segments,(i+1)*ns+segments) for i in range(len(rr)-1))
    for b,a in edges:
        off=len(vs);vs.extend([vs[a],vs[b],vs[b+block],vs[a+block]])
        fs.extend([(off,off+1,off+3),(off+1,off+2,off+3)])
    m=Mesh(vs,fs)
    volume=sum(dot(m.vertices[a],cross(m.vertices[b],m.vertices[c]))/6 for a,b,c in fs)
    if volume<0:m.faces=[(a,c,b) for a,b,c in fs]
    return m

def airfoil(rows,span_steps=18,chord_steps=44):
    """Rows: y, leading X, trailing X, centre Z, thickness ratio."""
    # Closed, smooth, spanwise NACA-style artistic sections.
    rr=[]
    for i in range(len(rows)-1):
        for k in range(span_steps):rr.append(lerp(rows[i],rows[i+1],k/span_steps))
    rr.append(rows[-1]);vs=[];fs=[];nc=chord_steps+1
    uv=[(1-math.cos(math.pi*j/chord_steps))/2 for j in range(nc)]
    for sign in (1,-1):
        for y,le,te,z,tr in rr:
            chord=te-le
            for u in uv:
                thick=5*tr*chord*(.2969*math.sqrt(max(u,0))-.126*u-.3516*u*u+.2843*u**3-.1036*u**4)
                vs.append((le+u*chord,y,z+sign*max(.00025,thick)))
    block=len(rr)*nc
    for layer in (0,1):
        for i in range(len(rr)-1):
            for j in range(chord_steps):
                a=layer*block+i*nc+j;b=a+nc
                ff=[(a,a+1,b+1),(a,b+1,b)]
                fs.extend([(a,c,b) for a,b,c in ff] if layer else ff)
    edges=[(j,j+1) for j in range(chord_steps)]
    edges.extend(((len(rr)-1)*nc+j+1,(len(rr)-1)*nc+j) for j in range(chord_steps))
    edges.extend(((i+1)*nc,i*nc) for i in range(len(rr)-1))
    edges.extend((i*nc+chord_steps,(i+1)*nc+chord_steps) for i in range(len(rr)-1))
    for a,b in edges:
        off=len(vs);vs.extend([vs[b],vs[a],vs[a+block],vs[b+block]])
        fs.extend([(off,off+1,off+2),(off,off+2,off+3)])
    m=Mesh(vs,fs)
    if sum(dot(vs[a],cross(vs[b],vs[c])) for a,b,c in fs)<0:m.faces=[(a,c,b) for a,b,c in fs]
    return m

def sheet_wing(points,thick=.045):
    return prism([(x,y,z-thick/2) for x,y,z in points],(0,0,thick))

def ring_on_body(x,width,z,hu,hd,r=.002,segments=96):
    pts=[]
    for i in range(segments+1):
        a=2*math.pi*i/segments;c=math.cos(a)
        pts.append((x,(width+.001)*math.sin(a),z+(hu if c>=0 else hd)*c+.001))
    return tube(pts,r,6)

def fastener(p,axis=(0,0,1),r=.006):
    return cylinder(p,add(p,mul(unit(axis),.0015)),r,segments=10)

def conform_side(mesh,rows,side,offset=.001):
    """Place original stencil geometry on the curved painted skin."""
    dense=stations(rows,.025);xs=[r[0] for r in dense];base=min(abs(p[1]) for p in mesh.vertices)
    out=[]
    for x,y,z in mesh.vertices:
        i=max(0,min(len(xs)-2,bisect.bisect_right(xs,x)-1));t=max(0,min(1,(x-xs[i])/(xs[i+1]-xs[i])))
        row=lerp(dense[i],dense[i+1],t);w,cz,hu,hd=row[1:5];h=hu if z>=cz else hd
        surf=w*math.sqrt(max(.001,1-((z-cz)/h)**2))
        out.append((x,side*(surf+offset+abs(abs(y)-base)),z))
    return Mesh(out,list(mesh.faces))

def build(scene):
    build_fuselage(scene);build_wings(scene);build_tails(scene);build_gear(scene);build_misc(scene)
    scene.notes.extend([
        'Legacy F/A-18C proportions anchored to NASA three-view and US Navy photographs; approximately 17.07 m length and 11.43 m bare wing span.',
        'Visual reconstruction for rendering. Internal structure, loads, certified materials, exact hinges and motion limits are not engineering data.',
        'VFA-146/CVW-9 NG identity is historical for Stennis circa 2009. The NG301 low-visibility markings are an original interpretation, not a museum-exact BuNo reconstruction.',
        'Default HALF-flap launch appearance: approximately 12 degrees leading-edge and 30 degrees trailing-edge droop; joints are artistic animation controls.',
    ])

def build_fuselage(s):
    s.add('Radome','Radome composite shell','radome',body_loft([(0.03,.015,1.78,.018,.016),(.35,.22,1.86,.20,.18),(.9,.42,2.05,.35,.28),(1.7,.53,2.21,.43,.35),(1.85,.54,2.24,.44,.36)]))
    s.joint('Radome service opening','Airframe','Radome',(1.85,.53,2.24),(0,0,-1),(0,95),0)
    s.add('Airframe','Radome hinge brackets','steel',Mesh.merged([cylinder((1.85,.53,z),(1.85,.53,z+.09),.018,16) for z in (2.03,2.32)]),detail_count=2)
    s.add('Airframe','Forward nose skin','skin',body_loft([(1.855,.54,2.24,.44,.36),(2.5,.58,2.29,.49,.41),(3.35,.65,2.32,.57,.49)]))
    s.add('Airframe','Cockpit aperture skin','skin',body_loft([(3.35,.65,2.32,.57,.49,.01),(3.65,.67,2.32,.61,.50,.50),(4.2,.70,2.31,.64,.51,.66),(5.0,.71,2.28,.68,.55,.68),(6.1,.74,2.24,.69,.59,.65),(6.6,.79,2.21,.68,.63,.48),(6.95,.84,2.18,.67,.65,.01)],gap=True))
    s.add('Airframe','Aft spine and centre fuselage','skin',body_loft([(6.95,.84,2.18,.67,.65),(8.1,1.0,2.14,.66,.65),(9.7,1.08,2.10,.62,.62),(11.5,1.04,2.10,.52,.62),(13.4,1.03,2.10,.43,.59),(14.6,1.05,2.08,.34,.55),(15.70,.92,2.07,.30,.50),(16.05,.80,2.06,.26,.44)]))
    # Distinct lower nacelle contours and D-shaped inlets of a Legacy Hornet.
    for side,label in ((-1,'Port'),(1,'Starboard')):
        y=side*.70
        s.add('Airframe',label+' lower engine fairing','skin_lower',body_loft([(6.15,.38,1.97,.40,.46),(6.6,.49,1.96,.46,.48),(8,.57,1.93,.56,.56),(10.8,.58,1.93,.54,.56),(13.6,.54,1.96,.49,.50),(15.6,.51,1.99,.46,.46)],center_y=y))
        # The inlet interior is recessed, with a rounded rim and a visible dark duct.
        outline=[]
        for j in range(57):
            t=2*math.pi*j/56
            yy=side*max(.34,.71+.46*math.sin(t));zz=1.98+.44*math.cos(t)
            outline.append((6.08,yy,zz))
        s.add('Airframe',label+' intake lip','skin_lower',tube(outline,.035,12))
        s.add('Airframe',label+' dark recessed intake duct','black',body_loft([(6.09,.424,1.98,.402,.40),(6.28,.416,1.98,.39,.39),(7.85,.34,1.98,.34,.34)],center_y=y))
        # Dark inset front blocks the outer nacelle behind it, preserving inlet depth.
        darkpoly=[(6.105,side*max(.355,.71+.422*math.sin(2*math.pi*j/56)),1.98+.402*math.cos(2*math.pi*j/56)) for j in range(56)]
        s.add('Airframe',label+' intake shadow','black',prism(darkpoly,(.045,0,0)))
        # Splitter plate: narrow stand-off gap, flange and panel screw row.
        yy=side*.29
        plate=[(5.76,yy,2.38),(6.39,yy,2.46),(7.4,yy,2.35),(7.3,yy,1.58),(6.1,yy,1.58)]
        s.add('Airframe',label+' intake splitter plate','skin',prism(plate,(0,side*.022,0)))
        vents=[]
        for i in range(18):vents.append(box((6.3+i*.052,side*.314,2.26),(.023,.006,.13)))
        s.add('Airframe',label+' splitter bleed slots','paint_dark',Mesh.merged(vents),detail_count=18)
        # Broad leading-edge extension; upper surface tapers smoothly from nose to wing root.
        lex=[(3.45,side*.52,2.70),(4.7,side*.85,2.73),(6.30,side*1.13,2.68),(7.3,side*1.43,2.62),(8.80,side*1.60,2.56),(9.8,side*1.43,2.51),(9.8,side*.78,2.55),(6.5,side*.63,2.74)]
        s.add('Airframe',label+' leading edge root extension','skin',sheet_wing(lex,.045))
        fence=[(8.66,side*1.07,2.60),(8.45,side*1.07,2.91),(9.13,side*1.07,2.78),(9.35,side*1.07,2.59)]
        s.add('Airframe',label+' LEX fence','skin_panel',prism(fence,(0,side*.018,0)))
    # Cockpit lips, blackout coaming and fixed windscreen.
    for side in (-1,1):
        s.add('Airframe',('Port' if side<0 else 'Starboard')+' cockpit sill','rubber_seal',tube([(3.63,side*.32,2.85),(4.25,side*.445,2.82),(5.5,side*.455,2.80),(6.48,side*.38,2.81),(6.85,side*.16,2.83)],.025,12))
    windrows=[(3.40,.035,2.86,.025),(3.62,.22,2.85,.20),(4.10,.40,2.82,.42),(4.62,.46,2.80,.59)]
    s.add('Airframe','Fixed windscreen glazing','glass',blister(windrows))
    s.add('Airframe','Windscreen arch frame','skin',tube([(4.62,.46*math.sin(t),2.80+.59*math.cos(t)) for t in [-math.pi/2+math.pi*j/64 for j in range(65)]],.021,10))
    s.add('Airframe','Windscreen centre bow','paint_dark',tube([(x,0,b+h+.006) for x,w,b,h in stations(windrows,.07)],.012,10))
    canopyrows=[(4.66,.465,2.80,.595),(5.0,.49,2.80,.64),(5.6,.48,2.80,.58),(6.15,.44,2.80,.43),(6.59,.31,2.81,.22),(6.87,.06,2.83,.03)]
    s.add('Canopy','Closed double-skin canopy glazing','glass',blister(canopyrows))
    frame=[]
    for side in (-1,1):frame.append(tube([(x,side*w,b-.008) for x,w,b,h in stations(canopyrows,.08)],.030,12))
    for x,w,b,h in (canopyrows[0],canopyrows[-1]):frame.append(tube([(x,w*math.sin(t),b+h*math.cos(t)) for t in [-math.pi/2+math.pi*j/48 for j in range(49)]],.023,10))
    s.add('Canopy','Canopy perimeter metal frame','skin',Mesh.merged(frame))
    seals=[];bolts=[]
    for side in (-1,1):
        seals.append(tube([(x,side*(w-.008),b-.028) for x,w,b,h in stations(canopyrows,.11)],.010,8))
        for x,w,b,h in stations(canopyrows,.18):bolts.append(fastener((x,side*(w+.015),b),axis=(0,side,0),r=.005))
        s.add('Canopy',f'Internal grab rail {side}','black',tube([(4.95,side*.43,2.77),(5.55,side*.43,2.77),(6.18,side*.36,2.78)],.018,10))
    s.add('Canopy','Canopy gasket','rubber_seal',Mesh.merged(seals))
    s.add('Canopy','Canopy frame screw array','steel',Mesh.merged(bolts),detail_count=len(bolts))
    for y in (-.28,0,.28):
        mirror=box((4.82,y,3.27 if y else 3.34),(.017,.13,.075))
        s.add('Canopy',f'Rear view mirror {y}','stainless',mirror)
    s.add('Canopy','Rear hinge cross shaft','steel',cylinder((6.85,-.28,2.83),(6.85,.28,2.83),.044,32))
    s.add('Canopy carriage','Canopy hinge sliding carriage','steel',box((6.85,0,2.81),(.14,.36,.06)))
    s.joint('Canopy unlatch slide','Airframe','Canopy carriage',(6.85,0,2.83),(1,0,0),(0,.0381),0,'slider')
    s.joint('Canopy open','Canopy carriage','Canopy',(6.85,0,2.83),(0,1,0),(0,68),0)
    # Canopy actuator represented with separately poseable barrel and sliding rod.
    s.add('Canopy actuator','Canopy lift actuator body','steel',cylinder((6.6,0,2.51),(6.86,0,2.71),.035,24))
    s.fixed('Canopy actuator mount','Airframe','Canopy actuator')
    # Panel seams and subtly varied access panels, not painted black outlines.
    seams=[];rivet=[]
    for x,w,z,hu,hd in [(1.85,.54,2.24,.44,.36),(2.5,.58,2.29,.49,.41),(3.25,.642,2.32,.56,.48),(7.05,.86,2.18,.67,.65),(8.25,1.01,2.13,.65,.64),(10.3,1.07,2.10,.59,.62),(11.9,1.04,2.1,.50,.61),(13.45,1.03,2.10,.43,.59),(14.7,1.04,2.08,.33,.54),(15.55,.94,2.07,.30,.50)]:
        seams.append(ring_on_body(x,w,z,hu,hd,r=.0016))
        for a in [2*math.pi*i/52 for i in range(52)]:
            c=math.cos(a);p=(x+.025,(w+.002)*math.sin(a),z+(hu if c>=0 else hd)*c)
            rivet.append(fastener(p,axis=(0,math.sin(a),math.cos(a)),r=.0038))
    for side in (-1,1):
        for z in (1.85,2.15,2.43):
            pts=[]
            for x,w,cz,hu,hd in stations([(7.1,.86,2.18,.67,.65),(8.4,1.03,2.13,.64,.64),(10.7,1.06,2.10,.56,.62),(13.5,1.03,2.10,.42,.59),(15.4,.96,2.07,.31,.51)],.12):
                h=hu if z>=cz else hd;term=max(.05,1-((z-cz)/h)**2);pts.append((x,side*(w*math.sqrt(term)+.003),z))
            seams.append(tube(pts,.0016,6))
    s.add('Airframe','Skin panel engraved seams','seam',Mesh.merged(seams),detail_count=len(seams))
    s.add('Airframe','Skin flush fastener rows','steel_dark',Mesh.merged(rivet),detail_count=len(rivet))
    # Gun bay vents, cooling grilles, blade aerials, formation-light strips.
    ventmeshes=[]
    for side in (-1,1):
        for i in range(9):ventmeshes.append(box((3.06+i*.055,side*.57,2.43),(.025,.012,.13)))
        for i in range(12):ventmeshes.append(box((7.20+i*.057,side*.67,2.57),(.032,.018,.095)))
        s.add('Airframe',f'Forward slime light {side}','cream',box((2.45,side*.555,2.32),(.43,.008,.045)))
        s.add('Airframe',f'Aft slime light {side}','cream',box((13.4,side*1.012,2.24),(.5,.008,.045)))
    s.add('Airframe','Cooling louvers','paint_dark',Mesh.merged(ventmeshes),detail_count=len(ventmeshes))
    for x,z,h in [(7.43,2.84,.28),(12.1,2.62,.33),(4.0,1.78,-.24),(12.9,1.48,-.24)]:
        pts=[(x,0,z),(x+.37,0,z),(x+.20,0,z+h),(x+.10,0,z+h)]
        s.add('Airframe',f'Blade aerial {x}','skin_panel',prism(pts,(0,.025,0)))
    s.add('Airframe','Upper anti collision lens','red',sphere((7.12,0,2.89),(.08,.05,.035),24,12))
    s.add('Airframe','Lower anti collision lens','red',sphere((9.1,0,1.41),(.065,.05,.025),24,12))
    # Low-visibility markings, all original geometry; no decal asset extraction.
    for side,label in ((-1,'Port'),(1,'Starboard')):
        right=(1,0,0) if side<0 else (-1,0,0);origin=(2.15 if side<0 else 3.2,side*.583,2.36)
        nose_rows=[(1.855,.54,2.24,.44,.36),(2.5,.58,2.29,.49,.41),(3.35,.65,2.32,.57,.49)]
        rear_rows=[(11.5,1.04,2.10,.52,.62),(13.4,1.03,2.10,.43,.59),(14.6,1.05,2.08,.34,.55)]
        s.add('Airframe',label+' nose modex 301','paint_dark',conform_side(text('301',origin,.24,right=right,up=(0,0,1),depth=.0008),nose_rows,side))
        s.add('Airframe',label+' NAVY stencil','paint_dark',conform_side(text('NAVY',(12.0 if side<0 else 13.45,side*1.045,2.05),.23,right=right,up=(0,0,1),depth=.0008),rear_rows,side))
        s.add('Airframe',label+' VFA146 stencil','paint_dark',conform_side(text('VFA-146',(11.92 if side<0 else 13.43,side*1.05,1.87),.115,right=right,up=(0,0,1),depth=.0007),rear_rows,side))
        # Rescue arrow and ejection warning triangle.
        yy=side*.666
        tri=[(3.91,yy,2.57),(4.15,yy,2.57),(4.03,yy,2.39)]
        s.add('Airframe',label+' ejection warning placard','yellow',prism(tri,(0,side*.001,0)))
        s.add('Airframe',label+' RESCUE marking','paint_dark',text('RESCUE',(3.50 if side<0 else 4.01,side*.66,2.69),.062,right=right,up=(0,0,1),depth=.001))

def wing_patch(s,component,label,rows,material='composite'):
    m=airfoil(rows,span_steps=16,chord_steps=34)
    s.add(component,label,material,m)
    # Raised panel lines are deliberately submillimetre in width at full scale.
    seams=[];bolts=[]
    for t in (.36,.68):
        pts=[]
        for y,le,te,z,tr in rows:
            u=t;th=5*tr*(te-le)*(.2969*math.sqrt(u)-.126*u-.3516*u*u+.2843*u**3-.1036*u**4)
            pts.append((le+u*(te-le),y,z+th+.002))
        seams.append(tube(pts,.0016,6))
    for y,le,te,z,tr in (rows[0],rows[-1]):
        for k in range(15):
            u=.12+.78*k/14;th=5*tr*(te-le)*(.2969*math.sqrt(u)-.126*u-.3516*u*u+.2843*u**3-.1036*u**4)
            bolts.append(fastener((le+u*(te-le),y,z+th+.002),r=.0037))
    s.add(component,label+' seams','seam',Mesh.merged(seams))
    s.add(component,label+' fasteners','steel_dark',Mesh.merged(bolts),detail_count=len(bolts))

def build_wings(s):
    for side,label in ((-1,'Port'),(1,'Starboard')):
        # Wing centre section between leading flap and trailing flap.
        fixed=[(side*1.10,8.86,11.47,2.54,.054),(side*3.74,10.24,11.72,2.46,.051)]
        outer=[(side*3.77,10.25,11.72,2.46,.051),(side*5.715,11.26,12.23,2.40,.047)]
        wing_patch(s,'Airframe',label+' inner wing',fixed)
        fold=label+' outer wing'
        wing_patch(s,fold,label+' outer wing',outer)
        s.joint(label+' wing fold','Airframe',fold,(10.2,side*3.75,2.46),(side,0,0),(0,100),0)
        # Wing fold hinge barrels and lock lugs remain on their respective halves.
        barrels=[];lugs=[]
        for i in range(9):
            x=10.25+i*.16
            barrels.append(cylinder((x,side*3.75,2.45),(x+.095,side*3.75,2.45),.028,16))
            lugs.append(box((x+.025,side*3.80,2.48),(.06,.09,.04)))
        s.add('Airframe',label+' wingfold hinge barrels','steel',Mesh.merged(barrels),detail_count=9)
        s.add(fold,label+' wingfold locking knuckles','steel',Mesh.merged(lugs),detail_count=9)
        # The leading flap follows the swept leading edge; outer flap follows fold.
        for out in (False,True):
            comp=label+(' outer leading flap' if out else ' inner leading flap')
            rr=[(side*3.78,9.97,10.24,2.46,.065),(side*5.71,11.0,11.25,2.40,.060)] if out else [(side*1.11,8.45,8.85,2.54,.07),(side*3.73,9.95,10.23,2.46,.065)]
            wing_patch(s,comp,'Leading edge flap',rr)
            start=(rr[0][2],rr[0][0],rr[0][3]);end=(rr[-1][2],rr[-1][0],rr[-1][3]);axis=sub(end,start)
            if side<0:axis=mul(axis,-1)
            s.joint(label+(' outer LE flap' if out else ' inner LE flap'),fold if out else 'Airframe',comp,start,mul(axis,-1),(0,25),12)
        # Trailing edge inboard flap and outer aileron.
        for out in (False,True):
            comp=label+(' aileron' if out else ' trailing flap')
            rr=[(side*3.80,11.75,12.50,2.46,.07),(side*5.67,12.25,12.53,2.40,.07)] if out else [(side*1.18,11.51,12.55,2.54,.06),(side*3.70,11.76,12.55,2.46,.065)]
            wing_patch(s,comp,'Trailing surface',rr)
            start=(rr[0][1],rr[0][0],rr[0][3]);end=(rr[-1][1],rr[-1][0],rr[-1][3]);axis=sub(end,start)
            if side<0:axis=mul(axis,-1)
            s.joint(label+(' aileron droop' if out else ' TE flap'),'Airframe' if not out else fold,comp,start,axis,(-25,45),30)
            if not out:
                for yy in (side*1.65,side*3.05):
                    s.add(comp,f'Flap underside fairing {yy}','skin',sphere((11.95,yy,2.38),(.42,.11,.12),24,10))
        # Wingtip rail, coloured position lens and small static dischargers.
        s.add(fold,'LAU7 visual rail','gray',box((11.64,side*5.77,2.40),(2.40,.11,.12)))
        s.add(fold,'Rail end cap forward','aluminum',sphere((10.44,side*5.77,2.40),(.13,.065,.065),20,10))
        s.add(fold,'Navigation light','red' if side<0 else 'light_green',sphere((12.33,side*5.78,2.43),(.09,.04,.035),20,10))
        s.add(fold,'Wing formation light','cream',box((11.81,side*5.72,2.47),(.39,.045,.006)))
        wicks=[]
        for y in (4.3,4.8,5.3):wicks.append(cylinder((12.53,side*y,2.39),(12.76,side*y,2.39),.003,8))
        s.add(fold,'Static discharge wicks','black',Mesh.merged(wicks),detail_count=3)
        # Pylons and inert drop tanks: two prominent station fairings per side.
        for yi,xc in ((2.35,10.05),(4.1,10.85)):
            comp='Airframe' if yi<3.75 else fold;y=side*yi
            pp=[(xc-.5,y,2.45),(xc+.85,y,2.42),(xc+.64,y,1.98),(xc-.23,y,2.01)]
            s.add(comp,f'{label} wing pylon {yi}','skin_lower',prism(pp,(0,.085,0)))
            bolts=[fastener((xc+.1+i*.12,y-.015,2.23),(0,-1,0),.007) for i in range(4)]
            s.add(comp,f'{label} pylon attachment hardware {yi}','steel',Mesh.merged(bolts),detail_count=4)
        # A geometrically original, visually inert training store on each wingtip.
        store=label+' wingtip training store'
        yy=side*5.94
        s.add(store,'Inert cylindrical display body','white',body_loft([(10.05,.012,2.40,.012,.012),(10.25,.063,2.40,.063,.063),(10.7,.064,2.40,.064,.064),(12.52,.064,2.40,.064,.064),(12.90,.035,2.40,.035,.035)],segments=40,center_y=yy))
        s.add(store,'Dark inert seeker cover','black',sphere((10.17,yy,2.40),(.13,.065,.065),24,12))
        fins=[]
        for x,width in ((10.85,.18),(12.48,.29)):
            for ang in [math.pi/4+k*math.pi/2 for k in range(4)]:
                direction=(0,math.cos(ang),math.sin(ang));p0=(x,yy,2.4)
                ps=[add(p0,mul(direction,.06)),add(add(p0,(.31,0,0)),mul(direction,.06)),add(add(p0,(.33,0,0)),mul(direction,width)),add(add(p0,(.15,0,0)),mul(direction,width))]
                fins.append(prism(ps,(0,-math.sin(ang)*.003,math.cos(ang)*.003)))
        s.add(store,'Inert display fins','skin_panel',Mesh.merged(fins),detail_count=8)
        for x in (10.55,12.13):s.add(store,f'Blue inert band {x}','blue',cylinder((x,yy,2.4),(x+.07,yy,2.4),.065,40))
        s.fixed(label+' rail mount',fold,store)
    # Centreline fuel tank, hollow-looking seams and pylon.
    s.add('Airframe','Centreline fuel tank','skin_lower',body_loft([(7.2,.01,.90,.01,.01),(7.5,.22,.90,.23,.23),(8.1,.32,.90,.32,.32),(9.5,.33,.90,.33,.33),(10.7,.27,.90,.27,.27),(11.55,.02,.90,.02,.02)],segments=64))
    s.add('Airframe','Centreline tank pylon','skin_lower',box((9.0,0,1.35),(1.3,.15,.28)))
    s.add('Airframe','Fuel tank equatorial seam','seam',tube([(x,0,.90+h+.002) for x,w,z,h,d in stations([(7.5,.22,.90,.23,.23),(8.1,.32,.90,.32,.32),(9.5,.33,.90,.33,.33),(10.7,.27,.90,.27,.27),(11.4,.08,.90,.08,.08)],.12)],.002,6))

def build_tails(s):
    for side,label in ((-1,'Port'),(1,'Starboard')):
        # Fins canted 20 degrees; planar polygon with thin tapered depth.
        def fp(x,z,offset=0):return (x,side*(.88+(z-2.38)*.364+offset),z)
        fin=[fp(11.85,2.40),fp(14.02,4.66),fp(15.10,4.66),fp(14.90,3.94),fp(14.52,3.94),fp(13.96,2.51)]
        s.add('Airframe',label+' canted fin fixed surface','composite',prism(fin,(0,side*.055,0)))
        rud=label+' rudder';ps=[fp(14.52,3.94),fp(15.07,3.94),fp(14.48,2.53),fp(13.96,2.51)]
        s.add(rud,'Rudder surface','composite',prism(ps,(0,side*.058,0)))
        axis=sub(fp(14.52,3.94),fp(13.96,2.51));s.joint(label+' rudder','Airframe',rud,fp(13.96,2.51),axis,(-30,30),0)
        # Root strengthening pad, hinge lines, RWR tips and low visibility identity.
        s.add('Airframe',label+' fin root reinforcement','skin_panel',tube([fp(11.86,2.40),fp(14.5,2.53)],.043,10))
        s.add('Airframe',label+' fin leading cap','gray',tube([fp(11.87,2.43),fp(14.03,4.66),fp(15.08,4.66)],.018,10))
        s.add('Airframe',label+' fin tip sensor','gray',cylinder(fp(14.03,4.69),fp(14.51,4.69),.043,20))
        s.add('Airframe',label+' fin slime light','cream',prism([fp(13.69,3.43,.034),fp(14.13,3.43,.034),fp(14.15,3.49,.034),fp(13.71,3.49,.034)],(0,side*.004,0)))
        # NG and 301 stencils orient on each outward face.
        up=unit((0,side*.364,1));right=(1,0,0) if side<0 else (-1,0,0)
        for txt,x,z,h in [('NG',13.55 if side<0 else 14.65,4.10,.40),('301',13.55 if side<0 else 14.42,3.73,.22),('VFA-146',12.94 if side<0 else 14.24,3.06,.13)]:
            s.add('Airframe',label+' tail '+txt,'paint_dark',text(txt,fp(x,z,.064),h,right,up,.001))
        diamond=[fp(13.35,3.49,.064),fp(13.62,3.69,.064),fp(13.89,3.49,.064),fp(13.62,3.29,.064)]
        s.add('Airframe',label+' Blue Diamonds emblem','blue',prism(diamond,(0,side*.001,0)))
        # Full-moving horizontal stabilators.
        comp=label+' stabilator'
        rows=[(side*.84,13.04,16.67,2.12,.039),(side*3.29,15.78,17.07,2.04,.037)]
        wing_patch(s,comp,'All moving stabilator',rows)
        s.add(comp,'Stabilator pivot trunnion','steel',cylinder((14.73,side*.72,2.12),(14.73,side*1.13,2.12),.11,32))
        s.joint(label+' stabilator pitch','Airframe',comp,(14.73,side*.84,2.12),(0,1,0),(-25,25),-4)
        wicks=[cylinder((16.93,side*y,2.04),(17.07,side*y,2.04),.003,8) for y in (2.9,3.15)]
        s.add(comp,'Stabilator discharge wicks','black',Mesh.merged(wicks),detail_count=2)
    # Dorsal speedbrake lies closed in the default launch pose.
    panel=[(7.0,-.49,2.854),(9.53,-.60,2.735),(9.76,-.38,2.705),(9.76,.38,2.705),(9.53,.60,2.735),(7.0,.49,2.854)]
    s.add('Speedbrake','Dorsal airbrake panel','composite',prism(panel,(0,0,.022)))
    ribs=[box((7.35+i*.34,0,2.827-i*.017),(.035,.90,.045)) for i in range(6)]
    s.add('Speedbrake','Speedbrake underside ribs','aluminum',Mesh.merged(ribs),detail_count=6)
    s.joint('Dorsal speedbrake','Airframe','Speedbrake',(7.0,0,2.85),(0,-1,0),(0,60),0)

def tire_mesh(center,radius,width):
    x,y,z=center;vs=[];fs=[];segments=72
    profile=[(-width/2,.56*radius),(-width*.53,.73*radius),(-width*.45,.92*radius),(-width*.30,radius),(width*.30,radius),(width*.45,.92*radius),(width*.53,.73*radius),(width/2,.56*radius)]
    for yy,r in profile:
        for i in range(segments):
            a=2*math.pi*i/segments;vs.append((x+r*math.cos(a),y+yy,z+r*math.sin(a)))
    for j in range(len(profile)):
        nj=(j+1)%len(profile)
        for i in range(segments):
            ni=(i+1)%segments;a=j*segments+i;b=j*segments+ni;c=nj*segments+ni;d=nj*segments+i
            fs.extend([(a,c,b),(a,d,c)])
    return Mesh(vs,fs)

def wheel(s,component,name,center,radius,width):
    s.add(component,name+' tyre','tire',tire_mesh(center,radius,width))
    x,y,z=center
    s.add(component,name+' wheel alloy hub','gear_white',cylinder((x,y-width*.44,z),(x,y+width*.44,z),radius*.55,48))
    s.add(component,name+' axle cap','steel',cylinder((x,y-width*.55,z),(x,y+width*.55,z),radius*.17,32))
    grooves=[];nuts=[];holes=[]
    for yy in (-width*.2,0,width*.2):grooves.append(torus((x,y+yy,z),radius*.997,.0035,axis=(0,1,0),segments=72,sides=5))
    for side in (-1,1):
        for j in range(10):
            a=2*math.pi*j/10
            pp=(x+radius*.36*math.cos(a),y+side*width*.454,z+radius*.36*math.sin(a))
            nuts.append(cylinder(pp,add(pp,(0,side*.010,0)),.012 if radius>.35 else .009,6))
            pp=(x+radius*.45*math.cos(a+.12),y+side*width*.447,z+radius*.45*math.sin(a+.12))
            holes.append(cylinder(pp,add(pp,(0,side*.002,0)),.025 if radius>.35 else .015,16))
    s.add(component,name+' tread grooves','black',Mesh.merged(grooves),detail_count=3)
    s.add(component,name+' hub fasteners','steel',Mesh.merged(nuts),detail_count=20)
    s.add(component,name+' wheel vents','steel_dark',Mesh.merged(holes),detail_count=20)

def build_gear(s):
    # Nose gear at 5.55 m; mains at 10.97 m; track 3.11 m.
    nose='Nose gear leg'
    s.add(nose,'Nose gear upper strut','gear_white',cylinder((5.45,0,1.73),(5.48,0,.83),.075,32))
    s.add(nose,'Exposed oleo piston','stainless',cylinder((5.48,0,.94),(5.52,0,.53),.047,32))
    s.add(nose,'Torque scissor links','gear_white',Mesh.merged([cylinder((5.53,0,.92),(5.74,0,.72),.022,16),cylinder((5.74,0,.72),(5.55,0,.54),.022,16)]))
    s.add(nose,'Nose drag brace','gear_white',Mesh.merged([cylinder((6.26,0,1.53),(5.73,0,.98),.032,20),cylinder((5.73,0,.98),(5.48,0,.80),.035,20)]))
    fork='Nose wheel steering'
    for side in (-1,1):s.add(fork,f'Fork arm {side}','gear_white',cylinder((5.52,side*.115,.63),(5.55,side*.17,.31),.035,20))
    s.add(fork,'Steering cross head','gear_white',box((5.52,0,.60),(.14,.30,.09)))
    s.joint('Nose gear retract','Airframe',nose,(5.45,0,1.73),(0,1,0),(-96,0),0)
    s.joint('Nose wheel steering',nose,fork,(5.52,0,.65),(0,0,1),(-65,65),0)
    for side,label in ((-1,'Port'),(1,'Starboard')):
        comp='Nose '+label+' wheel';center=(5.55,side*.20,.31)
        wheel(s,comp,'Nose '+label,center,.31,.13)
        s.joint('Nose '+label+' wheel spin',fork,comp,center,(0,1,0),(-360,360),0)
    # Launch bar terminates near the deck shuttle; entirely a visual linkage.
    comp='Launch bar';pivot=(5.39,0,.60)
    s.add(comp,'Launch bar forged arms','steel',Mesh.merged([cylinder(pivot,(4.73,-.10,.10),.032,20),cylinder(pivot,(4.73,.10,.10),.032,20)]))
    s.add(comp,'Launch shuttle engagement cross pin','steel',cylinder((4.71,-.17,.09),(4.71,.17,.09),.040,24))
    s.joint('Launch bar lift',fork,comp,pivot,(0,1,0),(-75,0),0)
    s.add(nose,'Nose gear brake and hydraulic lines','black',tube([(5.38,.085,1.57),(5.40,.10,1.10),(5.60,.13,.72),(5.58,.13,.40)],.008,8))
    s.add(nose,'Taxi lamp housing','gear_white',cylinder((5.40,0,.78),(5.31,0,.78),.062,24))
    s.add(nose,'Taxi lamp lens','glass',cylinder((5.305,0,.78),(5.315,0,.78),.053,32))
    s.add('Airframe','Nose gear bay dark cavity','black',box((5.55,0,1.745),(1.67,.52,.04)))
    # Door inner faces have visible ribs and painted edges in the gear-down pose.
    for side,label in ((-1,'Port'),(1,'Starboard')):
        comp='Nose '+label+' door';y=side*.28
        s.add(comp,'Nose door outer skin','skin_lower',box((5.65,y+side*.19,1.72),(1.56,.38,.026)))
        s.add(comp,'Nose door inner liner','gear_white',box((5.65,y+side*.19,1.739),(1.49,.34,.012)))
        ribs=[box((5.03+i*.24,y+side*.19,1.755),(.022,.31,.022)) for i in range(6)]
        s.add(comp,'Door reinforcement ribs','gear_white',Mesh.merged(ribs),detail_count=6)
        s.joint('Nose '+label+' door','Airframe',comp,(5.65,y,1.72),(-side,0,0),(0,95),83)
    for side,label in ((-1,'Port'),(1,'Starboard')):
        comp=label+' main gear';root=(10.53,side*.74,1.70);elbow=(10.89,side*1.25,.85);axle=(10.97,side*1.555,.405)
        s.add(comp,'Main oleo upper barrel','gear_white',cylinder(root,elbow,.115,36))
        s.add(comp,'Main oleo chrome piston','stainless',cylinder(elbow,axle,.069,32))
        s.add(comp,'Main torque scissor','gear_white',Mesh.merged([cylinder(add(elbow,(-.12,0,0)),(11.12,side*1.38,.66),.031,18),cylinder((11.12,side*1.38,.66),add(axle,(-.09,0,.08)),.031,18)]))
        s.add(comp,'Side stay and drag brace','gear_white',Mesh.merged([cylinder((9.98,side*.9,1.49),(10.62,side*1.24,.92),.045,24),cylinder((10.62,side*1.24,.92),axle,.045,24),cylinder((11.68,side*.75,1.48),(11.03,side*1.18,.86),.037,20)]))
        s.add(comp,'Axle spindle','steel',cylinder(add(axle,(0,-.18,0)),add(axle,(0,.18,0)),.07,32))
        s.add(comp,'Brake hydraulic pipes','black',tube([add(root,(.10,side*.1,0)),(10.75,side*1.23,1.03),(10.94,side*1.37,.61),add(axle,(0,-side*.17,0))],.010,8))
        s.add(comp,'Brake rotor pack','steel_dark',cylinder(add(axle,(0,-side*.14,0)),add(axle,(0,-side*.20,0)),.21,48))
        s.joint(label+' main gear retract','Airframe',comp,root,(1,0,0),(-115 if side>0 else 0,115 if side<0 else 0),0)
        wh=label+' main wheel';wheel(s,wh,'Main '+label,axle,.405,.24)
        s.joint(label+' main wheel spin',comp,wh,axle,(0,1,0),(-360,360),0)
        door=label+' main gear door'
        pp=[(10.06,side*.94,1.39),(11.66,side*.94,1.39),(11.68,side*1.48,1.38),(10.50,side*1.48,1.38)]
        s.add(door,'Main bay door skin','skin_lower',prism(pp,(0,0,.033)))
        s.add(door,'Main bay door liner','gear_white',prism([(p[0],p[1],p[2]+.038) for p in pp],(0,0,.008)))
        ribs=[cylinder((10.4+i*.22,side*1.0,1.45),(10.4+i*.22,side*1.42,1.44),.012,10) for i in range(6)]
        s.add(door,'Bay door ribs','gear_white',Mesh.merged(ribs),detail_count=6)
        s.joint(label+' main bay door','Airframe',door,(10.8,side*.94,1.39),(-side,0,0),(0,100),87)
        s.add('Airframe',label+' main bay recess','black',box((10.85,side*.80,1.395),(1.72,.65,.035)))

def build_exhausts(s):
    for side,label in ((-1,'Port'),(1,'Starboard')):
        y=side*.61;z=2.03
        s.add('Airframe',label+' hot section fairing','hot_metal',body_loft([(15.54,.48,z,.48,.48),(16.06,.45,z,.45,.45)],segments=64,center_y=y))
        # A short inward dark tube, nested rings and static visual turbine disk.
        rings=[]
        for x,r in ((16.03,.43),(15.90,.41),(15.75,.39),(15.58,.36)):
            rings.append(torus((x,y,z),r,.024,(1,0,0),64,8))
        s.add('Airframe',label+' exhaust liner rings','exhaust',Mesh.merged(rings),detail_count=4)
        s.add('Airframe',label+' turbine shadow disk','black',cylinder((15.53,y,z),(15.55,y,z),.35,64))
        vanes=[]
        for k in range(32):
            a=2*math.pi*k/32
            ps=[(15.56,y+.11*math.cos(a),z+.11*math.sin(a)),(15.56,y+.34*math.cos(a+.09),z+.34*math.sin(a+.09)),(15.56,y+.34*math.cos(a+.16),z+.34*math.sin(a+.16)),(15.56,y+.11*math.cos(a+.12),z+.11*math.sin(a+.12))]
            vanes.append(prism(ps,(.004,0,0)))
        s.add('Airframe',label+' visible exhaust vane pattern','steel_dark',Mesh.merged(vanes),detail_count=32)
        # External variable-area nozzle petals are separate native moving parts.
        for k in range(12):
            a=2*math.pi*k/12;b=a+2*math.pi/12*.94
            comp=f'{label} nozzle petal {k+1:02d}'
            p0=(16.04,y+.453*math.cos(a),z+.453*math.sin(a));p1=(16.04,y+.453*math.cos(b),z+.453*math.sin(b))
            p2=(16.68,y+.35*math.cos(b),z+.35*math.sin(b));p3=(16.68,y+.35*math.cos(a),z+.35*math.sin(a))
            n=(0,math.cos((a+b)/2),math.sin((a+b)/2))
            s.add(comp,'Titanium nozzle petal','titanium' if k%3 else 'blue_heat',prism([p0,p1,p2,p3],mul(n,.008)))
            s.add(comp,'Petal longitudinal reinforcement','hot_metal',tube([lerp(p0,p1,.50),lerp(p3,p2,.50)],.012,8))
            hinge=lerp(p0,p1,.50);axis=(0,-math.sin((a+b)/2),math.cos((a+b)/2))
            s.joint(f'{label} nozzle opening {k+1:02d}','Airframe',comp,hinge,axis,(-8,10),-3)

def build_misc(s):
    # Arresting hook below the aft belly, stowed for launch.
    pp=(13.05,0,1.51)
    s.add('Arresting hook','Hook shank','steel',cylinder(pp,(16.21,0,1.43),.037,28))
    s.add('Arresting hook','Hook shoe','steel_dark',tube([(16.17,0,1.43),(16.40,0,1.38),(16.47,0,1.46),(16.44,0,1.58)],.045,12))
    bands=[]
    for i in range(11):bands.append(cylinder((13.18+i*.25,0,1.507-i*.006),(13.29+i*.25,0,1.504-i*.006),.039,20))
    s.add('Arresting hook','Hook white bands','white',Mesh.merged(bands),detail_count=11)
    s.joint('Arresting hook lower','Airframe','Arresting hook',pp,(0,1,0),(0,42),0)
    # Refuelling probe stowed on starboard shoulder; hinge opens outward.
    comp='Refuelling probe';p=(4.23,.58,2.72)
    s.add(comp,'Probe alloy boom','aluminum',tube([p,(3.66,.61,2.75),(3.15,.63,2.80),(2.91,.68,2.82)],.024,16))
    s.add(comp,'Probe nozzle external fitting','steel',cylinder((2.91,.68,2.82),(2.78,.69,2.83),.038,24))
    s.joint('Refuelling probe extend','Airframe',comp,p,(0,0,-1),(0,65),0)
    cover='Refuelling probe door'
    s.add(cover,'Probe fairing access cover','skin',box((3.62,.64,2.77),(1.35,.065,.14)))
    s.joint('Probe door open','Airframe',cover,(3.62,.62,2.83),(1,0,0),(0,95),0)
    # Boarding ladder, inset into port LEX in closed pose.
    comp='Boarding ladder';hinge=(4.89,-.82,2.61)
    rails=[]
    for y in (-.70,-.94):rails.append(cylinder((4.89,y,2.61),(6.02,y,2.61),.020,16))
    for i in range(5):rails.append(cylinder((4.96+i*.22,-.70,2.61),(4.96+i*.22,-.94,2.61),.018,16))
    s.add(comp,'Folding ladder rungs and rails','aluminum',Mesh.merged(rails),detail_count=7)
    # Ladder built in a horizontal stowed envelope; rotating opens downward.
    s.joint('Boarding ladder deploy','Airframe',comp,hinge,(0,1,0),(0,90),0)
    s.add('Airframe','Boarding ladder flush cover','skin',box((5.46,-.82,2.64),(1.17,.29,.018)))
    # AOA probes, pitot-like air-data vanes, IFF features and nose service ports.
    for side in (-1,1):
        s.add('Airframe',f'Air data probe {side}','steel',cylinder((2.15,side*.50,2.21),(2.0,side*.78,2.23),.011,16,radius2=.004))
        s.add('Airframe',f'AOA vane {side}','aluminum',prism([(2.63,side*.56,2.19),(2.54,side*.73,2.17),(2.76,side*.67,2.17)],(0,0,.006)))
        s.add('Airframe',f'Forward RWR blister {side}','gray',sphere((1.91,side*.50,2.22),(.09,.06,.07),24,12))
        s.add('Airframe',f'Aft RWR blister {side}','gray',sphere((15.5,side*.94,2.15),(.11,.07,.08),24,12))
    iff=[]
    for y in (-.16,-.055,.055,.16):
        iff.append(prism([(3.03,y,2.80),(3.24,y,2.83),(3.15,y,2.92),(3.08,y,2.90)],(0,.018,0)))
    s.add('Airframe','Four IFF bird slicer antenna blades','gray',Mesh.merged(iff),detail_count=4)
    # Large star and bars on the port upper wing, starboard lower wing and sides.
    for side in (-1,1):
        yy=side*1.00;x=11.2;z=2.18;pts=[]
        for i in range(10):
            a=math.pi/2+math.pi*i/5;r=.18 if i%2==0 else .075
            pts.append((x+r*math.cos(a),yy,z+r*math.sin(a)))
        s.add('Airframe',f'National star insignia {side}','paint_dark',prism(pts,(0,side*.002,0)))
        s.add('Airframe',f'Insignia bars {side}','paint_dark',box((x,yy,z),(.65,.003,.075)))

