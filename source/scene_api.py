"""Original, reproducible visual geometry for the F/A-18C / Stennis showcase.

Authoring units are metres, +X aft, +Y starboard, +Z up. OBJ is exported in mm.
No third-party meshes, textures, CAD files, or game assets are incorporated.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import json, math, re
from pathlib import Path
from collections import OrderedDict, defaultdict

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def length(a): return math.sqrt(dot(a,a))
def unit(a):
    n=length(a)
    if n<1e-14: raise ValueError('Zero direction')
    return mul(a,1/n)
def lerp(a,b,t): return add(mul(a,1-t),mul(b,t))
def basis(axis):
    w=unit(axis); u=unit(cross((0,0,1) if abs(w[2])<.9 else (0,1,0),w))
    return u,cross(w,u),w
def rot(point,origin,axis,angle):
    p=sub(point,origin); a=unit(axis); c=math.cos(angle); s=math.sin(angle)
    return add(origin,add(add(mul(p,c),mul(cross(a,p),s)),mul(a,dot(a,p)*(1-c))))
def slug(s): return re.sub(r'[^A-Za-z0-9_-]+','_',s).strip('_')

@dataclass
class Mesh:
    vertices:list=field(default_factory=list)
    faces:list=field(default_factory=list)
    smooth:bool=True
    @classmethod
    def merged(cls, meshes):
        vs=[];fs=[]
        for m in meshes:
            if m is None: continue
            n=len(vs);vs.extend(m.vertices);fs.extend(tuple(i+n for i in f) for f in m.faces)
        return cls(vs,fs)
    def transformed(self,matrix):
        vs=[tuple(sum(matrix[r][c]*p[c] for c in range(3))+matrix[r][3] for r in range(3)) for p in self.vertices]
        det=dot(matrix[0][:3],cross(matrix[1][:3],matrix[2][:3]))
        fs=self.faces if det>=0 else [(f[0],f[2],f[1]) for f in self.faces]
        return Mesh(vs,list(fs),self.smooth)
    def translated(self,offset): return Mesh([add(p,offset) for p in self.vertices],list(self.faces),self.smooth)
    def rotated(self,origin,axis,degrees):
        return Mesh([rot(p,origin,axis,math.radians(degrees)) for p in self.vertices],list(self.faces),self.smooth)
    def mirrored(self,axis=1):
        vs=[tuple(-v if i==axis else v for i,v in enumerate(p)) for p in self.vertices]
        return Mesh(vs,[(a,c,b) for a,b,c in self.faces],self.smooth)
    def bounds(self):
        return [list(map(min,zip(*self.vertices))),list(map(max,zip(*self.vertices)))]
    def normals(self):
        ns=[[0.,0.,0.] for _ in self.vertices]
        for a,b,c in self.faces:
            n=cross(sub(self.vertices[b],self.vertices[a]),sub(self.vertices[c],self.vertices[a]))
            for ix in (a,b,c):
                for j in range(3):ns[ix][j]+=n[j]
        return [unit(n) if length(n)>1e-16 else (0,0,1) for n in ns]

def quad(a,b,c,d):return Mesh([a,b,c,d],[(0,1,2),(0,2,3)])
def box(center,size):
    x,y,z=center;dx,dy,dz=[s/2 for s in size]
    pts=[(x-dx,y-dy,z-dz),(x+dx,y-dy,z-dz),(x+dx,y+dy,z-dz),(x-dx,y+dy,z-dz),
         (x-dx,y-dy,z+dz),(x+dx,y-dy,z+dz),(x+dx,y+dy,z+dz),(x-dx,y+dy,z+dz)]
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return Mesh.merged(quad(*(pts[i] for i in f)) for f in faces)

def cylinder(a,b,radius,segments=24,radius2=None):
    if radius2 is None:radius2=radius
    u,v,w=basis(sub(b,a)); vs=[];fs=[]
    for p,r in ((a,radius),(b,radius2)):
        vs.extend(add(p,add(mul(u,r*math.cos(2*math.pi*i/segments)),mul(v,r*math.sin(2*math.pi*i/segments)))) for i in range(segments))
    for i in range(segments):
        j=(i+1)%segments;fs.extend([(i,j,j+segments),(i,j+segments,i+segments)])
    for p,r,reverse in ((a,radius,True),(b,radius2,False)):
        off=len(vs);vs.append(p)
        vs.extend(add(p,add(mul(u,r*math.cos(2*math.pi*i/segments)),mul(v,r*math.sin(2*math.pi*i/segments)))) for i in range(segments))
        for i in range(segments):
            f=(off,off+1+i,off+1+(i+1)%segments);fs.append((f[0],f[2],f[1]) if reverse else f)
    return Mesh(vs,fs)

def sphere(center,radii,segments=32,rings=16):
    if isinstance(radii,(float,int)):radii=(radii,radii,radii)
    vs=[add(center,(0,0,-radii[2]))];fs=[]
    for j in range(1,rings):
        lat=-math.pi/2+math.pi*j/rings
        for i in range(segments):
            t=2*math.pi*i/segments
            vs.append(add(center,(radii[0]*math.cos(lat)*math.cos(t),radii[1]*math.cos(lat)*math.sin(t),radii[2]*math.sin(lat))))
    top=len(vs);vs.append(add(center,(0,0,radii[2])))
    for i in range(segments):
        k=(i+1)%segments;fs.append((0,1+k,1+i))
        fs.append((top,1+(rings-2)*segments+i,1+(rings-2)*segments+k))
    for j in range(rings-2):
        for i in range(segments):
            a=1+j*segments+i;b=1+j*segments+(i+1)%segments;c=b+segments;d=a+segments
            fs.extend([(a,b,c),(a,c,d)])
    return Mesh(vs,fs)

def torus(center,major,minor,axis=(0,0,1),segments=48,sides=10):
    u,v,w=basis(axis);vs=[];fs=[]
    for i in range(segments):
        t=2*math.pi*i/segments;e=add(mul(u,math.cos(t)),mul(v,math.sin(t)))
        for j in range(sides):
            q=2*math.pi*j/sides
            vs.append(add(center,add(mul(e,major+minor*math.cos(q)),mul(w,minor*math.sin(q)))))
    for i in range(segments):
        for j in range(sides):
            a=i*sides+j;b=((i+1)%segments)*sides+j;c=((i+1)%segments)*sides+(j+1)%sides;d=i*sides+(j+1)%sides
            fs.extend([(a,b,c),(a,c,d)])
    return Mesh(vs,fs)

def tube(points,radius,segments=8):
    """Closed sweep with transported frames; closed paths have no overlapping caps."""
    clean=[]
    for p in points:
        p=tuple(p)
        if not clean or length(sub(p,clean[-1]))>1e-12:clean.append(p)
    points=clean;vs=[];fs=[]
    if len(points)<2:return Mesh()
    closed=len(points)>2 and length(sub(points[0],points[-1]))<1e-10
    if closed:points.pop()
    count=len(points)
    if count<2:return Mesh()
    axes=[]
    for i in range(count):
        before=points[(i-1)%count] if closed else points[max(i-1,0)]
        after=points[(i+1)%count] if closed else points[min(i+1,count-1)]
        tangent=sub(after,before)
        if length(tangent)<1e-12:tangent=sub(points[(i+1)%count],points[i])
        axes.append(unit(tangent))
    def transport(u,previous,current):
        turn=cross(previous,current);s=length(turn);c=max(-1,min(1,dot(previous,current)))
        if s>1e-12:u=rot(u,(0,0,0),mul(turn,1/s),math.atan2(s,c))
        u=sub(u,mul(current,dot(u,current)))
        return unit(u) if length(u)>1e-12 else basis(current)[0]
    frames=[basis(axes[0])[0]]
    for i in range(1,count):frames.append(transport(frames[-1],axes[i-1],axes[i]))
    if closed:
        end=transport(frames[-1],axes[-1],axes[0])
        correction=math.atan2(dot(axes[0],cross(end,frames[0])),dot(end,frames[0]))
        frames=[rot(u,(0,0,0),axes[i],correction*i/count) for i,u in enumerate(frames)]
    for i,p in enumerate(points):
        u=frames[i];v=cross(axes[i],u)
        for j in range(segments):
            t=2*math.pi*j/segments;vs.append(add(p,add(mul(u,radius*math.cos(t)),mul(v,radius*math.sin(t)))))
    for i in range(count if closed else count-1):
        ni=(i+1)%count
        for j in range(segments):
            nj=(j+1)%segments;a=i*segments+j;b=i*segments+nj;c=ni*segments+nj;d=ni*segments+j
            fs.extend([(a,b,c),(a,c,d)])
    if not closed:
        for end,reverse in ((0,True),(count-1,False)):
            ci=len(vs);vs.append(points[end]);off=len(vs)
            # Separate cap vertices keep the end face flat-shaded while remaining
            # geometrically welded to the swept wall.
            vs.extend(vs[end*segments:(end+1)*segments])
            for j in range(segments):
                f=(ci,off+j,off+(j+1)%segments);fs.append((f[0],f[2],f[1]) if reverse else f)
    return Mesh(vs,fs)

def triangulate(points):
    """Ear clipping in the dominant plane, preserving the supplied winding."""
    if len(points)<3:return []
    normal=(0,0,0)
    for a,b in zip(points,points[1:]+points[:1]):normal=add(normal,cross(a,b))
    skip=max(range(3),key=lambda i:abs(normal[i]));dims=[i for i in range(3) if i!=skip]
    pp=[(p[dims[0]],p[dims[1]]) for p in points]
    area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pp,pp[1:]+pp[:1]));sign=1 if area>=0 else -1
    def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    idx=list(range(len(pp)));faces=[];budget=len(idx)**2
    while len(idx)>3 and budget>0:
        budget-=1;found=False
        for j in range(len(idx)):
            a,b,c=idx[j-1],idx[j],idx[(j+1)%len(idx)]
            if sign*orient(pp[a],pp[b],pp[c])<=1e-12:continue
            inside=False
            for k in idx:
                if k in (a,b,c):continue
                if min(sign*orient(pp[a],pp[b],pp[k]),sign*orient(pp[b],pp[c],pp[k]),sign*orient(pp[c],pp[a],pp[k]))>1e-12:
                    inside=True;break
            if not inside:
                faces.append((a,b,c));idx.pop(j);found=True;break
        if not found:break
    if len(idx)==3:faces.append(tuple(idx))
    if len(faces)!=len(points)-2:raise ValueError('Polygon cannot be triangulated')
    return faces

def prism(points3d,vector):
    ps=[tuple(p) for p in points3d];n=len(ps)
    normal=(0,0,0)
    for a,b in zip(ps,ps[1:]+ps[:1]):normal=add(normal,cross(a,b))
    if dot(normal,vector)<0:ps.reverse()
    fs=triangulate(ps);top=[add(p,vector) for p in ps]
    meshes=[Mesh(ps,[(a,c,b) for a,b,c in fs]),Mesh(top,fs)]
    for i in range(n):
        j=(i+1)%n;meshes.append(quad(ps[i],ps[j],top[j],top[i]))
    return Mesh.merged(meshes)

# Compact original pixel alphabet, only geometry, no external font assets.
FONT={
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01111'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','11001','10101','10011','10011','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','10101','01010'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00001','00010','00100','01000','10000','11111'],
'0':['01110','10001','10011','10101','11001','10001','01110'],
'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'5':['11111','10000','10000','11110','00001','00001','11110'],
'6':['01110','10000','10000','11110','10001','10001','01110'],
'7':['11111','00001','00010','00100','01000','01000','01000'],
'8':['01110','10001','10001','01110','10001','10001','01110'],
'9':['01110','10001','10001','01111','00001','00001','01110'],
'-':['00000','00000','00000','11111','00000','00000','00000'],
'.':['00000','00000','00000','00000','00000','00110','00110'],
'/':['00001','00001','00010','00100','01000','10000','10000'],
' ':['00000']*7,
}
def text(value,origin,height,right=(1,0,0),up=(0,1,0),depth=.001):
    right=unit(right);up=unit(up);normal=unit(cross(right,up));pitch=height/7;meshes=[]
    for ci,ch in enumerate(str(value).upper()):
        rows=FONT.get(ch,FONT[' '])
        for row,pattern in enumerate(rows):
            start=None
            for k,bit in enumerate(pattern+'0'):
                if bit=='1' and start is None:start=k
                elif bit=='0' and start is not None:
                    p=add(origin,add(mul(right,(ci*6+start)*pitch),mul(up,(6-row)*pitch)))
                    w=(k-start)*pitch*.96;h=pitch*.96
                    meshes.append(prism([p,add(p,mul(right,w)),add(add(p,mul(right,w)),mul(up,h)),add(p,mul(up,h))],mul(normal,depth)))
                    start=None
    return Mesh.merged(meshes)

MATERIALS={
 'skin':dict(physical='Aluminum',color=[151,160,166],metallic=0,roughness=.56),
 'skin_lower':dict(physical='Aluminum',color=[174,182,185],metallic=0,roughness=.61),
 'skin_panel':dict(physical='Aluminum',color=[144,154,160],metallic=0,roughness=.64),
 'composite':dict(physical='Aluminum',color=[155,163,170],metallic=0,roughness=.57),
 'radome':dict(physical='ABS Plastic',color=[169,170,162],metallic=0,roughness=.66),
 'paint_dark':dict(physical='Aluminum',color=[48,56,61],metallic=0,roughness=.76),
 'gray':dict(physical='Aluminum',color=[117,125,130],metallic=0,roughness=.62),
 'hull_gray':dict(physical='Steel',color=[135,149,157],metallic=0,roughness=.69),
 'steel':dict(physical='Steel',color=[137,145,147],metallic=.86,roughness=.34),
 'steel_dark':dict(physical='Steel',color=[64,68,72],metallic=.88,roughness=.40),
 'metal':dict(physical='Stainless Steel',color=[167,173,177],metallic=.92,roughness=.24),
 'stainless':dict(physical='Stainless Steel',color=[190,197,202],metallic=.96,roughness=.19),
 'aluminum':dict(physical='Aluminum',color=[185,193,197],metallic=.92,roughness=.32),
 'titanium':dict(physical='Titanium',color=[115,110,106],metallic=.90,roughness=.38),
 'hot_metal':dict(physical='Titanium',color=[98,88,76],metallic=.89,roughness=.42),
 'exhaust':dict(physical='Steel',color=[43,39,34],metallic=.78,roughness=.58),
 'blue_heat':dict(physical='Titanium',color=[77,83,101],metallic=.90,roughness=.38),
 'tire':dict(physical='ABS Plastic',color=[24,26,27],metallic=0,roughness=.91),
 'black':dict(physical='ABS Plastic',color=[18,22,24],metallic=0,roughness=.65),
 'cockpit':dict(physical='Aluminum',color=[47,52,55],metallic=0,roughness=.71),
 'fabric':dict(physical='Nylon',color=[87,96,73],metallic=0,roughness=.96),
 'olive':dict(physical='Nylon',color=[90,96,70],metallic=0,roughness=.94),
 'white':dict(physical='Aluminum',color=[216,220,215],metallic=0,roughness=.64),
 'gear_white':dict(physical='Steel',color=[208,214,209],metallic=0,roughness=.38),
 'yellow':dict(physical='Aluminum',color=[219,171,38],metallic=0,roughness=.60),
 'red':dict(physical='Aluminum',color=[174,43,38],metallic=0,roughness=.48),
 'blue':dict(physical='Aluminum',color=[28,57,100],metallic=0,roughness=.44),
 'orange':dict(physical='Nylon',color=[206,98,37],metallic=0,roughness=.81),
 'cream':dict(physical='Nylon',color=[194,188,159],metallic=0,roughness=.79),
 'pipe':dict(physical='Steel',color=[97,111,117],metallic=.35,roughness=.48),
 'zinc':dict(physical='Steel',color=[134,143,137],metallic=.70,roughness=.43),
 'deck':dict(physical='Steel',color=[61,66,69],metallic=0,roughness=.97),
 'ocean':dict(physical='Glass',color=[21,57,74],metallic=.12,roughness=.24),
 'green_screen':dict(physical='Glass',color=[16,68,47],metallic=0,roughness=.22),
 'light_green':dict(physical='Glass',color=[59,186,111],metallic=0,roughness=.21),
 'glass':dict(physical='Polycarbonate',color=[200,214,217],opacity=.20,ior=1.49,roughness=.045,metallic=0),
 'hud_glass':dict(physical='Glass',color=[119,184,161],opacity=.34,ior=1.51,roughness=.045,metallic=0),
 'seam':dict(physical='Aluminum',color=[75,84,89],metallic=0,roughness=.84),
 'rubber_seal':dict(physical='ABS Plastic',color=[52,53,50],metallic=0,roughness=.88),
}

class Scene:
    def __init__(self):
        self.components=OrderedDict();self.bodies=[];self.joints=[];self.materials=dict(MATERIALS);self.cameras={};self.notes=[];self.motion_links=[]
        self._names=set();self.category='aircraft'
    def add(self,component,name,material,mesh,detail_count=1):
        if not mesh.vertices or not mesh.faces:return None
        if material not in self.materials:raise ValueError('Undefined material '+material)
        bodyname=slug(component)+'__'+slug(name)
        if bodyname in self._names:raise ValueError('Duplicate '+bodyname)
        self._names.add(bodyname)
        if component not in self.components:self.components[component]={'name':component,'slug':slug(component),'category':self.category,'parts':[]}
        part={'name':bodyname,'label':name,'component':component,'material':material,'mesh':mesh,'detail_count':detail_count}
        self.components[component]['parts'].append(part);self.bodies.append(part)
        return bodyname
    def joint(self,name,parent,child,origin,axis,limits=(-90,90),default=0,kind='revolute'):
        if name in [j['name'] for j in self.joints]:raise ValueError('Duplicate joint '+name)
        self.joints.append(dict(name=name,parent=parent,child=child,origin=list(origin),axis=list(unit(axis)),limits=list(limits),default=default,kind=kind))
    def fixed(self,name,parent,child):self.joint(name,parent,child,(0,0,0),(0,0,1),(0,0),0,'rigid')
    def export(self,out):
        out=Path(out);(out/'obj').mkdir(parents=True,exist_ok=True)
        manifest={'title':'F/A-18C / USS John C. Stennis — RC3 detailed structural model','geometry_units':'m','obj_units':'mm','coordinate_system':'+X aft, +Y starboard, +Z up; deck surface Z=0','components':[],'bodies':[],'materials':self.materials,'joints':self.joints,'motion_links':self.motion_links,'cameras':self.cameras,'notes':self.notes}
        for cname,comp in self.components.items():
            path=out/'obj'/f"{comp['slug']}.obj";offset=0
            with path.open('w',encoding='utf-8') as f:
                f.write('# Original procedural geometry. Units: millimetres. No third-party assets.\n')
                for part in comp['parts']:
                    m=part['mesh'];f.write('o '+part['name']+'\ns 1\n')
                    for p in m.vertices:f.write('v '+' '.join(f'{v*1000:.6f}' for v in p)+'\n')
                    for n in m.normals():f.write('vn '+' '.join(f'{v:.7f}' for v in n)+'\n')
                    for face in m.faces:f.write('f '+' '.join(f'{i+offset+1}//{i+offset+1}' for i in face)+'\n')
                    offset+=len(m.vertices)
                    manifest['bodies'].append({k:part[k] for k in ('name','label','component','material','detail_count')}|{'triangles':len(m.faces),'vertices':len(m.vertices),'bounds_m':m.bounds()})
            manifest['components'].append({'name':cname,'slug':comp['slug'],'file':'obj/'+path.name,'bodies':[p['name'] for p in comp['parts']],'category':comp['category']})
        manifest['statistics']={'components':len(self.components),'bodies':len(self.bodies),'joints':len(self.joints),'articulated_joints':sum(j['kind']!='rigid' for j in self.joints),'triangles':sum(len(p['mesh'].faces) for p in self.bodies),'vertices':sum(len(p['mesh'].vertices) for p in self.bodies),'modeled_detail_instances':sum(p['detail_count'] for p in self.bodies)}
        (out/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        return manifest

