#!/usr/bin/env python3
"""Generate the detailed Legacy Hornet model for official SolidCraft v0.40.0-rc.3.

Writes original geometry and native assembly metadata; no rendering. Follow with
native_build_rc3.py, which verifies the official executable and a fresh reopen.
"""
from __future__ import annotations
from pathlib import Path
import argparse,json,math,time
from scene_api import Scene,cross,sub,dot
import aircraft,cockpit,carrier,internals,engines

CAMERAS={
 'Launch aircraft':dict(target=[7.8,0,2.1],yaw=.84,pitch=.27,distance=27.,fov=.70),
 'Launch deck low':dict(target=[8.5,0,2.35],yaw=1.08,pitch=.105,distance=24.5,fov=.67),
 'Aircraft overview':dict(target=[8.1,0,2.2],yaw=.82,pitch=.54,distance=24.5,fov=.66),
 'Aircraft rear':dict(target=[10.2,0,2.15],yaw=-2.12,pitch=.32,distance=22.,fov=.70),
 'Aircraft plan':dict(target=[8.3,0,2.3],yaw=0,pitch=math.pi/2-.0001,distance=22.,fov=0),
 'Cockpit pilot eye':dict(target=[4.77,0,2.84],yaw=0,pitch=.19,distance=.96,fov=1.02),
 'Cockpit overhead':dict(target=[5.17,0,2.59],yaw=0,pitch=1.25,distance=1.64,fov=.98),
 'Cockpit equipment':dict(target=[4.91,0,2.64],yaw=2.22,pitch=.45,distance=2.24,fov=.85),
 'NACES seat':dict(target=[5.66,0,2.72],yaw=2.5,pitch=.27,distance=1.58,fov=.86),
 'Landing gear':dict(target=[5.15,0,.95],yaw=.9,pitch=.1,distance=4.8,fov=.8),
 'Main gear mechanism':dict(target=[10.8,-.83,1.02],yaw=2.2,pitch=.26,distance=3.2,fov=.78),
 'Internal systems':dict(target=[8.75,0,2.12],yaw=2.35,pitch=.58,distance=18.,fov=.70),
 'Wing structure':dict(target=[10.65,-2.9,2.49],yaw=1.8,pitch=1.03,distance=6.,fov=.75),
 'Forward avionics':dict(target=[2.45,0,2.26],yaw=2.5,pitch=.30,distance=3.4,fov=.75),
 'Twin F404 cutaway':dict(target=[14.7,0,1.98],yaw=1.05,pitch=.57,distance=7.1,fov=.75),
 'F404 port core':dict(target=[14.6,-.71,1.98],yaw=1.25,pitch=.72,distance=4.7,fov=.73),
 'F404 inlet stages':dict(target=[13.34,-.71,1.98],yaw=2.86,pitch=.20,distance=2.6,fov=.75),
 'F404 nozzle mechanism':dict(target=[16.15,-.71,1.98],yaw=.4,pitch=.40,distance=2.6,fov=.78),
 'Carrier overview':dict(target=[78,-13,-3.5],yaw=.87,pitch=.55,distance=345.,fov=.66),
 'Island detail':dict(target=[110,16,14],yaw=.85,pitch=.20,distance=62.,fov=.72),
}

def validate_scene(scene):
    bad=[];degenerate=0;triangles=0;verts=0;negative=[]
    for body in scene.bodies:
        mesh=body['mesh'];verts+=len(mesh.vertices);triangles+=len(mesh.faces)
        anchor=mesh.vertices[0];volume=0.
        if any(not all(math.isfinite(v) for v in p) for p in mesh.vertices):bad.append(body['name']+': nonfinite')
        for face in mesh.faces:
            if len(face)!=3 or min(face)<0 or max(face)>=len(mesh.vertices):bad.append(body['name']+': invalid face');break
            a,b,c=[mesh.vertices[i] for i in face];n=cross(sub(b,a),sub(c,a))
            if dot(n,n)<1e-24:degenerate+=1
            volume+=dot(sub(a,anchor),cross(sub(b,anchor),sub(c,anchor)))/6
        if volume<-1e-9:negative.append(body['name'])
    names=[j['name'] for j in scene.joints]
    if len(names)!=len(set(names)):bad.append('duplicate joint names')
    for j in scene.joints:
        for key in ('parent','child'):
            if j[key] not in scene.components:bad.append(j['name']+': missing '+key)
    follows={}
    for q in scene.motion_links:
        if q['a'] not in names or q['b'] not in names:bad.append('unresolved motion link '+str(q))
        if q['b'] in follows:bad.append('duplicate follower '+q['b'])
        follows[q['b']]=q['a']
    for follower in follows:
        visited={follower};p=follower
        while p in follows:
            p=follows[p]
            if p in visited:bad.append('motion-link cycle '+follower);break
            visited.add(p)
    if degenerate:bad.append(f'{degenerate} degenerate triangles')
    if bad:raise ValueError(bad[:30])
    return dict(finite_vertices=True,valid_indices=True,degenerate_triangles=degenerate,
                triangles=triangles,vertices=verts,joint_references_valid=True,motion_links_valid=True,
                negative_signed_volume_body_count=len(negative),negative_signed_volume_bodies=negative)

def variants(s):
    skins=['Fuselage Dorsal skins','Fuselage Port lower skins','Port cabin skins',
           'Nose upper skins','Nose port lower skins','Exterior markings and skin fasteners',
           'Port inlet fairing skins','Port inner wing upper skin','Port outer wing upper skin',
           'Starboard inner wing upper skin','Starboard outer wing upper skin']
    engine_top=[f'{side} F404 {layer} Q{i}' for side in ('Port','Starboard')
                for layer in ('casing','combustor liner','afterburner liner') for i in (1,2)]
    engine_non=[c for c in s.components if ' F404 ' not in c and s.components[c]['category']=='aircraft']
    structure_more=[c for c in s.components if c.startswith('Fuselage fuel cell')
                    or c in ('Fuel vent cell','Port intake duct','Starboard intake duct')]
    return [
      dict(name='Aircraft',subset='aircraft',hide_components=[],pose={},view='Aircraft overview'),
      dict(name='Cockpit access',subset='aircraft',hide_components=['Pilot'],
           pose={'Canopy unlatch slide':.0381,'Canopy open':68,'Boarding ladder deploy':90},view='Cockpit overhead'),
      dict(name='Internal systems',subset='aircraft',hide_components=skins+engine_top+['Pilot','Canopy','Speedbrake'],
           pose={'Radome service opening':95},view='Internal systems'),
      dict(name='Airframe structure',subset='aircraft',hide_components=skins+structure_more+engine_top+['Pilot','Canopy','Speedbrake'],
           pose={'Radome service opening':95},view='Wing structure'),
      dict(name='Twin F404 engines',subset='aircraft',hide_components=engine_non+engine_top,
           pose={},view='Twin F404 cutaway'),
    ]

def make(out,aircraft_only=False,intermediate=False):
    started=time.monotonic();s=Scene();s.category='aircraft'
    import importlib
    aircraft.build(s)
    for name,entry in [('landing_gear_refinement','refine')]:
        try:module=importlib.import_module(name)
        except ImportError:
            if not intermediate:raise RuntimeError(name+'.py must be present for final generation')
        else:getattr(module,entry)(s)
    cockpit.build(s);internals.build(s);engines.build(s)
    try:importlib.import_module('control_couplings').connect(s)
    except ImportError:
        if not intermediate:raise RuntimeError('control_couplings.py must be present for final generation')
    if not aircraft_only:s.category='carrier';carrier.build(s)
    s.cameras={k:v for k,v in CAMERAS.items() if not aircraft_only or k not in ('Carrier overview','Island detail')}
    check=validate_scene(s);manifest=s.export(out)
    manifest.update(name='F/A-18C NG301 and CVN-74 Stennis - detailed RC3 revision',
       generation_validation=check,variant='aircraft' if aircraft_only else 'complete',
       sources_file='REFERENCES.md',target_solidcraft_release='v0.40.0-rc.3',
       target_release_commit='7001949c49e211a430fe4747221589b2b9384f2c',target_native_format=51,
       intended_use='Detailed original visual and kinematic reconstruction for inspection and future showcase work. Exact internal engineering dimensions and systems behavior are not asserted.',
       source_parameters=dict(aircraft_nominal_length_m=17.07,aircraft_bare_wing_span_m=11.43,
         aircraft_nominal_height_m=4.66,main_gear_track_m=3.11,nose_main_wheelbase_m=5.42,
         engine_length_m=3.9116,engine_inlet_diameter_m=.7112,engine_maximum_diameter_m=.889,
         carrier_class_length_m=332.85,carrier_class_deck_beam_m=76.8,reference_year=2009),
       inspection_variants=variants(s))
    manifest['gear_retract_pose']=getattr(s,'gear_retract_pose',{})
    manifest['gear_dimensions']=getattr(s,'gear_dimensions',{})
    try:manifest['studies']=importlib.import_module('control_couplings').studies(s)
    except ImportError:manifest['studies']=[]
    manifest['statistics'].update(motion_links=len(s.motion_links),passive_loop_joints=sum(j.get('passive',False) for j in s.joints))
    manifest['subassembly_statistics']={}
    for label,predicate in [('engines',lambda b:' F404 ' in b['component']),
                            ('carrier',lambda b:s.components[b['component']]['category']=='carrier')]:
        bodies=[b for b in s.bodies if predicate(b)]
        manifest['subassembly_statistics'][label]=dict(bodies=len(bodies),triangles=sum(len(b['mesh'].faces) for b in bodies))
    out=Path(out);(out/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'verification').mkdir(exist_ok=True)
    (out/'verification'/'geometry-validation.json').write_text(json.dumps(check,indent=2)+'\n')
    print(json.dumps(dict(output=str(out),statistics=manifest['statistics'],validation=check,
                         seconds=round(time.monotonic()-started,2))),flush=True)
    return s,manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--aircraft-only',action='store_true')
    parser.add_argument('--intermediate',action='store_true',help='allow incomplete modules for development only')
    args=parser.parse_args();make(args.out,args.aircraft_only,args.intermediate)
