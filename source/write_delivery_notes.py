#!/usr/bin/env python3
"""Write the delivery guide from the completed scene and verified native receipts."""
from pathlib import Path
import json,hashlib

ROOT=Path(__file__).resolve().parents[1]
FILES=[
 ('FA18C_Stennis_RC3_Master.sc','Complete aircraft on the Stennis launch deck; closed launch configuration'),
 ('FA18C_RC3_Aircraft.sc','Aircraft alone, with the same complete internal assemblies'),
 ('FA18C_RC3_Cockpit.sc','Canopy open and pilot hidden; reference-guided cockpit and NACES seat accessible'),
 ('FA18C_RC3_Internal_Systems.sc','Skins removed on the inspection side; installed systems and engine cores exposed'),
 ('FA18C_RC3_Structure.sc','Fuel cells and ducts additionally hidden to reveal frames, spars and ribs'),
 ('F404_RC3_Engines.sc','Both engines isolated by visibility, with upper casing and liner quadrants removed'),
]

def write():
    manifest=json.loads((ROOT/'scene_manifest.json').read_text());stats=manifest['statistics'];records=[]
    for name,description in FILES:
        path=ROOT/'native'/name
        receipt=json.loads(path.with_name(path.stem+'-receipts').joinpath('build-receipt.json').read_text())
        if receipt['status']!='complete' or not receipt.get('fresh_reopen'):raise RuntimeError('Native verification incomplete: '+name)
        records.append(dict(file='native/'+name,description=description,bytes=path.stat().st_size,
          sha256=hashlib.sha256(path.read_bytes()).hexdigest(),verification=receipt['verification'],
          release=receipt['release_proof'],fresh_reopen=receipt['fresh_reopen'],
          driven_joint_probes=len(receipt.get('joint_probes',[])),native_format=receipt['saved_native']['format']))
    (ROOT/'verification'/'FINAL_VALIDATION.json').write_text(json.dumps(dict(
        requested_release='v0.40.0-rc.3',release_commit='7001949c49e211a430fe4747221589b2b9384f2c',
        scene_statistics=stats,geometry=manifest['generation_validation'],native_files=records,
        no_rendering=True),indent=2)+'\n')
    rows='\n'.join(f'| [{n}](native/{n}) | {d} |' for n,d in FILES)
    main=records[0]['verification']
    guide=f'''# F/A-18C / USS John C. Stennis — detailed RC3 revision

## Open the model

Open **native/FA18C_Stennis_RC3_Master.sc** in **SolidCraft 0.40.0-rc.3**.

The complete model is saved in native `solidcraft/51` format. It was built, saved,
closed and reopened with the official Linux RC3 executable from release commit
`7001949c49e211a430fe4747221589b2b9384f2c`. The executable SHA-256 was checked
before each native build. The user's installed RC3 AppImage was also identified
against the official release. See `verification/RC3_COMPATIBILITY.md` and
`verification/FINAL_VALIDATION.json` for the recorded evidence.

No beauty renders, screenshots or textures extracted from DCS are needed to use
the deliverable. The model, materials, joints, studies and saved views are stored
in the `.sc` documents themselves. OBJ coordinates are millimetres; the authored
Python geometry is in metres, with +X aft, +Y starboard and +Z up.

## Native files

| File | Starting inspection state |
| --- | --- |
{rows}

The inspection documents preserve named aircraft components and use visibility
to reveal the interiors. Hidden parts are retained and can be shown again in the
browser. The aircraft inspection files omit the carrier. The engine inspection
file retains the hidden aircraft assembly, so installation context can be restored.

## What changed in this revision

### Cockpit

The original generic panel and repeated console blocks were replaced. The main
instrument face is now approximately X4.75m, aligned with the seat, pedal reach
and canopy envelope. DDI, AMPCD, UFC and central-panel envelopes are scaled from
the explicitly measured public OpenHornet replica references; DCS's public guide
supplies the instrument identification and layout cross-check.

The cockpit has separate display bezels and perimeter buttons, UFC keys and option
selectors, warning/caution lenses, analog instruments with movable needles,
individual toggles, rotary controls, guards, circuit breakers, HOTAS hats,
throttles, stick pitch/roll, pedal carriages and toe brakes. Each named panel has
its own organization. Instrument backs, connector shells, representative circuit
cards, switch bodies and looms are present behind the faceplates.

The revised NACES-style seat includes its formed exterior, headbox, survival-pack
and cushion shapes, harness webbing, buckles, leg restraints, hoses and visible
service fittings. The seated pilot is a separate hideable component. Seat height
adjustment is articulated. The seat's internal firing/ejection system is not built.

The standalone cockpit module contains 335 components, 886 material-separated
bodies and 269 moving joints before whole-aircraft integration. Its HUD was checked
against the actual fixed-windscreen and canopy meshes, with no tested edge crossings.
Detailed measurements and source boundaries are in `COCKPIT_REFERENCE.md`.

### Engines

Two original F404-family assemblies occupy the GE -402 overall envelope:
3.9116m long, 0.7112m inlet diameter and 0.8890m maximum diameter. Those values
are direct inch-to-metre conversions of published rounded dimensions, not
manufacturing-tolerance claims. Both open intake ducts meet the fan interfaces.

Each engine contains three fan rotor stages, seven high-pressure compressor
stages, single high- and low-pressure turbine stages, stator rows, separate
concentric shafts, hubs/disks, bearing supports, annular combustion hardware,
injector exterior detail, open perforated liners, bypass passages, afterburner
flameholder and spraybar forms, accessory housings, pipes, flanges and fasteners.

The LP spool links the fan stages to the LPT; the HP spool links the compressor
stages to the HPT. They rotate independently. Each engine has 140 individually
hinged variable guide vanes controlled by two common rings. A common nozzle
actuator drives twelve primary flaps and seals plus twelve divergent flaps and
seals through native motion links. Four outer casing, combustor-liner and
afterburner-liner sectors can be removed independently.

The two engines contain 1,563,136 source triangles and 376 native motion links.
The verified outer-skin clearance before the exposed nozzles is at least43.52mm;
the corrected firewall clears the local forward fastener envelope by6.41mm.
See `research/F404_REFERENCE_AND_MODELING_NOTES.md` for stage provenance,
authored blade counts, axial stations, drivers, materials and limitations.

### Airframe and internal equipment

The aft skin is now one hollow, double-lobed envelope, segmented into removable
panels. It replaces overlapping filled lofts that would obstruct engine cutaways.
Both intakes are continuous, finite-thickness ducts rather than dark blocking caps.

The internal model includes open fuselage frames, longerons, center-barrel load
members, wing attachment lugs, metal spar webs/caps, ribs with through-lightening
holes, skin stringers, wing-fold fittings and thin removable upper/lower wing skins.
Four shaped fuel-cell envelopes, a vent cell, representative transfer lines,
pumps and valves are present. Local bladder-roof recesses clear the dorsal beams.

The nose contains a two-axis articulated antenna assembly and separate slide-out
avionics trays with chassis covers, boards, connector pins and handles. Additional
equipment includes environmental-control housings, heat-exchanger fins, oxygen
equipment exteriors, accessory-drive housings, generators, hydraulic reservoirs,
manifolds, electrical looms, clamps, service pipes and engine-bay heat shields.

### Landing gear and mechanisms

The nose gear now retracts forward. Published 22×6.6-inch nose and30×11.5-inch
main tire dimensions inform the revised tires. The mains fold aft/inboard with
linked shortening and wheel planing so the wheels lie flat in their bays.
Separate oleos, trailing links, brake-pack parts, scissor/drag braces, pins and
fittings are modeled. The gear-cycle study sequences doors and launch bar around
retraction, rather than closing doors across extended wheels.

The canopy, speedbrake, inboard flaps and stabilators have telescoping actuators
with native pin/slider/pin loops. The official RC3 mechanism solver was exercised
at representative and full-travel positions. The master starts with wings spread,
gear down, launch bar engaged, canopy closed and the existing Stennis launch-deck
arrangement, including the jet-blast deflector and carrier detail.

## Inspect and move the model

Use the saved views for the pilot eye, cockpit overhead, instrument backs, NACES
seat, landing gear, internal systems, wing structure, forward avionics, both engine
cores, nozzle mechanism, carrier and island. Use the named native motion studies
for cockpit access, stick/pedals, flap selection, wing fold, gear cycle, hook,
speedbrake, radar/avionics access and each engine's two spools and variable geometry.

The principal engine driver names are:

- `Port F404 N1 shaft rotation` and `Port F404 N2 shaft rotation`.
- `Port F404 nozzle actuator travel`.
- `Port F404 fan variable guide control drive`.
- `Port F404 HPC variable guide control drive`.

Replace `Port` with `Starboard` for the other engine. Native revolute values are
degrees and native slider values are millimetres. The model's generator accepts
slider lengths in metres and converts them when building the native file.

For a continuous engine cutaway, hide casing Q1/Q2, combustor liner Q1/Q2 and
afterburner liner Q1/Q2 for the desired side. The engine inspection file already
applies that state. The other quadrants remain as context.

Cockpit inputs drive the corresponding display mechanisms through native links.
The guide `CONTROL_COUPLINGS.md` lists the exact mappings and independent controls.
Automatic aileron/flap mixing is not simulated: the safe RC3 mapping gives stick
roll control around the launch aileron droop, while the flap selector controls
the trailing and leading-edge flaps. This avoids a redundant constraint loop
that the tested RC3 solver allowed to move the other cockpit input unexpectedly.

## Fidelity and materials

This is a detailed original visual and kinematic reconstruction. Functional
means connected, articulated model mechanisms. It does not run DCS avionics,
simulate combustion/thrust, or reproduce the real flight-control computer.
Published overall dimensions, component organization and visible reference
details guide the model; unpublished internal station measurements, blade profiles,
wall gauges, exact pipe/wire routes and small linkage geometry remain authored
estimates. OpenHornet supplies replica measurements, not production drawings.
Public -400 family engine documents are distinguished from -402-specific facts.

All parts receive an available physical material plus an authored appearance.
Aluminum, Titanium, Steel, Stainless Steel, Copper, Glass, Polycarbonate, Nylon
and ABS Plastic are used where appropriate. RC3 has no Nickel/Inconel entry;
hot-section parts use an explicitly documented Stainless Steel proxy. Rubber,
fabric and composite categories likewise use the nearest available catalog entry
with a separately defined appearance. No verified aircraft mass, stress or
thermal behavior should be inferred from those proxies. See `MATERIALS.md`.

No DCS or OpenHornet mesh, CAD path, texture, screenshot or artwork is embedded
in the aircraft geometry. The source-generated meshes and geometric lettering
are original. Bundled reference documents retain their original authorship and
terms. The VFA-146/NG301 marking scheme is an original historical interpretation,
not a claim to reproduce one verified Bureau Number aircraft in every detail.

## Completed-model statistics and checks

| Measure | Complete master |
| --- | ---: |
| Named components | {stats['components']:,} |
| Material-separated bodies | {stats['bodies']:,} |
| Triangles | {stats['triangles']:,} |
| Source assembly joints | {stats['joints']:,} |
| Articulated source joints | {stats['articulated_joints']:,} |
| Native motion links | {stats['motion_links']:,} |
| Native saved views | {main['named_views']:,} |
| Native saved motion studies | {main['motion_studies']:,} |

Geometry checks found zero nonfinite coordinates, invalid face indices and
degenerate triangles. Joint and motion-link references resolve. Every independently
driven mechanism tested by the native builder moved and restored its launch state;
linked followers were checked against their coupling equations. The saved files
reopened in fresh official RC3 processes, preserving bodies, materials, joints,
visibility, views and studies, with zero reported floating chains or joint conflicts.
These checks establish native compatibility and the tested geometric mechanisms;
they are not a certification of every possible animated combination or physical
collision in a full aircraft systems simulation.

## Rebuild or revise

The `source` directory contains the original procedural model modules. `obj`
contains the per-component millimetre mesh files and `scene_manifest.json` records
materials, joints, links, cameras, studies and inspection definitions. Python3.10+
with its standard library is sufficient for source generation.

From the project folder:

```bash
python3 source/generate.py --out .
python3 source/native_build_rc3.py --cli /path/to/official-rc3/solidcraft-cli --manifest scene_manifest.json --output native/FA18C_Stennis_RC3_Master.sc --view "Launch aircraft" --force
```

The native builder is pinned to the verified official Linux x86_64 RC3 binary.
It uses public import, assembly, material, motion, view and save commands; it does
not hand-edit a newer file into an older format. The runtime itself is installed
separately on Galactica and is excluded from the portable model archive.

The source index is `research/PRIMARY_SOURCE_INDEX.md`; detailed cockpit, engine,
control and landing-gear notes accompany it. `FILE_INDEX.json` and `SHA256SUMS.txt`
describe the self-contained archive. No render is part of this delivery.
'''
    # Restore conventional spaces in numeric prose while retaining exact joint names.
    for a,b in [('least43','least 43'),('by6.41','by 6.41'),('and30','and 30'),('Python3.10','Python 3.10')]:guide=guide.replace(a,b)
    (ROOT/'README.md').write_text(guide)
    materials=manifest['materials'];used={b['material'] for b in manifest['bodies']}
    table=['# Material assignments','',
      'Physical catalog entries and visible appearances are separate. These are the actual authored assignments, not a certified aircraft bill of materials. Unavailable elastomer, composite and hot-section alloys use documented catalog proxies.','',
      '| Appearance alias | Physical catalog entry | RGB | Metallic | Roughness | Opacity |',
      '| --- | --- | --- | ---: | ---: | ---: |']
    for name in sorted(used):
        m=materials[name];table.append(f"| {name} | {m['physical']} | {m['color']} | {m.get('metallic',0)} | {m.get('roughness',.5)} | {m.get('opacity',1)} |")
    (ROOT/'MATERIALS.md').write_text('\n'.join(table)+'\n')
    index=(ROOT/'research'/'PRIMARY_SOURCE_INDEX.md').read_text()
    (ROOT/'REFERENCES.md').write_text('# References for the detailed RC3 revision\n\nSee the detailed cockpit, F404, gear and control notes for how each source was used and which dimensions remain authored estimates. The archived primary PDFs are reference material; no third-party model geometry is embedded.\n\n'+index)
    print(json.dumps({'guide':'README.md','native_files':len(records),'statistics':stats,'all_reopened':True}))

if __name__=='__main__':write()
