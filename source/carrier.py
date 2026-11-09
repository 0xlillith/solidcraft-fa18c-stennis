"""Original photo-informed CVN-74 scene geometry; metres, +X aft, +Y starboard.

Overall scale follows the Navy's published Nimitz-class dimensions. Individual
offsets, deck markings and fittings are visual reconstructions, not ship plans.
The 2009–2010 visual setting is documented in research/stennis_references.md.
No game meshes, photographs, logos, textures or proprietary CAD are embedded.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict

from scene_api import (
    Mesh, box, cylinder, sphere, torus, tube, prism, text,
    add, sub, mul, cross, unit,
)


STRUCTURE = "Carrier structure"
DECK = [
    (-80.00, -27.0), (-80.00, 0.0), (-73.0, 7.0),
    (-47.0, 13.0), (-23.0, 19.0), (16.0, 23.0),
    (63.0, 25.2), (88.0, 24.5), (130.0, 24.5),
    (157.0, 24.5), (184.0, 20.5), (219.0, 18.0),
    (246.0, 13.0), (252.85, 7.0), (252.85, -28.0),
    (246.0, -35.0), (211.0, -36.8), (206.0, -45.0),
    (184.0, -45.0), (177.0, -41.0), (142.0, -46.0),
    (104.0, -51.6), (74.0, -51.6), (47.0, -43.0),
    (26.0, -35.0), (-42.0, -34.0), (-68.0, -31.0),
]
# An approximate silhouette at published class scale. Coordinates are not
# claimed to be surveyed or exact for any particular Stennis refit.
ELEVATORS = [
    (42.0, 64.0, 11.0, 25.2),
    (135.0, 157.0, 10.5, 24.5),
    (198.0, 220.0, 4.5, 18.0),
    (184.0, 206.0, -45.0, -28.5),
]


class Parts:
    """Batch small repeated details without discarding material separation."""
    def __init__(self, scene, component=STRUCTURE):
        self.scene = scene
        self.component = component
        self.groups = defaultdict(list)
        self.counts = defaultdict(int)

    def put(self, name, material, mesh, count=1):
        key = (name, material)
        self.groups[key].append(mesh)
        self.counts[key] += count

    def flush(self):
        variants = defaultdict(int)
        for name, material in self.groups:
            variants[name] += 1
        for (name, material), meshes in self.groups.items():
            label = name if variants[name] == 1 else name+" "+material
            self.scene.add(self.component, label, material,
                           Mesh.merged(meshes), self.counts[(name, material)])


def _clip(poly, axis, value, lower):
    """Clip a 2-D polygon at an axis-aligned half plane."""
    if not poly:
        return []
    out = []
    def inside(p):
        return p[axis] >= value - 1e-8 if lower else p[axis] <= value + 1e-8
    a = poly[-1]
    for b in poly:
        ia, ib = inside(a), inside(b)
        if ia != ib:
            t = (value-a[axis])/(b[axis]-a[axis])
            out.append((a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1])))
        if ib:
            out.append(b)
        a = b
    clean = []
    for p in out:
        if not clean or math.dist(p, clean[-1]) > 1e-7:
            clean.append(p)
    if len(clean) > 1 and math.dist(clean[0], clean[-1]) < 1e-7:
        clean.pop()
    # Remove collinear vertices before triangulation.
    changed = True
    while changed and len(clean) > 3:
        changed = False
        for i, p in enumerate(clean):
            a, b = clean[i-1], clean[(i+1) % len(clean)]
            if abs((p[0]-a[0])*(b[1]-p[1])-(p[1]-a[1])*(b[0]-p[0])) < 1e-8:
                clean.pop(i)
                changed = True
                break
    return clean


def _inside(p, polygon=DECK):
    x, y = p
    c = False
    a = polygon[-1]
    for b in polygon:
        if (a[1] > y) != (b[1] > y):
            if x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
                c = not c
        a = b
    return c


def _elevator_at(x, y, margin=0):
    return any(a-margin < x < b+margin and c-margin < y < d+margin
               for a, b, c, d in ELEVATORS)


def _stripe(a, b, width, z=.009, height=.003):
    d = unit((b[0]-a[0], b[1]-a[1], 0))
    n = (-d[1]*width/2, d[0]*width/2, 0)
    p, q = (a[0], a[1], z), (b[0], b[1], z)
    return prism([add(p,n), sub(p,n), sub(q,n), add(q,n)], (0,0,height))


def _dash(parts, a, b, width, on=2.3, off=1.5, material="white", name="Deck dashed markings", z=.009):
    d = sub((b[0], b[1], 0), (a[0], a[1], 0))
    length = math.sqrt(sum(v*v for v in d))
    u = mul(d, 1/length)
    t = 0.0
    while t < length:
        p = add((a[0], a[1], 0), mul(u,t))
        q = add((a[0], a[1], 0), mul(u,min(t+on,length)))
        parts.put(name, material, _stripe(p,q,width,z))
        t += on+off


def _hull():
    stations = [(-79.0,.3), (-71.0,5.1), (-56.0,10.9),
                (-33.0,17.2), (-5.0,19.6), (35.0,20.42),
                (155.0,20.42), (202.0,19.7), (234.0,17.0),
                (251.0,13.4)]
    # More rounded underbody than a box, intentionally low detail below water.
    shape = [(-1.0,-3.0), (-1.0,-8.0), (-.95,-14.0),
             (-.82,-20.0), (-.56,-25.0), (-.26,-28.0),
             (0,-29.0), (.26,-28.0), (.56,-25.0),
             (.82,-20.0), (.95,-14.0), (1.0,-8.0), (1.0,-3.0)]
    vs = [(x,-13.0+w*y,z) for x,w in stations for y,z in shape]
    n = len(shape)
    fs = []
    for i in range(len(stations)-1):
        for j in range(n):
            a=i*n+j; b=i*n+(j+1)%n; c=b+n; d=a+n
            fs += [(a,b,c),(a,c,d)]
    for station, reverse in ((0,True),(len(stations)-1,False)):
        idx = len(vs)
        vs.append((stations[station][0],-13,-14))
        for j in range(n):
            a=station*n+j; b=station*n+(j+1)%n
            fs.append((idx,b,a) if reverse else (idx,a,b))
    return Mesh(vs,fs)


def _deck_and_hull(scene, p):
    p.put("Lofted hull shell", "hull_gray", _hull())
    p.put("Hangar and gallery structural envelope", "hull_gray",
          box((110,-13,-5.6),(245,38,8.0)))
    # Segment the deck at elevator and hero-JBD boundaries. The deflector
    # leaves a genuinely recessed pit, rather than a decal on an intact slab.
    holes=ELEVATORS+[(22.35,27.25,-7.25,7.25)]
    xs=sorted(set([-80.0,252.85]+[v for r in holes for v in r[:2]]))
    ys=sorted(set([-51.6,25.2]+[v for r in holes for v in r[2:]]))
    pieces=[]
    for xa,xb in zip(xs,xs[1:]):
        for ya,yb in zip(ys,ys[1:]):
            mx,my=(xa+xb)/2,(ya+yb)/2
            if any(a < mx < b and c < my < d for a,b,c,d in holes):
                continue
            poly=DECK[:]
            for axis,value,low in ((0,xa,True),(0,xb,False),(1,ya,True),(1,yb,False)):
                poly=_clip(poly,axis,value,low)
            if len(poly)<3:
                continue
            area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))
            if area < 1e-6:
                continue
            pieces.append(prism([(x,y,-.5) for x,y in poly],(0,0,.5)))
    p.put("Flight deck non-skid with elevator wells", "deck", Mesh.merged(pieces), len(pieces))
    for i,(xa,xb,ya,yb) in enumerate(ELEVATORS,1):
        # Slender segmented perimeter and visible underside structure.
        p.put("Elevator well edges", "steel_dark", Mesh.merged([
            box((xa,(ya+yb)/2,-.42),(.16,yb-ya+.16,.25)),
            box((xb,(ya+yb)/2,-.42),(.16,yb-ya+.16,.25)),
            box(((xa+xb)/2,ya,-.42),(xb-xa,.16,.25)),
            box(((xa+xb)/2,yb,-.42),(xb-xa,.16,.25)),
        ]),4)
        comp="Carrier deck elevator "+str(i)
        scene.add(comp,"Non-skid platform","deck",box(((xa+xb)/2,(ya+yb)/2,-.13),(xb-xa-.12,yb-ya-.12,.26)))
        beams=[]
        for x in (xa+.4,xa+4,xa+8,xa+12,xa+16,xb-.4):
            beams.append(box((x,(ya+yb)/2,-.8),(.2,yb-ya-1,1.0)))
        scene.add(comp,"Platform underside beams","hull_gray",Mesh.merged(beams),len(beams))
        scene.joint("Elevator "+str(i)+" vertical travel",STRUCTURE,comp,
                    ((xa+xb)/2,(ya+yb)/2,0),(0,0,1),(-10,0),0,"slider")
        for a,b in [((xa+.2,ya+.2),(xb-.2,ya+.2)),((xa+.2,yb-.2),(xb-.2,yb-.2))]:
            _dash(p,a,b,.19,.75,.75,"yellow","Elevator caution edge")
        # Navy hull has pronounced elevator/gallery cut-outs; these dark
        # backing recesses improve their appearance in low views.
        p.put("Elevator gallery recesses", "paint_dark",box(((xa+xb)/2,(ya+yb)/2,-5.0),(xb-xa-.6,yb-ya-.6,3)))

    # Flight-deck fascia, gutter, galleries and shallow side buttresses.
    for a,b in zip(DECK,DECK[1:]+DECK[:1]):
        p.put("Deck edge fascia", "hull_gray", tube([(a[0],a[1],-.45),(b[0],b[1],-.45)],.38,6))
        p.put("Deck edge dark gutter", "steel_dark", tube([(a[0],a[1],-.08),(b[0],b[1],-.08)],.075,6))
    for x in range(-28,239,12):
        for y in (-34,8):
            p.put("Gallery structure ribs", "hull_gray",prism([(x-.18,y,-2.0),(x-.18,y,-7.0),(x-.18,y+(3 if y>0 else -3),-2.0)],(.36,0,0)))
    # Hangar door silhouettes, portholes and service ports on both sides.
    for side in (-1,1):
        y=-13+side*20.55
        for x in (15,64,112,160,211):
            p.put("Hangar side recesses", "paint_dark",box((x,y,-7.5),(10,.12,4.2)))
            p.put("Hangar side opening frames", "hull_gray",box((x,y+side*.07,-5.35),(10.5,.2,.25)))
        for x in range(-20,241,6):
            p.put("Gallery ports", "black",cylinder((x,y,-3.6),(x,y+side*.04,-3.6),.19,12))


def _deck_markings(p):
    # Ship number and launch-area numerals are true geometry, no texture map.
    p.put("Bow 74 deck identification", "white",text("74",(-60,-13,.015),8.0,right=(0,1,0),up=(-1,0,0),depth=.006))
    for x,y,num in ((9,3.0,"1"),(1,-21,"2"),(157,-28,"3"),(175,-19,"4")):
        p.put("Catapult deck numbers", "yellow",text(num,(x+1.2,y,.013),1.2,right=(0,1,0),up=(-1,0,0),depth=.004))

    # Angled recovery area. A broad landing lane remains clear behind the
    # aircraft; diagonal topology makes the Nimitz deck recognizable.
    a=(244,-16); b=(65,-44)
    d=unit((b[0]-a[0],b[1]-a[1],0)); n=(-d[1],d[0],0)
    for side in (-1,1):
        aa=add((a[0],a[1],0),mul(n,side*9.0))
        bb=add((b[0],b[1],0),mul(n,side*9.0))
        p.put("Angled landing area edges", "white",_stripe(aa,bb,.32))
        aa=add(aa,mul(n,side*1.15));bb=add(bb,mul(n,side*1.15))
        _dash(p,aa,bb,.25,2.2,1.4,"white","Landing area foul-line dashes")
    _dash(p,a,b,.28,5.0,4.0,"white","Angled landing area centreline")
    for t in (19,33,47,61):
        centre=add((a[0],a[1],.025),mul(d,t))
        # Arresting wires rest only a few centimetres above the deck.
        pa=add(centre,mul(n,-11.0));pb=add(centre,mul(n,11.0))
        p.put("Four arresting-wire visual spans", "steel_dark",tube([pa,centre,pb],.025,8))
        for q in (pa,pb):
            p.put("Arresting-wire deck sockets", "steel",box((q[0],q[1],.015),(.55,.42,.03)))

    # Foredeck foul lines and narrow working-area outlines.
    _dash(p,(-55,9),(39,12),.24,2.4,1.6,"white","Forward starboard foul line")
    _dash(p,(-48,-30),(42,-26),.24,2.4,1.6,"white","Forward port foul line")
    for y in (-8.25,8.25):
        _dash(p,(-12,y),(29,y),.16,.9,.9,"red","Catapult one safety-boundary red")
        _dash(p,(-11.1,y),(29,y),.16,.9,.9,"white","Catapult one safety-boundary white")
    p.put("Catapult one yellow working line", "yellow",_stripe((-12,10.2),(31,10.2),.16))
    # Warning stencil beside the deflector, small enough for a close camera.
    p.put("Jet blast danger stencils", "white",text("JET BLAST",(29.14,-4.2,.014),.54,right=(0,1,0),up=(-1,0,0),depth=.003))


def _catapult(p, a, b, label, fine=False):
    length=math.dist(a,b)
    u=unit((b[0]-a[0],b[1]-a[1],0)); n=(-u[1],u[0],0)
    p.put(label+" track slot", "black",_stripe(a,b,.115,.006,.004))
    for side in (-1,1):
        aa=add((a[0],a[1],0),mul(n,side*.175));bb=add((b[0],b[1],0),mul(n,side*.175))
        p.put(label+" flush steel track strips", "steel",_stripe(aa,bb,.20,.007,.007))
    # The worn maintenance strip is broad and flush, not a raised rail.
    for side in (-1,1):
        aa=add((a[0],a[1],0),mul(n,side*.42));bb=add((b[0],b[1],0),mul(n,side*.42))
        p.put(label+" track scuff", "deck_scuff",_stripe(aa,bb,.22,.003,.002))
    step=1.25 if fine else 3.5
    t=0.0
    while t<length:
        c=add((a[0],a[1],.018),mul(u,t))
        p.put(label+" transverse track seams", "steel_dark",_stripe(add(c,mul(n,-.27)),add(c,mul(n,.27)),.014,.018,.003))
        if fine:
            for side in (-1,1):
                q=add(c,mul(n,side*.20))
                p.put(label+" track countersunk fasteners", "steel_dark",cylinder((q[0],q[1],.018),(q[0],q[1],.025),.018,8))
        t+=step


def _catapults_and_foredeck(scene,p):
    _catapult(p,(-66,0),(7.0,0),"Catapult 1",True)
    _catapult(p,(-66,-17),(-1.0,-17),"Catapult 2")
    _catapult(p,(61,-46),(154,-31),"Catapult 3")
    _catapult(p,(74,-36),(171,-20.5),"Catapult 4")
    # Shallow shuttle, side cheeks, tow-point and small visible hardware.
    p.put("Catapult one shuttle base", "steel_dark",box((4.71,0,.045),(.78,.47,.075)))
    p.put("Catapult one shuttle cheeks", "steel",Mesh.merged([
        box((4.71,-.24,.09),(.62,.075,.12)),box((4.71,.24,.09),(.62,.075,.12)),
        box((4.54,0,.12),(.12,.39,.12)),
        cylinder((4.71,-.26,.09),(4.71,.26,.09),.05,16),
    ]),4)
    for x in (4.41,5.01):
        for y in (-.17,.17):
            p.put("Shuttle bolt heads", "stainless",cylinder((x,y,.085),(x,y,.10),.028,6))
    p.put("Catapult one holdback deck insert", "steel_dark",box((6.45,0,.013),(.9,.48,.025)))
    for i in range(6):
        p.put("Holdback insert relief slots", "black",box((6.12+i*.12,0,.029),(.025,.31,.008)))
    # Separate, hideable exterior visual for the launch-pose holdback link.
    # This is not a mechanism model and does not move with a retracted gear.
    holdback_top=(5.62,0,.54)
    holdback_deck=(6.45,0,.035)
    holdback_axis=unit(sub(holdback_deck,holdback_top))
    p.put("Catapult one holdback bar visual", "steel",
          cylinder(holdback_top,holdback_deck,.032,16))
    collar_meshes=[]
    for t in (.12,.72):
        q=add(holdback_top,mul(sub(holdback_deck,holdback_top),t))
        collar_meshes.append(cylinder(sub(q,mul(holdback_axis,.045)),
                                      add(q,mul(holdback_axis,.045)),.047,12))
    collar_meshes.append(torus(holdback_top,.045,.012,holdback_axis,16,6))
    collar_meshes.append(torus(holdback_deck,.045,.012,holdback_axis,16,6))
    p.put("Catapult one holdback exterior collars", "steel_dark",
          Mesh.merged(collar_meshes),len(collar_meshes))

    # A genuinely separated JBD panel bank. Hinges are in authoring position
    # and its native joint defaults rotate the bank into the launch preset.
    p.put("Catapult one JBD pit shadow", "black",box((24.8,0,-.43),(4.85,14.4,.035)))
    p.put("Catapult one JBD recessed foundation", "steel_dark",box((24.8,0,-.51),(4.92,14.55,.12)))
    for i in range(4):
        comp=f"JBD 1 panel {i+1}"
        q=Parts(scene,comp)
        y=-5.25+i*3.5
        q.put("Heat-worn upper deflector panel","jbd_heat",box((24.78,y,-.025),(4.50,3.46,.12)))
        q.put("Deflector structural tray","hull_gray",box((24.78,y,-.13),(4.50,3.46,.12)))
        # Subtle alternating replaceable face plates and closely spaced screws.
        for row in range(3):
            q.put("Replaceable hot-face plates","deck_patch",box((23.28+row*1.49,y,.041),(1.46,3.40,.009)))
            for yy in (-1.48,-.75,0,.75,1.48):
                for xx in (22.62+row*1.49,23.95+row*1.49):
                    q.put("Hot-face captive bolts","steel_dark",cylinder((xx,y+yy,.046),(xx,y+yy,.057),.024,8))
        for yy in (-1.65,-1.10,-.55,0,.55,1.10,1.65):
            q.put("Deflector deep underside ribs","hull_gray",box((24.8,y+yy,-.35),(4.35,.09,.42)))
        for xx in (22.72,23.85,25.1,26.8):
            q.put("Deflector underside crossmembers","hull_gray",box((xx,y,-.32),(.12,3.35,.36)))
        q.put("Deflector hinge sleeves","steel",cylinder((22.5,y-1.7,-.08),(22.5,y+1.7,-.08),.11,16))
        # Bracket eyes are modelled on the panel; no unsupported simulation
        # of a hydraulic linkage is implied by these decorative brackets.
        for yy in (-.9,.9):
            q.put("Deflector lifting brackets","steel_dark",prism([(23.8,y+yy-.07,-.16),(24.6,y+yy-.07,-.16),(24.25,y+yy-.07,-.85)],(0,.14,0)))
            q.put("Deflector lifting bracket pins","steel",cylinder((24.23,y+yy-.12,-.66),(24.23,y+yy+.12,-.66),.055,12))
        q.flush()
        scene.joint(f"JBD 1 panel {i+1} elevation",STRUCTURE,comp,(22.5,y,0),(0,-1,0),(0,75),60)
    # Fixed foundation hinge saddles and cover edge.
    for y in (-7,-3.5,0,3.5,7):
        p.put("JBD ground hinge saddles", "steel_dark",box((22.5,y,-.03),(.40,.30,.28)))
    for y in (-7.25,7.25):
        p.put("JBD well edge steel", "steel",box((24.8,y,.005),(4.85,.16,.035)))
    _dash(p,(22.1,-7.5),(28,-7.5),.22,.7,.7,"red","JBD hazard border red")
    _dash(p,(22.8,-7.5),(28,-7.5),.22,.7,.7,"white","JBD hazard border white")
    _dash(p,(22.1,7.5),(28,7.5),.22,.7,.7,"red","JBD hazard border red")
    _dash(p,(22.8,7.5),(28,7.5),.22,.7,.7,"white","JBD hazard border white")

    # Other catapults' deflectors are flush standby modules, individually
    # divided into visible plates without adding artificial raised barriers.
    for number,centre in ((2,(16,-17)),(3,(172,-28.1)),(4,(189,-17.6))):
        x,y=centre
        p.put("Standby JBD recesses", "black",box((x,y,.006),(4.8,14.1,.012)))
        for j in range(4):
            yy=y-5.22+j*3.48
            p.put("Standby JBD flush plates", "deck_patch",box((x,yy,.015),(4.7,3.43,.019)))
            p.put("Standby JBD transverse ribs", "steel_dark",box((x,yy,.027),(.025,3.42,.009)))
        p.put("Standby JBD deck designation", "yellow",text(str(number),(x+4,y+6,.012),1,right=(0,1,0),up=(-1,0,0),depth=.003))


def _deck_microdetail(p):
    rng=random.Random(74018)
    # Foredeck pad-eyes use inset dark wells, a worn rim and two cross-bars.
    # All fittings are merged by material and hierarchy, not separate bodies.
    for ix in range(25):
        x=-18+ix*2.4
        for iy in range(16):
            y=-18+iy*2.4
            if abs(y)<.50 or (21.8<x<28.1 and abs(y)<7.8):
                continue
            p.put("Foredeck recessed tie-down wells","black",cylinder((x,y,.001),(x,y,.006),.115,16))
            p.put("Foredeck worn tie-down rings","steel",torus((x,y,.007),.096,.010,(0,0,1),16,6))
            for a,b in (((x-.075,y,.009),(x+.075,y,.009)),((x,y-.075,.009),(x,y+.075,.009))):
                p.put("Foredeck tie-down crossbars","steel_dark",cylinder(a,b,.014,8))
    # Coarser background pad-eyes retain density without excessive triangles.
    for x in range(-72,249,5):
        for y in range(-49,24,5):
            if (-20<x<42 and -20<y<20) or not _inside((x,y)) or _elevator_at(x,y,.4):
                continue
            if 90<x<132 and 7<y<24:
                continue
            p.put("Background deck tie-down fittings","steel_dark",cylinder((x,y,.004),(x,y,.012),.10,8))

    # Non-repeating maintenance patches, restrained rubber marks and seams.
    for i in range(125):
        x=rng.uniform(-14,37);y=rng.uniform(-16,16)
        if abs(y)<.6 or (22<x<28 and abs(y)<8):
            continue
        sx=rng.uniform(.20,1.9);sy=rng.uniform(.12,.65)
        p.put("Foredeck subtle non-skid repair patches","deck_patch",box((x,y,.0025),(sx,sy,.003)))
    for side in (-1,1):
        for j in range(22):
            x=-2+j*.78+rng.random()*.2
            y=side*1.6+rng.uniform(-.22,.22)
            p.put("Restrained foredeck tyre scuff fragments","paint_dark",box((x,y,.006),(rng.uniform(.25,.65),rng.uniform(.025,.065),.004)))
    # Maintenance hatch covers with flush edge screws near the hero aircraft.
    for x,y,w,h in ((-7,4,1.1,.8),(11,9,1.4,.8),(19,-10,1.5,.9),(30,5,.9,.8),(5,-8,1.1,.8)):
        p.put("Foredeck access hatch seams","black",box((x,y,.004),(w+.035,h+.035,.006)))
        p.put("Foredeck access hatch covers","deck_patch",box((x,y,.009),(w,h,.009)))
        for dx in (-w*.43,w*.43):
            for dy in (-h*.40,h*.40):
                p.put("Foredeck hatch countersunk screws","steel_dark",cylinder((x+dx,y+dy,.014),(x+dx,y+dy,.020),.018,8))
        p.put("Foredeck hatch recessed lifting handle","black",box((x,y,.017),(.14,.035,.006)))


def _edge_detail(p):
    # Safety nets outside the deck lip, lowered for flight operations. They
    # never create a tall rail across an aircraft's flight path.
    for a,b in zip(DECK,DECK[1:]+DECK[:1]):
        length=math.dist(a,b)
        u=unit((b[0]-a[0],b[1]-a[1],0))
        # DECK is clockwise viewed above, exterior is its left-hand normal.
        out=(-u[1],u[0],0)
        count=max(1,int(length/2.5))
        for k in range(count):
            t0=k/count;t1=(k+1)/count
            aa=(a[0]+(b[0]-a[0])*t0,a[1]+(b[1]-a[1])*t0,-.28)
            bb=(a[0]+(b[0]-a[0])*t1,a[1]+(b[1]-a[1])*t1,-.28)
            oa=add(aa,add(mul(out,1.7),(0,0,-.7)))
            ob=add(bb,add(mul(out,1.7),(0,0,-.7)))
            p.put("Flight-deck lowered safety-net frames","pipe",tube([aa,oa,ob,bb],.035,6))
            for f in (.25,.5,.75):
                pp=add(mul(aa,1-f),mul(oa,f));qq=add(mul(bb,1-f),mul(ob,f))
                p.put("Flight-deck safety-net mesh","zinc",cylinder(pp,qq,.009,4))
            for f in (.25,.5,.75):
                pp=add(mul(aa,1-f),mul(bb,f));qq=add(mul(oa,1-f),mul(ob,f))
                p.put("Flight-deck safety-net mesh","zinc",cylinder(pp,qq,.009,4))
        # Gallery catwalk sits below the flight deck; repeated support beams.
        middle=add(((a[0]+b[0])/2,(a[1]+b[1])/2,-1.7),mul(out,.45))
        aa=add((a[0],a[1],-1.7),mul(out,-.15));bb=add((b[0],b[1],-1.7),mul(out,-.15))
        oa=add(aa,mul(out,1.3));ob=add(bb,mul(out,1.3))
        p.put("Below-deck gallery catwalks","hull_gray",prism([aa,bb,ob,oa],(0,0,-.13)))
        for z in (-1.1,-.62):
            p.put("Below-deck gallery rails","pipe",cylinder((oa[0],oa[1],z),(ob[0],ob[1],z),.022,6))
        for k in range(max(1,int(length/3))):
            f=k/max(1,int(length/3));q=add(mul(oa,1-f),mul(ob,f))
            p.put("Gallery railing stanchions","pipe",cylinder((q[0],q[1],-1.67),(q[0],q[1],-.59),.027,6))

    # Raft capsules and their small racks along gallery edges.
    for side in (-1,1):
        y=-35.4 if side<0 else 9.8
        for x in (-23,-19,13,17,73,77,161,165,229,233):
            p.put("Life raft capsule bodies","white",cylinder((x,y,-2.3),(x+2.0,y,-2.3),.42,16))
            p.put("Life raft capsule rounded ends","white",Mesh.merged([sphere((x,y,-2.3),(.22,.42,.42),16,8),sphere((x+2,y,-2.3),(.22,.42,.42),16,8)]),2)
            for xx in (x+.4,x+1.6):
                p.put("Life raft securing straps","steel_dark",torus((xx,y,-2.3),.425,.024,(1,0,0),16,6))
                p.put("Life raft cradle feet","hull_gray",box((xx,y,-2.83),(.12,.75,.20)))
    # Small deck edge lights and separate low reflectors.
    for x in range(-60,239,9):
        for y in (-32,12):
            if not _inside((x,y)):
                continue
            p.put("Inset edge-light bezels","steel_dark",cylinder((x,y,.003),(x,y,.016),.082,12))
            p.put("Inset edge-light lenses","light_green",cylinder((x,y,.017),(x,y,.025),.052,12))


def _rail(p,points,name="Island platform railings",height=1.05):
    for a,b in zip(points,points[1:]):
        for h in (.50,height):
            p.put(name,"pipe",cylinder(add(a,(0,0,h)),add(b,(0,0,h)),.026,8))
        n=max(1,int(math.dist(a,b)/1.5))
        for i in range(n):
            q=add(mul(a,1-i/n),mul(b,i/n))
            p.put(name,"pipe",cylinder(q,add(q,(0,0,height)),.031,8))


def _island(scene,p):
    # Layered island and two cantilevered bridge/PriFly bands.
    p.put("Island lower superstructure","hull_gray",box((110,16,3.6),(34,12.2,7.2)))
    p.put("Island forward bridge body","hull_gray",box((106,15.7,9.5),(33,14.7,4.6)))
    p.put("Island bridge upper deck","hull_gray",box((106,15.7,11.95),(34.1,15.3,.38)))
    p.put("Island upper control tower","hull_gray",box((109.1,15.8,15.0),(25.4,12.2,5.7)))
    p.put("PriFly overhang roof","hull_gray",box((108.4,15.8,18.0),(27.6,13.9,.36)))
    p.put("Island aft equipment block","hull_gray",box((125.5,17.0,12.0),(7.0,8.3,10.0)))
    p.put("Mast foundation building","hull_gray",box((112,16,20.5),(10.0,7.3,4.6)))

    # Glazing sits just outside the opaque envelope. Thin frames and forward
    # sunshades remain visible in bow-facing views as well as along the sides.
    for z,x0,x1,yleft,yright in ((9.5,89.45,122.55,8.28,23.12),(15.5,96.35,121.85,9.64,21.96)):
        for y in (yleft,yright):
            for x in range(math.ceil(x0),math.floor(x1),2):
                p.put("Bridge and PriFly glazing","bridge_glass",box((x+.65,y,z),(1.55,.075,1.55)))
                p.put("Bridge window upper sunshades","hull_gray",box((x+.65,y,z+.89),(1.78,.45,.14)))
                p.put("Bridge window frames","white",box((x-.16,y,z),(.055,.13,1.65)))
        for x,outward in ((x0,-1),(x1,1)):
            bays=max(1,int((yright-yleft)/2.05))
            pitch=(yright-yleft)/bays
            for i in range(bays):
                y=yleft+(i+.5)*pitch
                p.put("Bridge and PriFly glazing","bridge_glass",box((x,y,z),(.075,pitch-.24,1.55)))
                p.put("Bridge window frames","white",box((x,y-pitch/2+.07,z),(.13,.055,1.65)))
                p.put("Bridge window upper sunshades","hull_gray",box((x+outward*.13,y,z+.89),(.42,pitch-.12,.14)))
    # Two major side hull numbers; geometric stencil inspired by Navy photos.
    p.put("Island port 74","white",text("74",(105.5,9.87,1.35),5.3,right=(1,0,0),up=(0,0,1),depth=.035))
    p.put("Island starboard 74","white",text("74",(114.5,22.13,1.35),5.3,right=(-1,0,0),up=(0,0,1),depth=.035))
    p.put("Island ship-name plate","paint_dark",box((108,9.84,.83),(20,.08,.60)))
    p.put("Island ship-name lettering","white",text("JOHN C STENNIS",(105.8,9.77,.59),.40,right=(1,0,0),up=(0,0,1),depth=.018))

    platforms=[(93,128,7.0,25.0,7.1),(95,123,8.8,23.3,12.1),(94.6,122.4,8.8,22.8,18.25)]
    for xa,xb,ya,yb,z in platforms:
        p.put("Island exterior walkways","hull_gray",box(((xa+xb)/2,(ya+yb)/2,z-.08),(xb-xa,yb-ya,.16)))
        _rail(p,[(xa,ya,z),(xb,ya,z),(xb,yb,z),(xa,yb,z),(xa,ya,z)])
    # External ladders and rungs.
    for x,y,z0,z1 in ((123.4,8.15,.5,7.0),(126.3,9.0,7.25,12.0),(122.8,10.0,12.25,18.2),(116.8,19.9,18.3,23.3)):
        for dx in (-.27,.27):
            p.put("Island exterior ladders","pipe",cylinder((x+dx,y,z0),(x+dx,y,z1),.035,8))
        for i in range(int((z1-z0)/.29)+1):
            z=z0+i*.29
            p.put("Island ladder rungs","steel",cylinder((x-.27,y,z),(x+.27,y,z),.025,8))
    # Surface doors, vent banks, pipes and small boxes add readable layers.
    for x in (94.4,100.0,123.8,126.0):
        p.put("Island exterior door frames","white",box((x,9.76,2.0),(1.0,.09,2.05)))
        p.put("Island exterior doors","hull_gray",box((x,9.68,2.0),(.84,.09,1.90)))
        p.put("Island exterior door handles","steel_dark",cylinder((x+.25,9.60,1.94),(x+.25,9.60,2.13),.028,8))
    for x,z in ((97,5.5),(102,5.5),(125,6),(126,14),(111,20.5)):
        p.put("Island ventilation housings","paint_dark",box((x,9.77,z),(2,.15,1.05)))
        for i in range(6):
            p.put("Island ventilation louvers","hull_gray",box((x,9.64,z-.43+i*.17),(1.9,.16,.065)))
    for x in (95.5,119.4,127.7):
        p.put("Island vertical service pipes","pipe",tube([(x,9.5,.2),(x,9.5,5.8),(x+.6,9.5,6.4)],.06,10))
    for x,y,z in ((92,10.1,8.4),(92,21.3,8.4),(121,10.1,13.7),(121,21,13.7)):
        p.put("Island navigation-light housings","steel_dark",cylinder((x,y,z),(x,y,z+.26),.15,12))
        p.put("Island navigation-light lenses","light_green" if y>15 else "red",sphere((x,y,z+.31),(.12,.12,.12),12,6))

    # Main tapered lattice mast, platforms, and diagonal braces.
    base=(111,16,22.7)
    levels=[(0,2.2),(5,1.85),(10,1.45),(15,1.05),(20,.65)]
    for (z0,w0),(z1,w1) in zip(levels,levels[1:]):
        corners0=[(base[0]+sx*w0,base[1]+sy*w0,base[2]+z0) for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1))]
        corners1=[(base[0]+sx*w1,base[1]+sy*w1,base[2]+z1) for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1))]
        for i in range(4):
            p.put("Main mast structural legs","hull_gray",cylinder(corners0[i],corners1[i],.15,10,radius2=.10))
            p.put("Main mast crossed braces","pipe",cylinder(corners0[i],corners1[(i+1)%4],.06,8))
            p.put("Main mast crossed braces","pipe",cylinder(corners0[(i+1)%4],corners1[i],.06,8))
            p.put("Main mast horizontal braces","pipe",cylinder(corners1[i],corners1[(i+1)%4],.075,8))
    for z,w in ((27.8,3.3),(33.0,2.7),(38.1,2.0)):
        p.put("Mast maintenance platforms","hull_gray",box((111,16,z),(w*2,w*2,.18)))
        _rail(p,[(111-w,16-w,z+.1),(111+w,16-w,z+.1),(111+w,16+w,z+.1),(111-w,16+w,z+.1),(111-w,16-w,z+.1)],"Mast safety rails",.85)
    p.put("Mast tip and antenna","hull_gray",cylinder((111,16,42.6),(111,16,47.5),.12,12,radius2=.035))

    # Distinct radar silhouettes: one broad planar array and one tall array.
    _radar(scene,"Carrier broad radar",(111,16,41.2),7.2,3.4,25)
    _radar(scene,"Carrier tall radar",(123,16.7,29.0),4.6,5.7,-25)
    p.put("Aft radar foundation mast","hull_gray",cylinder((123,16.7,17.2),(123,16.7,28.8),.32,16,radius2=.19))
    # Radomes and smaller whip/aerial groupings.
    for x,y,z,r in ((96,12,20.4,1.15),(119,20.2,23.9,1.0),(123,12,21.5,.75),(105,20,24.7,.65)):
        p.put("Island communications radome pedestals","hull_gray",cylinder((x,y,z-1.1),(x,y,z),r*.54,16))
        p.put("Island pale communications radomes","white",sphere((x,y,z+.52),(r,r,r*1.15),24,12))
    for i in range(12):
        x=96+(i%6)*4.2;y=11.4+(i//6)*9.2;z=19.2 if i%3 else 23.1
        h=2.4+(i%4)*.55
        p.put("Island whip antennas","pipe",cylinder((x,y,z),(x,y,z+h),.045,8,radius2=.011))
        p.put("Island antenna bases","white",cylinder((x,y,z-.25),(x,y,z+.30),.13,12))
    for x,y,z in ((107,13,31),(107,19,31),(115,13,35),(115,19,35)):
        p.put("Mast yardarms","pipe",cylinder((111,16,z),(x,y,z),.09,10))
        p.put("Mast yardarm aerials","steel_dark",cylinder((x,y,z-.4),(x,y,z+2.2),.025,8))


def _radar(scene,name,centre,width,height,angle):
    comp=name
    p=Parts(scene,comp)
    x,y,z=centre
    # Array in the X-Z plane; native rotary joint sweeps it about vertical.
    p.put("Radar rotation bearing","steel_dark",cylinder((x,y,z-.65),(x,y,z-.35),.55,20))
    p.put("Radar pedestal","hull_gray",cylinder((x,y,z-.35),(x,y,z+.4),.24,16))
    for xx in (-width/2,width/2):
        p.put("Radar array perimeter","hull_gray",cylinder((x+xx,y,z+.35),(x+xx,y,z+height+.35),.06,8))
    for zz in (.35,height+.35):
        p.put("Radar array perimeter","hull_gray",cylinder((x-width/2,y,z+zz),(x+width/2,y,z+zz),.06,8))
    cols=max(4,int(width/.36));rows=max(4,int(height/.35))
    for i in range(cols+1):
        xx=x-width/2+i*width/cols
        p.put("Radar array fine vertical lattice","pipe",cylinder((xx,y,z+.35),(xx,y,z+height+.35),.018,6))
    for j in range(rows+1):
        zz=z+.35+j*height/rows
        p.put("Radar array fine horizontal lattice","pipe",cylinder((x-width/2,y,zz),(x+width/2,y,zz),.018,6))
    for sx in (-1,1):
        p.put("Radar array rear bracing","hull_gray",cylinder((x,y+.7,z+.8),(x+sx*width/2,y,z+height*.8),.055,8))
    p.flush()
    scene.joint(name+" azimuth",STRUCTURE,comp,centre,(0,0,1),(-180,180),angle)


def _deck_equipment(p):
    # Low-profile equipment cabinets, fire points, coiled hoses and a parked
    # tow tractor stay well clear of the featured aircraft's launch corridor.
    for x,y in ((32,17),(65,18),(145,14),(214,10)):
        p.put("Flight-deck service cabinets","hull_gray",box((x,y,.54),(1.4,.7,1.08)))
        p.put("Cabinet doors and handles","white",box((x-.1,y-.36,.56),(1.1,.06,.88)))
        p.put("Cabinet door latches","steel_dark",box((x+.3,y-.42,.6),(.07,.04,.20)))
        p.put("Red fire-point housings","red",box((x+1.4,y,.38),(.5,.5,.76)))
        for i in range(4):
            p.put("Stowed fire-hose coils","tire",torus((x+1.4,y+.42,.65),.24+i*.035,.022,(0,1,0),20,6))
    # Parked tractor, mechanically styled but intentionally subordinate.
    x,y,z=53,17,.38
    p.put("Parked deck tractor chassis","yellow",box((x,y,z),(3.6,2.0,.5)))
    p.put("Parked deck tractor engine bonnet","yellow",box((x-.9,y,.94),(1.65,1.7,.72)))
    p.put("Parked tractor operator footwell","paint_dark",box((x+.9,y,.71),(1.3,1.65,.15)))
    for dx in (-1.15,1.15):
        for dy in (-1.05,1.05):
            p.put("Parked tractor tyres","tire",cylinder((x+dx,y+dy-.16,.40),(x+dx,y+dy+.16,.40),.39,24))
            p.put("Parked tractor wheel hubs","steel_dark",cylinder((x+dx,y+dy-.18,.40),(x+dx,y+dy+.18,.40),.20,16))
    p.put("Parked tractor seat","black",Mesh.merged([box((x+.9,y,.92),(.62,.65,.16)),box((x+1.19,y,1.24),(.13,.65,.65))]),2)
    p.put("Parked tractor steering column","steel_dark",cylinder((x+.23,y,.79),(x+.34,y,1.34),.035,10))
    p.put("Parked tractor steering wheel","black",torus((x+.34,y,1.36),.22,.025,(.3,0,1),24,6))
    p.put("Parked tractor bumpers","paint_dark",Mesh.merged([box((x-1.87,y,.41),(.17,2.1,.22)),box((x+1.87,y,.41),(.17,2.1,.22))]),2)
    p.put("Parked tractor identification","white",text("74",(x-1.738,y+.62,.70),.32,right=(0,-1,0),up=(0,0,1),depth=.01))
    # Sculpted low towing eye, stowed towbar and a small beacon.
    p.put("Parked tractor towing eye","steel",torus((x+2.05,y,.38),.105,.027,(0,0,1),20,6))
    p.put("Parked tractor beacon support","steel_dark",cylinder((x+1.5,y+.6,.7),(x+1.5,y+.6,1.5),.025,8))
    p.put("Parked tractor amber beacon","orange",cylinder((x+1.5,y+.6,1.5),(x+1.5,y+.6,1.66),.09,16))


def _ellipsoid_between(a,b,depth,width):
    """A clothed body volume, oriented along its spine/limb axis."""
    w=unit(sub(b,a));u=unit(cross((0,1,0),w));v=cross(w,u)
    centre=mul(add(a,b),.5)
    m=[[u[i],v[i],w[i],centre[i]] for i in range(3)]+[[0,0,0,1]]
    return sphere((0,0,0),(depth,width,math.dist(a,b)*.60),16,10).transformed(m)


def _crew_figure(scene,name,origin,yaw,role,pose):
    """Original static human figure with no real-person likeness.

    The five material batches preserve named, editable people without turning
    every glove, seam and ear protector into a separate imported CAD body.
    """
    p=Parts(scene,name)
    c=math.cos(math.radians(yaw));s=math.sin(math.radians(yaw))
    matrix=[[c,-s,0,origin[0]],[s,c,0,origin[1]],[0,0,1,origin[2]],[0,0,0,1]]
    def put(group,material,mesh,count=1):
        p.put(group,material,mesh.transformed(matrix),count)
    clothing="crew_"+role
    pelvis=(0,0,1.0);neck=(-.025,0,1.50);head=(-.04,0,1.68)
    hips=[(0,-.12,.98),(0,.12,.98)]
    knees=[(-.035,-.155,.53),(.045,.16,.53)]
    ankles=[(0,-.17,.15),(.085,.18,.15)]
    shoulders=[(-.025,-.23,1.39),(-.025,.23,1.39)]
    elbows=[(-.10,-.36,1.14),(-.10,.36,1.14)]
    wrists=[(-.23,-.38,.97),(-.23,.38,.97)]
    if pose=="kneeling":
        pelvis=(0,0,.75);neck=(-.20,0,1.25);head=(-.255,0,1.43)
        hips=[(-.035,-.12,.73),(.025,.12,.73)]
        knees=[(-.48,-.17,.50),(.08,.18,.15)]
        ankles=[(-.44,-.18,.14),(.43,.18,.11)]
        shoulders=[(-.165,-.225,1.16),(-.165,.225,1.16)]
        elbows=[(-.59,-.28,.92),(-.48,.28,1.01)]
        wrists=[(-.62,-.29,.60),(-.83,.30,.99)]
    elif pose=="check":
        elbows=[(-.28,-.40,1.35),(-.17,.37,1.13)]
        wrists=[(-.10,-.14,1.58),(-.31,.36,.97)]
    elif pose=="director":
        elbows=[(-.06,-.54,1.53),(-.06,.54,1.53)]
        wrists=[(-.12,-.78,1.79),(-.12,.78,1.79)]
    elif pose=="safety":
        elbows=[(-.25,-.34,1.15),(-.12,.36,1.16)]
        wrists=[(-.35,-.24,1.10),(-.38,.18,1.15)]

    # Smooth jersey and padded flotation vest, with a distinct pelvis and
    # tapered clothing on each limb to avoid an unscaled mannequin silhouette.
    put("Role jersey and flotation vest",clothing,_ellipsoid_between(add(pelvis,(0,0,.04)),neck,.15,.245))
    put("Work trousers","fabric",sphere(add(pelvis,(0,0,-.05)),(.16,.225,.16),16,10))
    for side in (-1,1):
        a=add(pelvis,(-.12,side*.115,.08));b=add(neck,(-.12,side*.115,-.12))
        put("Role jersey and flotation vest",clothing,_ellipsoid_between(a,b,.070,.094))
    # Vest closure, webbing and straps are dark fabric/rubber visual batches.
    put("Boots gloves webbing and goggles","black",tube([add(pelvis,(-.164,0,.10)),add(neck,(-.163,0,-.10))],.009,8))
    for side in (-1,1):
        put("Cranial shells and reflective trim","crew_helmet",tube([add(pelvis,(-.19,side*.13,.13)),add(neck,(-.18,side*.13,-.14))],.012,6))
    # Waist belt follows the elliptical waist instead of a rectangular block.
    belt=torus(add(pelvis,(0,0,.025)),.205,.019,(0,0,1),24,6)
    bm=[[.76,0,0,pelvis[0]*(1-.76)],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
    put("Boots gloves webbing and goggles","black",belt.transformed(bm))
    put("Cranial shells and reflective trim","crew_helmet",box(add(pelvis,(-.169,0,.025)),(.015,.052,.046)))

    for hip,knee,ankle in zip(hips,knees,ankles):
        put("Work trousers","fabric",cylinder(hip,knee,.103,14,radius2=.082))
        put("Work trousers","fabric",sphere(knee,(.085,.086,.09),14,8))
        put("Work trousers","fabric",cylinder(knee,ankle,.085,14,radius2=.069))
        # Cargo pocket and kneepad add shape cues in oblique close views.
        outer=-1 if hip[1]<0 else 1
        middle=mul(add(hip,knee),.5)
        put("Work trousers","fabric",box(add(middle,(0,outer*.09,0)),(.14,.028,.17)))
        put("Boots gloves webbing and goggles","black",sphere(add(knee,(-.063,0,0)),(.033,.065,.08),12,8))
        foot=(ankle[0]-.065,ankle[1],.075)
        if pose=="kneeling" and ankle[0]>.2:
            foot=(ankle[0]+.03,ankle[1],.06)
        put("Boots gloves webbing and goggles","black",sphere(foot,(.145,.084,.068),16,8))
        put("Boots gloves webbing and goggles","black",cylinder(add(ankle,(0,0,-.07)),add(ankle,(0,0,.10)),.077,14,radius2=.069))
        put("Boots gloves webbing and goggles","black",box((foot[0],foot[1],.024),(.25,.157,.037)))
        for j in range(4):
            put("Cranial shells and reflective trim","crew_helmet",cylinder((foot[0]-.04+j*.023,foot[1]-.04,.129),(foot[0]-.04+j*.023,foot[1]+.04,.129),.004,6))

    for shoulder,elbow,wrist in zip(shoulders,elbows,wrists):
        put("Role jersey and flotation vest",clothing,sphere(shoulder,(.085,.086,.10),14,8))
        put("Role jersey and flotation vest",clothing,cylinder(shoulder,elbow,.073,14,radius2=.059))
        put("Role jersey and flotation vest",clothing,sphere(elbow,(.063,.063,.064),12,8))
        put("Role jersey and flotation vest",clothing,cylinder(elbow,wrist,.059,14,radius2=.043))
        hand_axis=unit(sub(wrist,elbow));tip=add(wrist,mul(hand_axis,.10))
        put("Boots gloves webbing and goggles","black",_ellipsoid_between(wrist,tip,.045,.037))
        put("Boots gloves webbing and goggles","black",sphere(add(wrist,(-.025,.035,0)),(.025,.022,.045),12,6))
        put("Cranial shells and reflective trim","crew_helmet",torus(wrist,.044,.007,hand_axis,16,6))
    if pose=="kneeling":
        # A short pointing glove finger provides the recognizable shooter
        # silhouette; this is a static artistic pose, not launch instruction.
        wrist=wrists[1]
        put("Boots gloves webbing and goggles","black",cylinder(add(wrist,(-.045,0,.018)),add(wrist,(-.15,0,.018)),.013,8))
    if pose=="safety":
        put("Boots gloves webbing and goggles","black",box((-.43,-.01,1.17),(.035,.36,.28)))
        put("Cranial shells and reflective trim","crew_helmet",box((-.452,-.01,1.17),(.008,.29,.21)))
        for i in range(4):
            put("Boots gloves webbing and goggles","black",box((-.458,-.01,1.12+i*.032),(.004,.18,.006)))

    # Head, neck and cranial: dome, separate ear defenders, tinted goggles,
    # chin strap, central role stripe and a compact radio microphone boom.
    put("Face and neck","crew_skin",cylinder(add(neck,(0,0,-.015)),add(head,(0,0,-.10)),.063,16))
    put("Face and neck","crew_skin",sphere(head,(.105,.094,.133),20,12))
    put("Face and neck","crew_skin",sphere(add(head,(-.098,0,.008)),(.037,.025,.027),12,8))
    put("Cranial shells and reflective trim","crew_helmet",sphere(add(head,(.004,0,.083)),(.118,.113,.078),20,10))
    put("Cranial shells and reflective trim","crew_helmet",sphere(add(head,(.072,0,.015)),(.055,.105,.104),16,10))
    put("Role jersey and flotation vest",clothing,tube([add(head,(-.10,0,.10)),add(head,(-.04,0,.158)),add(head,(.04,0,.157)),add(head,(.11,0,.08))],.020,8))
    for side in (-1,1):
        put("Boots gloves webbing and goggles","black",cylinder(add(head,(0,side*.091,.015)),add(head,(0,side*.137,.015)),.066,16))
        put("Cranial shells and reflective trim","crew_helmet",cylinder(add(head,(0,side*.138,.015)),add(head,(0,side*.145,.015)),.045,16))
    put("Boots gloves webbing and goggles","black",sphere(add(head,(-.095,0,.041)),(.027,.085,.038),20,10))
    put("Cranial shells and reflective trim","crew_helmet",tube([add(head,(-.098,-.071,.06)),add(head,(-.112,0,.076)),add(head,(-.098,.071,.06))],.007,8))
    put("Boots gloves webbing and goggles","black",tube([add(head,(.02,-.12,.02)),add(head,(-.07,-.073,-.11)),add(head,(-.08,0,-.121)),add(head,(-.07,.073,-.11)),add(head,(.02,.12,.02))],.011,8))
    put("Boots gloves webbing and goggles","black",tube([add(head,(0,.143,.015)),add(head,(-.11,.12,-.012)),add(head,(-.14,.025,-.04))],.007,8))
    put("Boots gloves webbing and goggles","black",sphere(add(head,(-.14,.025,-.04)),(.018,.023,.017),10,6))
    p.flush()
    scene.fixed(name+" static pose",STRUCTURE,name)


def _crew(scene):
    _crew_figure(scene,"Deck crew yellow shooter",(0,-4,0),-135,"yellow","kneeling")
    _crew_figure(scene,"Deck crew green support",(10,7,0),90,"green","check")
    _crew_figure(scene,"Deck crew white safety",(14,-8,0),-90,"white","safety")
    _crew_figure(scene,"Deck crew yellow director",(-4,5,0),150,"yellow","director")


def build(scene):
    """Populate the full carrier and a close-detail catapult-one foreground."""
    scene.materials.setdefault("bridge_glass",dict(physical="Glass",color=[28,48,53],metallic=.18,roughness=.17,opacity=1.0,ior=1.51))
    scene.materials.setdefault("deck_patch",dict(physical="Steel",color=[69,74,76],metallic=0,roughness=.98))
    scene.materials.setdefault("deck_scuff",dict(physical="Steel",color=[87,91,92],metallic=.12,roughness=.88))
    scene.materials.setdefault("jbd_heat",dict(physical="Steel",color=[104,99,90],metallic=.35,roughness=.73))
    scene.materials.setdefault("crew_yellow",dict(physical="Nylon",color=[211,173,48],metallic=0,roughness=.94))
    scene.materials.setdefault("crew_green",dict(physical="Nylon",color=[70,111,73],metallic=0,roughness=.94))
    scene.materials.setdefault("crew_white",dict(physical="Nylon",color=[202,210,207],metallic=0,roughness=.94))
    scene.materials.setdefault("crew_skin",dict(physical="ABS Plastic",color=[165,127,105],metallic=0,roughness=.75))
    scene.materials.setdefault("crew_helmet",dict(physical="ABS Plastic",color=[193,198,190],metallic=0,roughness=.49))
    p=Parts(scene)
    _deck_and_hull(scene,p)
    _deck_markings(p)
    _catapults_and_foredeck(scene,p)
    _deck_microdetail(p)
    _edge_detail(p)
    _island(scene,p)
    _deck_equipment(p)
    _crew(scene)
    p.flush()
    scene.notes.append("CVN-74 is an original photo-informed visual reconstruction at Nimitz-class overall scale, not a surveyed ship model. Detail is concentrated near catapult one and the island. Deck offset, surface wear, equipment and historic radar fit are interpretive.")
    scene.notes.append("The four catapult-one JBD panels and two radar arrays have native revolute joints. Four separate elevator platforms have vertical slider joints (metres in this source, travel -10 to 0); their machinery and realistic constraints are not simulated. Four static original deck-crew figures have no real-person likeness.")
    scene.notes.append("Catapult-one shuttle engagement is centred at x=4.71 m, y=0, z=0.09 m to meet the aircraft launch-bar cross pin in the launch preset. Its geometry is visual, not engineered launching hardware.")
