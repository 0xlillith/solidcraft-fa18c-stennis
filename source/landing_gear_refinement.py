"""Original Legacy Hornet landing-gear refinement for exact SolidCraft RC3.

Reference-supported features: forward nose retraction, aft main retraction,
horizontal main wheel stow, shrink/planing links, trailing-arm main suspension,
twin 22x6.6-10 nose tyres and single 30x11.5-14.5 main tyres. Small pivots and
link lengths below are authored visual approximations, not aircraft engineering.

All mechanism parts use scalar native revolute/slider joints. Passive closed
loops use the verified RC3 coplanar mechanism solver. There is no image render.
"""
from scene_api import *
import math


SOURCES = [
    {"id":"gear-tire-primary","title":"NAVAIR 04-10-506, Aircraft Tires and Tubes, Table4-1",
     "url":"https://navytribe.com/wp-content/uploads/2015/11/navair-04-10-506.pdf",
     "claim":"F-18A-D main30x11.5-14.5 and nose22x6.6-10; DistributionA public release."},
    {"id":"gear-main-photo","title":"Julian Herzog, HN-441 F/A-18C main gear, ILA2012",
     "url":"https://commons.wikimedia.org/wiki/File:HN-441_F-A-18C_Hornet_Finnish_Air_Force_ILA_2012_main_landing_gear.jpg",
     "license":"CC BY4.0","claim":"Visual reference for trailing arm, oleo, planing/shrink hardware, lines and fittings; no mesh copied."},
    {"id":"gear-directions","title":"F/A-18A/B/C/D NATOPS, section2.10.1",
     "url":"https://letsflyvfr.com/wp-content/uploads/2024/11/F-18-A-b-C-D-Hornet-NATOPS-FLIGHT-MANUAL.pdf",
     "claim":"Only broad external behavior used: nose forward, mains aft, doors open when gear down."},
    {"id":"gear-dcs","title":"Eagle Dynamics, F/A-18C landing-gear update,16 February2024",
     "url":"https://www.digitalcombatsimulator.com/en/news/2024-02-16/",
     "claim":"Reference that Hornet shock/gear articulation is complex; no DCS asset data used."},
]


def _joint(s,name,parent,child,origin,axis,limits=(-180,180),default=0,kind='revolute',passive=False):
    s.joint(name,parent,child,origin,axis,limits,default,kind)
    if passive:s.joints[-1]['passive']=True


def _link(s,a,b,ratio,offset=0):
    if not hasattr(s,'motion_links'):s.motion_links=[]
    s.motion_links.append(dict(a=a,b=b,ratio=ratio,offset=offset))


def _ring(center,axis,outer,inner,width,n=48):
    """Closed annulus with distinct normals at face/rim boundaries."""
    u,v,w=basis(axis);meshes=[]
    profile=[(-width/2,outer),(width/2,outer),(width/2,inner),(-width/2,inner)]
    for k in range(4):
        ya,ra=profile[k];yb,rb=profile[(k+1)%4];vs=[];fs=[]
        for y,r in ((ya,ra),(yb,rb)):
            vs.extend(add(center,add(mul(w,y),add(mul(u,r*math.cos(i*2*math.pi/n)),mul(v,r*math.sin(i*2*math.pi/n))))) for i in range(n))
        for i in range(n):
            j=(i+1)%n;fs.extend([(i,j,n+j),(i,n+j,n+i)])
        meshes.append(Mesh(vs,fs))
    return Mesh.merged(meshes)


def _pins(s,component,label,points,axis,r=.022,width=.075):
    w=unit(axis);pins=[];caps=[]
    for p in points:
        pins.append(cylinder(add(p,mul(w,-width/2)),add(p,mul(w,width/2)),r,24))
        for side in (-1,1):
            a=add(p,mul(w,side*width/2));b=add(a,mul(w,side*.007))
            caps.append(cylinder(a,b,r*1.3,6))
    s.add(component,label+' hinge pins','stainless',Mesh.merged(pins),detail_count=len(points))
    s.add(component,label+' castle nut heads','steel',Mesh.merged(caps),detail_count=2*len(points))


def _tyre(center,radius,width,rim):
    x,y,z=center;n=96;vs=[];fs=[]
    profile=[(-width*.49,rim*.99),(-width*.50,radius*.70),(-width*.46,radius*.89),
             (-width*.35,radius*.98),(-width*.28,radius)]
    for g in (-width*.20,0,width*.20):
        profile.extend([(g-.005,radius),(g-.003,radius-.004),(g+.003,radius-.004),(g+.005,radius)])
    profile.extend([(width*.28,radius),(width*.35,radius*.98),(width*.46,radius*.89),
                    (width*.50,radius*.70),(width*.49,rim*.99)])
    for yy,r in profile:
        vs.extend((x+r*math.cos(i*2*math.pi/n),y+yy,z+r*math.sin(i*2*math.pi/n)) for i in range(n))
    for k in range(len(profile)):
        q=(k+1)%len(profile)
        for i in range(n):
            j=(i+1)%n;a=k*n+i;b=k*n+j;c=q*n+j;d=q*n+i
            fs.extend([(a,c,b),(a,d,c)])
    return Mesh(vs,fs)


def _wheel(s,component,label,center,radius,width,rim):
    x,y,z=center
    s.add(component,label+' tyre with recessed circumferential grooves','tire',_tyre(center,radius,width,rim))
    s.add(component,label+' forged alloy rim barrel','gear_wheel_alloy',_ring(center,(0,1,0),rim,rim*.70,width*.86,64))
    s.add(component,label+' hub diaphragm','gear_wheel_alloy',cylinder((x,y-width*.10,z),(x,y+width*.10,z),rim*.72,64))
    lips=[];nuts=[];vents=[];studs=[]
    for side in (-1,1):
        lips.append(_ring((x,y+side*width*.44,z),(0,1,0),rim*1.055,rim*.88,.017,64))
        for j in range(12):
            a=2*math.pi*j/12
            p=(x+rim*.79*math.cos(a),y+side*width*.46,z+rim*.79*math.sin(a))
            nuts.append(cylinder(p,add(p,(0,side*.012,0)),.0095 if radius>.3 else .007,6))
            p=(x+rim*.57*math.cos(a+.12),y+side*width*.105,z+rim*.57*math.sin(a+.12))
            vents.append(cylinder(p,add(p,(0,side*.003,0)),rim*.075,16))
        studs.append(cylinder((x,y+side*width*.1,z),(x,y+side*width*.51,z),rim*.25,32))
    s.add(component,label+' bead retaining lips','gear_wheel_alloy',Mesh.merged(lips),detail_count=2)
    s.add(component,label+' split rim fastening nuts','steel',Mesh.merged(nuts),detail_count=24)
    s.add(component,label+' recessed hub ports','steel_dark',Mesh.merged(vents),detail_count=24)
    s.add(component,label+' bearing boss and grease cap','stainless',Mesh.merged(studs),detail_count=2)
    s.add(component,label+' inflation valve','brass',cylinder((x+rim*.60,y+width*.46,z),(x+rim*.65,y+width*.48,z),.006,12))


def _actuator(s,prefix,parent,child,a,b,axis,radius=.031):
    """True R-S-R loop: both pins and the slider axis lie in one plane."""
    barrel=prefix+' barrel';rod=prefix+' piston';direction=unit(sub(b,a));span=length(sub(b,a))
    # The barrel contains the piston at neutral; generous overlap admits the
    # visual mechanism's short motion range without detached visible shafts.
    barrel_len=span*.76;rod_start=span*.22
    s.add(barrel,'Cylinder outer sleeve','gear_white',cylinder(a,add(a,mul(direction,barrel_len)),radius,32))
    for t in (.08,.72):
        s.add(barrel,'Sleeve reinforcing collar '+str(t),'steel',_ring(add(a,mul(direction,span*t)),direction,radius*1.13,radius*.97,.022,32))
    s.add(rod,'Polished piston shaft','stainless',cylinder(add(a,mul(direction,rod_start)),b,radius*.48,32))
    s.add(rod,'Rod-end eye','gear_white',_ring(b,axis,radius*.94,radius*.34,radius*1.65,28))
    _pins(s,barrel,'Actuator base',[a],axis,radius*.38,radius*2.2)
    _pins(s,rod,'Actuator rod end',[b],axis,radius*.32,radius*1.8)
    _joint(s,prefix+' base swivel',parent,barrel,a,axis,(-180,180),passive=True)
    _joint(s,prefix+' working stroke',barrel,rod,a,direction,(-span*.75,span*1.2),kind='slider',passive=True)
    _joint(s,prefix+' rod swivel',child,rod,b,axis,(-180,180),passive=True)


def _two_link(s,prefix,parent,child,a,b,axis,bar_length,bend=-1,radius=.027):
    v=sub(b,a);d=length(v)
    if d>=2*bar_length:raise ValueError('Unreachable authored brace '+prefix)
    e=add(lerp(a,b,.5),mul(unit(cross(axis,v)),bend*math.sqrt(bar_length**2-(d/2)**2)))
    upper=prefix+' upper';lower=prefix+' lower'
    for name,p,q in ((upper,a,e),(lower,e,b)):
        direction=unit(sub(q,p));off=mul(unit(axis),radius*1.15)
        bars=[cylinder(add(p,off),add(q,off),radius*.65,16),
              cylinder(sub(p,off),sub(q,off),radius*.65,16)]
        bars.extend([_ring(p,axis,radius*1.55,radius*.55,radius*2.6,24),
                     _ring(q,axis,radius*1.55,radius*.55,radius*2.6,24)])
        s.add(name,'Forked link and bored eyes','gear_white',Mesh.merged(bars),detail_count=4)
        _pins(s,name,'Linkage',[p,q],axis,radius*.55,radius*3.8)
    _joint(s,prefix+' airframe hinge',parent,upper,a,axis,(-180,180),passive=True)
    _joint(s,prefix+' elbow hinge',upper,lower,e,axis,(-180,180),passive=True)
    _joint(s,prefix+' moving hinge',child,lower,b,axis,(-180,180),passive=True)
    return e


def _matrix_axisangle(m):
    angle=math.acos(max(-1,min(1,(m[0][0]+m[1][1]+m[2][2]-1)/2)))
    if angle<1e-8:return (1,0,0),0
    axis=unit((m[2][1]-m[1][2],m[0][2]-m[2][0],m[1][0]-m[0][1]))
    return axis,math.degrees(angle)


def _retract_frames(side):
    p=(10.40,side*.74,1.72);k=(10.52,side*1.435,.47);w=(10.97,side*1.555,.381)
    target_k=(11.65,side*.67,1.50)
    v0=sub(k,p);v1=sub(target_k,p);axis=unit(cross(v0,v1))
    angle=math.degrees(math.acos(dot(unit(v0),unit(v1))))
    # Keep legacy joint sign convention: port positive, starboard negative.
    if side>0:axis=mul(axis,-1);angle=-angle
    shrink=length(v1)-length(v0)
    normal=(0,side,0);long0=unit(sub(sub(w,k),mul(normal,.12)))
    long1=unit((-.44,side*.13,0))
    across0=cross(normal,long0);normal1=(0,0,1);across1=cross(normal1,long1)
    # Desired complete rigid orientation: wheel axle points up and tyre is flat.
    target=[[long1[r]*long0[c]+across1[r]*across0[c]+normal1[r]*normal[c] for c in range(3)] for r in range(3)]
    base=[[rot(tuple(1 if q==c else 0 for q in range(3)),(0,0,0),axis,math.radians(angle))[r] for c in range(3)] for r in range(3)]
    secondary=[[sum(base[q][r]*target[q][c] for q in range(3)) for c in range(3)] for r in range(3)]
    plane_axis,plane_angle=_matrix_axisangle(secondary)
    target_w=add(target_k,tuple(sum(target[r][c]*(w[c]-k[c]) for c in range(3)) for r in range(3)))
    return dict(p=p,k=k,w=w,axis=axis,angle=angle,shrink=shrink,plane_axis=plane_axis,
                plane_angle=plane_angle,target_k=target_k,target_w=target_w)


def _remove_baseline(s):
    names={'Nose gear leg','Nose wheel steering','Nose Port wheel','Nose Starboard wheel','Launch bar',
           'Nose Port door','Nose Starboard door'}
    for label in ('Port','Starboard'):
        names.update({label+' main gear',label+' main wheel',label+' main gear door'})
    labels={'Nose gear bay dark cavity','Port main bay recess','Starboard main bay recess'}
    removed={p['name'] for p in s.bodies if p['component'] in names or p.get('label') in labels}
    s.bodies[:]=[p for p in s.bodies if p['name'] not in removed]
    for name in list(s.components):
        if name in names:del s.components[name]
        else:s.components[name]['parts'][:]=[p for p in s.components[name]['parts'] if p['name'] not in removed]
    s.joints[:]=[j for j in s.joints if j['parent'] not in names and j['child'] not in names]
    s._names={p['name'] for p in s.bodies}


def _main(s,label,side):
    f=_retract_frames(side);p,k,w=f['p'],f['k'],f['w'];direction=unit(sub(k,p))
    root=label+' main gear';shrink=label+' main shrink strut'
    planing=label+' main planing cradle';arm=label+' main suspension arm';wheel=label+' main wheel'
    s.add(root,'Forged upper trunnion head','gear_white',cylinder(add(p,mul(f['axis'],-.11)),add(p,mul(f['axis'],.11)),.115,40))
    s.add(root,'Main load bearing barrel','gear_white',cylinder(add(p,mul(direction,.045)),add(p,mul(direction,.81)),.065,40,radius2=.055))
    s.add(root,'Barrel reinforcing bands','gear_white',Mesh.merged([_ring(add(p,mul(direction,t)),direction,.081,.074,.05,32) for t in (.16,.37,.76)]),detail_count=3)
    s.add(root,'Gland and sliding seal','black',_ring(add(p,mul(direction,.805)),direction,.067,.045,.018,32))
    s.add(shrink,'Main retract shrink polished tube','stainless',cylinder(add(p,mul(direction,.62)),k,.048,40))
    s.add(shrink,'Lower steering planing housing','gear_white',sphere(k,(.080,.072,.072),32,16))
    _pins(s,root,'Trunnion',[p],f['axis'],.055,.29)
    _joint(s,label+' main gear retract','Airframe',root,p,f['axis'],(min(0,f['angle']),max(0,f['angle'])),0)
    _joint(s,label+' main shrink travel',root,shrink,p,direction,(f['shrink']-.015,.015),0,'slider')
    _link(s,label+' main gear retract',label+' main shrink travel',1000*f['shrink']/f['angle'])
    s.add(planing,'Lower planing swivel knuckle','gear_white',cylinder(add(k,mul(f['plane_axis'],-.050)),add(k,mul(f['plane_axis'],.050)),.060,32))
    _joint(s,label+' main wheel planing',shrink,planing,k,f['plane_axis'],(-.1,f['plane_angle']+.1),0)
    _link(s,label+' main gear retract',label+' main wheel planing',f['plane_angle']/f['angle'])
    c=(w[0],k[1],w[2]);axis=(0,1,0)
    shock_a=add(k,(.25,0,.35));shock_b=add(k,(.33,0,-.065))
    s.add(planing,'Shock upper bracket','gear_white',Mesh.merged([
        cylinder(add(k,(.015,-.045,0)),add(shock_a,(0,-.045,0)),.031,20),
        cylinder(add(k,(.015,.045,0)),add(shock_a,(0,.045,0)),.031,20),
        cylinder(add(shock_a,(0,-.055,0)),add(shock_a,(0,.055,0)),.043,24)]),detail_count=3)
    links=[]
    for yy in (-.025,.025):
        links.append(cylinder(add(k,(0,yy,0)),add(c,(0,yy,0)),.036,24,radius2=.044))
    links.extend([sphere(k,(.09,.075,.071),24,12),sphere(c,(.072,.08,.071),24,12)])
    s.add(arm,'Forged trailing suspension fork','gear_white',Mesh.merged(links),detail_count=4)
    s.add(arm,'Wheel axle spindle','stainless',cylinder(add(c,(0,-side*.055,0)),add(w,(0,side*.143,0)),.037,32))
    _pins(s,arm,'Trailing arm pivot',[k],axis,.030,.14)
    _joint(s,label+' main oleo compression',planing,arm,k,axis,(-12,14),0)
    _actuator(s,label+' main oleo',planing,arm,shock_a,shock_b,axis,.043)
    # A coplanar two-link drag brace follows the primary trunnion rotation.
    normal=f['axis'] if side<0 else mul(f['axis'],-1)
    brace_a=sub(p,mul(unit(cross(normal,direction)),.34))
    brace_b=add(p,mul(direction,.56))
    _two_link(s,label+' main drag brace','Airframe',root,brace_a,brace_b,normal,.46,bend=-1,radius=.022)
    # This pin and lug are visible attachment hardware, not separate unconstrained parts.
    s.add(root,'Retraction lug','gear_white',cylinder(add(p,mul(direction,.39)),add(add(p,mul(direction,.39)),(.11,0,.02)),.040,24))
    s.add(shrink,'Planing linkage tie rod','stainless',cylinder(add(k,(-.18,side*.065,.23)),add(k,(.04,side*.065,.02)),.013,20))
    s.add(planing,'Lower tie down ring','steel',_ring(add(k,(-.065,side*.045,-.045)),(0,1,0),.042,.025,.015,32))
    s.add(root,'Rigid hydraulic feed pipes','stainless',Mesh.merged([
        tube([add(p,(.06,side*.045,-.05)),add(p,mul(direction,.32)),add(p,add(mul(direction,.68),(.065,side*.04,0)))],.006,10),
        tube([add(p,(-.06,side*.04,-.08)),add(p,add(mul(direction,.48),(-.05,side*.04,0))),add(p,add(mul(direction,.73),(-.035,side*.04,0)))],.005,10)]),detail_count=2)
    s.add(arm,'Brake flexible hydraulic hose','black',tube([
        add(k,(.07,side*.07,.04)),add(k,(.18,side*.08,.07)),
        add(c,(-.12,side*.06,.06)),add(c,(-.015,side*.075,.035))],.008,12))
    _wheel(s,wheel,label+' main',w,.381,.2921,.18415)
    _joint(s,label+' main wheel spin',arm,wheel,w,(0,1,0),(-360,360),0)
    # Alternating wheel-rotating discs and nonrotating brake stators, inboard.
    rotors=[];stators=[]
    for i in range(5):
        yy=w[1]-side*(.139+.010*i)
        rotors.append(_ring((w[0],yy,w[2]),(0,1,0),.148,.070,.008,48))
        stators.append(_ring((w[0],yy-side*.0058,w[2]),(0,1,0),.151,.075,.0035,48))
    s.add(wheel,'Five brake rotor discs','steel_dark',Mesh.merged(rotors),detail_count=5)
    s.add(arm,'Five axle keyed brake stator plates','steel',Mesh.merged(stators),detail_count=5)
    calipers=[];bolts=[]
    for j in range(4):
        a=j*math.pi/2+.25
        q=(w[0]+.125*math.cos(a),w[1]-side*.175,w[2]+.125*math.sin(a))
        calipers.append(cylinder(add(q,(0,-side*.019,0)),add(q,(0,side*.019,0)),.031,20))
        bolts.append(cylinder(add(q,(0,-side*.019,0)),add(q,(0,-side*.023,0)),.012,6))
    s.add(arm,'Hydraulic brake piston housings','gear_white',Mesh.merged(calipers),detail_count=4)
    s.add(arm,'Brake housing fastening heads','steel',Mesh.merged(bolts),detail_count=4)
    door=label+' main gear door';hy=side*1.20;hz=1.402
    verts=[(10.04,hy,hz),(11.72,hy,hz),(11.72,side*.36,hz),(10.04,side*.36,hz)]
    s.add(door,'Main well closing skin','skin_lower',prism(verts,(0,0,.018)))
    ribs=[]
    for x in (10.10,10.56,11.16,11.65):
        ribs.append(box((x,side*.78,hz+.030),(.025,.76,.028)))
    ribs.extend([box((10.88,side*y,hz+.025),(1.57,.022,.022)) for y in (.43,1.12)])
    s.add(door,'Door inner pressed ribs','gear_white',Mesh.merged(ribs),detail_count=len(ribs))
    _pins(s,door,'Main door hinges',[(10.18,hy,hz),(11.55,hy,hz)],(1,0,0),.021,.14)
    _joint(s,label+' main bay door','Airframe',door,(10.8,hy,hz),(side,0,0),(0,90),87)
    _actuator(s,label+' main door actuator','Airframe',door,(10.8,side*.75,1.70),(10.8,side*1.08,1.43),(1,0,0),.023)
    return f


def _nose(s):
    p=(5.45,0,2.04);w=(5.55,0,.2794);axis=(0,1,0)
    root='Nose gear leg';piston='Nose oleo piston';fork='Nose wheel steering'
    top=(5.57,0,1.90);bottom=(5.68,0,.77);direction=unit(sub(bottom,top))
    s.add(root,'Nose trunnion crosshead','gear_white',cylinder((p[0],-.20,p[2]),(p[0],.20,p[2]),.016,32))
    s.add(root,'Nose upper shock absorber barrel','gear_white',Mesh.merged([cylinder(p,top,.016,36,radius2=.066),cylinder(top,bottom,.066,40,radius2=.055)]))
    s.add(root,'Upper strut reinforcement collars','gear_white',Mesh.merged([_ring(add(top,mul(direction,t)),direction,.071,.063,.05,32) for t in (.15,.45,1.06)]),detail_count=3)
    s.add(root,'Oleo gland scraper seal','black',_ring(bottom,direction,.057,.038,.019,32))
    s.add(piston,'Nose polished oleo piston','stainless',cylinder((5.65664,0,1.01),(5.70726,0,.49),.039,40))
    s.add(piston,'Nose steering torque collar','gear_white',cylinder((5.70726,0,.49),(5.69071,0,.66),.061,36))
    _pins(s,root,'Nose trunnion',[p],axis,.013,.42)
    _joint(s,'Nose gear retract','Airframe',root,p,axis,(0,96.0),0)
    _joint(s,'Nose oleo compression',root,piston,(5.66735,0,.9),direction,(-.12,.08),0,'slider')
    _two_link(s,'Nose torque scissors',root,piston,(5.627,0,.96),(5.665,0,.56),axis,.25,bend=-1,radius=.019)
    _two_link(s,'Nose drag brace','Airframe',root,(5.45,0,1.83),(5.63,0,1.24),axis,.415,bend=-1,radius=.025)
    _actuator(s,'Nose retract actuator','Airframe',root,(5.56,.11,1.99),(5.605,.11,1.49),axis,.034)
    s.add(fork,'Twin wheel forged fork','gear_white',Mesh.merged([
        cylinder((5.70,-.075,.58),(5.55,-.075,.2794),.043,28),
        cylinder((5.70,.075,.58),(5.55,.075,.2794),.043,28),
        cylinder((5.70,-.075,.58),(5.70,.075,.58),.046,28),
        cylinder((5.55,-.290,.2794),(5.55,.290,.2794),.033,36)]),detail_count=4)
    s.add(fork,'Anti shimmy steering head','gear_white',cylinder((5.706,0,.50),(5.6865,0,.70),.065,40))
    s.add(fork,'Shimmy damper hardware','steel',Mesh.merged([
        cylinder((5.57,-.065,.59),(5.75,-.065,.59),.026,24),
        cylinder((5.58,-.065,.59),(5.79,-.065,.59),.012,24)]),detail_count=2)
    _joint(s,'Nosewheel steering',piston,fork,(5.696,0,.60),mul(direction,-1),(-75,75),0)
    s.add(root,'Nose hydraulic feed tube','stainless',tube([(5.60,.065,1.90),(5.65,.065,1.42),(5.73,.065,.84)],.005,10))
    s.add(piston,'Nose flexible hydraulic service loop','black',tube([(5.69,.064,.93),(5.76,.064,.79),(5.76,.064,.66),(5.71,.064,.60)],.008,12))
    s.add(fork,'Launch and tow attachment eyes','steel',Mesh.merged([
        _ring((5.70,-.085,.60),axis,.042,.022,.026,32),
        _ring((5.70,.085,.60),axis,.042,.022,.026,32)]),detail_count=2)
    for label,side in (('Port',-1),('Starboard',1)):
        center=(w[0],side*.20,w[2]);comp='Nose '+label+' wheel'
        _wheel(s,comp,'Nose '+label,center,.2794,.16764,.127)
        _joint(s,'Nose '+label+' wheel spin',fork,comp,center,axis,(-360,360),0)
    launch='Launch bar';lp=(5.70,0,.60)
    s.add(launch,'Catapult launch wishbone','steel',Mesh.merged([
        cylinder((lp[0],-.085,lp[2]),(4.73,-.10,.10),.023,28),
        cylinder((lp[0],.085,lp[2]),(4.73,.10,.10),.023,28)]),detail_count=2)
    s.add(launch,'Catapult shuttle cross pin','stainless',cylinder((4.71,-.17,.09),(4.71,.17,.09),.026,36))
    s.add(launch,'Launch bar yoke neck','steel',cylinder((4.73,-.10,.10),(4.73,.10,.10),.035,28))
    _pins(s,launch,'Launch yoke hinge',[(lp[0],-.085,lp[2]),(lp[0],.085,lp[2])],axis,.023,.07)
    _joint(s,'Launch bar lift',fork,launch,lp,axis,(0,125),0)
    for label,side in (('Port',-1),('Starboard',1)):
        door='Nose '+label+' door';hy=side*.295;hz=1.75
        # Stepped well: shallow rear opening and raised forward nose opening.
        outline=[(3.38,hy,1.815),(4.10,hy,1.75),(5.63,hy,1.72),
                 (5.63,0,1.72),(4.10,0,1.75),(3.38,0,1.815)]
        s.add(door,'Nose well closing panel','skin_lower',prism(outline,(0,0,.015)))
        ribs=[]
        for x,z in ((3.53,1.83),(4.02,1.776),(4.55,1.755),(5.10,1.745),(5.52,1.735)):
            ribs.append(box((x,side*.145,z),(.022,.255,.023)))
        s.add(door,'Nose door inner stiffeners','gear_white',Mesh.merged(ribs),detail_count=len(ribs))
        _pins(s,door,'Nose door hinges',[(3.63,hy,hz),(5.42,hy,hz)],(1,0,0),.016,.10)
        _joint(s,'Nose '+label+' door','Airframe',door,(4.8,hy,hz),(side,0,0),(0,90),83)
        _actuator(s,'Nose '+label+' door actuator','Airframe',door,(4.8,side*.10,1.98),(4.8,side*.20,1.75),(1,0,0),.018)
    return dict(pivot=p,angle=96.0,wheel_center=w,launch_bar_stow=math.degrees(math.pi-math.atan2(.97,.5)))


def refine(s):
    """Replace the old visual gear with articulated, tire-size-correct gear."""
    _remove_baseline(s);category=s.category;s.category='aircraft'
    s.materials['gear_wheel_alloy']=dict(physical='Aluminum',color=[191,198,195],metallic=.72,roughness=.32)
    s.materials.setdefault('brass',dict(physical='Brass',color=[159,126,66],metallic=.88,roughness=.36))
    before=len(s.bodies);frames={}
    for label,side in (('Port',-1),('Starboard',1)):
        frames[label]=_main(s,label,side)
    nose=_nose(s)
    s.gear_retract_pose={
        'Launch bar lift':nose['launch_bar_stow'],
        'Nose gear retract':nose['angle'],
        'Port main gear retract':frames['Port']['angle'],
        'Starboard main gear retract':frames['Starboard']['angle'],
        'Nose Port door':0,'Nose Starboard door':0,
        'Port main bay door':0,'Starboard main bay door':0,
    }
    s.gear_references=SOURCES
    s.gear_dimensions=dict(
        main_tire=dict(nominal='30x11.5-14.5',radius_m=.381,width_m=.2921,rim_radius_m=.18415),
        nose_tire=dict(nominal='22x6.6-10',radius_m=.2794,width_m=.16764,rim_radius_m=.127),
        main_frames=frames,nose=nose,added_bodies=len(s.bodies)-before,
        limitations='External visual reconstruction; exact linkage lengths, angles and load behavior are authored approximations.',
        sequence='Raise launch bar; leave doors open; retract nose and mains; close doors. Reverse to extend.',
    )
    s.notes.append('Landing gear rebuilt with public NAVAIR tire nominal sizes, original trailing-arm/oleo geometry, aft main and forward nose retraction, linked main shrink and wheel planing. True passive coplanar linkage loops are used. Small pivot/actuator dimensions and timing are visual approximations, not aircraft engineering.')
    s.category=category
    return s.gear_dimensions


if __name__=='__main__':
    from pathlib import Path
    import argparse,json
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    scene=Scene();scene.add('Airframe','Gear test fixed datum','steel',box((8,0,2.6),(.12,.12,.12)))
    data=refine(scene);out=Path(args.output)
    scene.cameras['Landing gear detail']=dict(target=[8.0,0,1.0],distance=10,yaw=math.radians(-125),pitch=math.radians(15),fov=math.radians(40))
    manifest=scene.export(out)
    invalid=[];degenerate=[];volumes={}
    for part in scene.bodies:
        mesh=part['mesh'];volume=0.0
        for i,v in enumerate(mesh.vertices):
            if not all(math.isfinite(c) for c in v):invalid.append([part['name'],i])
        for i,face in enumerate(mesh.faces):
            a,b,c=(mesh.vertices[j] for j in face)
            if length(cross(sub(b,a),sub(c,a)))<1e-13:degenerate.append([part['name'],i])
            volume+=dot(a,cross(b,c))/6
        volumes[part['name']]=volume
    receipt={'dimensions':data,'statistics':manifest['statistics'],'nonfinite_vertices':invalid,'degenerate_triangles':degenerate,
             'negative_volume_bodies':{k:v for k,v in volumes.items() if v < -1e-9},'sources':SOURCES}
    (out/'geometry-checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'statistics':manifest['statistics'],'dimensions':data,'invalid_count':len(invalid),'degenerate_count':len(degenerate),
                      'negative_volume_bodies':receipt['negative_volume_bodies']},indent=2))
    if invalid or degenerate:raise SystemExit('Invalid gear mesh')
