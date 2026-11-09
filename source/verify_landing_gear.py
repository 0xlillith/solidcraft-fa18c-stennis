#!/usr/bin/env python3
"""Check full gear endpoints and closed-loop residuals using official RC3 only."""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parent))
from native_build_rc3 import MCP,require_solution,verify_release
from scene_api import Scene,box
from landing_gear_refinement import refine

root=Path(__file__).resolve().parent.parent
folder=root/'verification/landing-gear-mechanism'
receipt_dir=folder/'full-stroke'
receipt_dir.mkdir(parents=True,exist_ok=True)
cli=root/'runtime/official-rc3/solidcraft-0.40.0-rc.3-linux-x86_64/bin/solidcraft-cli'
proof=verify_release(cli)
s=Scene();s.add('Airframe','Gear test fixed datum','steel',box((8,0,2.6),(.12,.12,.12)));data=refine(s)
m=MCP(cli,[folder,receipt_dir],receipt_dir,180,2,10)
records=[];results={}
def state():
    j=m.execute('joint.list');require_solution(j,'full stroke')
    assert not j.get('floating'),j
    byname={x['name']:x for x in j['joints']}
    residual=[]
    for x in j['joints']:
        if x['type']!='revolute':continue
        a=x['frame_a']['origin'];b=x['frame_b']['origin']
        error=math.sqrt(sum((aa-bb)**2 for aa,bb in zip(a,b)))
        residual.append(error)
    assert max(residual,default=0)<.02,('revolute pin mismatch mm',max(residual))
    return j,byname
def drive(name,value):
    r=m.execute('joint.drive',{'joint':name,'value':value,'quiet':True});require_solution(r,name)
    assert not any(r.get(k) for k in ('held','stopped_by_loop','stopped_by_contact')),(name,value,r)
    j,byname=state();actual=byname[name]['values'][0]['value']
    assert abs(actual-value)<.001,(name,value,actual)
    records.append({'joint':name,'requested_native':value,'actual_native':actual,'result':r})
def world_bodies():
    components=m.execute('component.list',{'compact':True,'bodies':True})['components']
    transforms={c['name']:c['occurrences'][0].get('transform') for c in components if c.get('occurrences')}
    bounds={}
    for body in s.bodies:
        a=transforms.get(body['component'])
        verts=body['mesh'].vertices
        if a:verts=[tuple(sum(a[c][r]*v[c] for c in range(3))+a[3][r]/1000 for r in range(3)) for v in verts]
        bounds[body['name']]={'component':body['component'],'label':body['label'],'min':[min(v[k] for v in verts) for k in range(3)],'max':[max(v[k] for v in verts) for k in range(3)]}
    return bounds
try:
    opened=m.execute('doc.open',{'path':str(folder/'gear.sc'),'read_only':True})
    state();results['down']=world_bodies()
    for name,values in [('Nose oleo compression',[-120,80,0]),('Port main oleo compression',[-12,14,0]),('Starboard main oleo compression',[-12,14,0])]:
        for value in values:drive(name,value)
    drive('Launch bar lift',data['nose']['launch_bar_stow'])
    for label in ('Port','Starboard'):
        target=data['main_frames'][label]['angle']
        for i in range(1,6):drive(label+' main gear retract',target*i/5)
    for i in range(1,6):drive('Nose gear retract',data['nose']['angle']*i/5)
    results['up_doors_open']=world_bodies()
    for name in ('Nose Port door','Nose Starboard door','Port main bay door','Starboard main bay door'):drive(name,0)
    results['up_closed']=world_bodies()
    final_joints,_=state()
    # Cycle back through the reverse choreography.
    for name,value in [('Nose Port door',83),('Nose Starboard door',83),('Port main bay door',87),('Starboard main bay door',87)]:drive(name,value)
    for name in ('Nose gear retract','Port main gear retract','Starboard main gear retract'):drive(name,0)
    drive('Launch bar lift',0)
    results['restored']=world_bodies()
    errors=[]
    for name,b in results['down'].items():
        a=results['restored'][name]
        error=max(abs(x-y) for key in ('min','max') for x,y in zip(a[key],b[key]))
        if error>1e-6:errors.append({'body':name,'bounds_error_m':error})
    assert not errors,errors
    receipt={'success':True,'official_release':proof,'drive_count':len(records),'drives':records,
             'final_stowed_joints':final_joints,'body_bounds_m':results,'restored_bounds_exact_within_1um':True}
    (receipt_dir/'full-stroke-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    tyres={k:v for k,v in results['up_closed'].items() if 'tyre with' in v['label']}
    print(json.dumps({'success':True,'drives':len(records),'stowed_tyre_bounds_m':tyres},indent=2))
except Exception as exc:
    (receipt_dir/'failure.json').write_text(json.dumps({'error':str(exc),'drives':records},indent=2)+'\n')
    raise
finally:
    m.close()
