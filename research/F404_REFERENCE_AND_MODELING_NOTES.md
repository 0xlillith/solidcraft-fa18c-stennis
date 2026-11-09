# F404-GE-402 engine reference and modeling notes

## Scope of the engine assemblies

The paired engines are original, three-dimensional visual assemblies for the F/A-18C showcase. They contain staged airfoils, separate shafts, internal liners, accessories and native articulated mechanisms. They are designed for inspection and future presentation.

“Functional” here means that the model has real, connected mechanical degrees of freedom: each spool rotates independently, each variable guide vane pitches on its own radial hinge, the exhaust flaps follow a common actuator, and shell/liner sectors can be removed. The files do not model combustion, thrust, gas dynamics, engine controls, durability or engineering performance. A photoreal rendering has not been generated for this revision.

No DCS mesh, texture, extracted game asset, third-party engine CAD, GE drawing or proprietary airfoil profile is included. All geometry is original procedural source. Published photographs and cutaways were used for visual interpretation only.

## What the primary sources establish

| Feature | Evidence and applicability |
|---|---|
| F/A-18C/D engine identification | GE identifies the F404-GE-402 as the Hornet C/D powerplant. The 2020 family datasheet is the model-specific dimensional authority. [1] |
| Published overall size | The GE -102/-103/-402 grouping lists 154 in length, 35 in maximum diameter and 28 in inlet diameter. The model converts those inch values to 3.9116 m, 0.8890 m and 0.7112 m. This is unit-conversion precision, not a claim to manufacturing tolerances. [1] |
| Spool and stage arrangement | NASA describes the F404-GE-400 family architecture as three fan stages driven by one low-pressure turbine stage, and seven compressor stages driven by one high-pressure turbine stage. The model retains this 3/7/1/1 organization. [2, 3] |
| Variable geometry | Public NASA descriptions identify variable fan and compressor guide geometry. The GAO component diagram additionally identifies compressor inlet and first/second stator rows. These rows are articulated in the model. [2, 4] |
| Combustor and bypass | Public family descriptions show an annular combustor and a bypass path around the core, with bypass air used in augmentor/nozzle cooling. The model keeps these passages open. [3, 4] |
| Exhaust mechanism | NASA describes a hinged, cam-linked hydraulic variable exhaust and explicitly identifies 12 primary flap hinges and 12 sectored hinge seals on the -400. The model adopts that public family architecture. [2] |
| Afterburner external arrangement | NASA's -400 description identifies 24 main and six pilot spraybars. The visible model includes that number of external forms, while avoiding a claim that every -402 installation detail is identical. [2] |
| Titanium fan and outer duct references | NASA's materials paper identifies a production titanium F404 fan blade. The GE-authored NASA composite-duct study distinguishes its experimental replacement from the production titanium outer duct. The model uses Titanium for those supported visual categories. [5, 6] |
| Compact support layout | The GE-authored 1984 paper describes eliminating a support frame/sump/bearing between the combustor and turbines. The model does not insert a fictitious intermediate hot-section bearing there. [7] |

The public sources span different dates and variants. The -402 identification and overall dimensions are specifically supported by GE's family datasheet; the detailed internal layout is a cautious F404-family interpretation from public -400 documentation. The -402 has development changes, particularly in its hot section and augmentor, so the visualization must not be described as an exact -402 production cutaway. [1]

An older 1984 GE paper labels its illustrated family engine 159 in long. The current model deliberately uses the later GE datasheet's -402-group figure of 154 in. The dimension difference is recorded rather than silently mixing the two documents. [1, 7]

## Original geometry and authored approximations

The following are authored display choices. They are not reverse-engineered or verified GE dimensions:

- Internal axial stations and detailed diameters.
- Rotor/stator blade counts, section shapes, camber, twist, sweep, clearances and roots.
- Bearing type, exact count, location, race cross-section and rolling-element count.
- Main combustor injector count, cup details, perforation size and liner hole pattern.
- Accessory sizes, housing shapes, fasteners, hose/pipe routing and nameplate placement.
- Exact -402 hot-section profiles and alloy grades.
- Nozzle actuator stroke, flap angles, linkage ratios, roller/cam shapes and neutral aperture.
- Fan/HPC guide-ring travel and its relation to individual vane pitch.

Each blade is a closed solid with multiple radial sections, camber, twist, sweep and a finite root/tip closure. Its tip wraps onto a cylindrical surface. Annular parts have actual central openings; none uses an opaque fan-shaped cap to imitate an engine passage. The combustor and afterburner liners contain real open bores with thickness and hole walls.

### Authored repeated-detail counts, per engine

| Row or assembly | Authored count |
|---|---:|
| Fan rotor stages 1 / 2 / 3 | 28 / 34 / 40 blades |
| HPC rotor stages 1–7 | 36 / 38 / 40 / 42 / 46 / 48 / 50 blades |
| HPT / LPT rotors | 58 / 72 blades |
| Fan inlet variable guide row | 24 individually hinged vanes |
| HPC inlet variable guide row | 34 individually hinged vanes |
| HPC variable stator rows 1 / 2 | 40 / 42 individually hinged vanes |
| Other fan/HPC/turbine stators | Repeated three-dimensional rows; exact counts are display choices in source |
| Main combustor injector exteriors | 18 |
| Afterburner main / pilot external bars | 24 / 6, based on public -400 family reference |
| Convergent primary flap / primary seal sectors | 12 / 12 |
| Divergent secondary flap / secondary seal sectors | 12 / 12 |
| Main casing / combustor liner / afterburner liner sectors | 4 / 4 / 4 removable quadrants |

The first seven numerical blade-count rows above should never be relabeled as verified GE production data.

### Authored axial stations

The assembly uses +X aft and engine-local distance u measured from the front interface.

| Feature | Local u in metres |
|---|---:|
| Front inlet interface | 0 |
| Fan rotor centers | 0.205, 0.405, 0.585 |
| HPC rotor centers | 0.865 to 1.423 in 0.093 steps |
| Combustor perforated liner | 1.553–1.913 |
| HPT rotor center | 2.045 |
| LPT rotor center | 2.233 |
| Afterburner perforated liner | 2.405–3.205 |
| Primary exhaust hinge | 3.200 |
| Primary/secondary throat hinge | 3.540 |
| Nozzle exit | 3.9116 |

Aircraft installation:

| Item | Position |
|---|---|
| Port axis | Y = -0.71 m, Z = 1.98 m |
| Starboard axis | Y = +0.71 m, Z = 1.98 m |
| Engine front | X = 12.7684 m |
| Engine exit, neutral authored pose | X = 16.6800 m |

## Native articulation and inspection

The engine source uses the shared scene API to create native components and joints. Each engine is rigidly mounted to the aircraft through its named mounting component. Internal stationary structure attaches to that mount. The LP and HP groups are not fused to each other.

Use the following driver names, replacing “Port” with “Starboard” for the second engine.

| Driver joint | Type | Source limits | Native RC3 units |
|---|---|---|---|
| Port F404 N1 shaft rotation | Revolute | -36000 to +36000 | Degrees |
| Port F404 N2 shaft rotation | Revolute | -36000 to +36000 | Degrees |
| Port F404 nozzle actuator travel | Slider | -0.025 to +0.025 m | -25 to +25 mm |
| Port F404 fan variable guide control drive | Revolute | -0.75 to +0.75 | Degrees |
| Port F404 HPC variable guide control drive | Revolute | -0.75 to +0.75 | Degrees |

All drivers default to zero.

N1 contains the fan rotor stages, their disks, the inner shaft and the LPT rotor. N2 contains the seven HPC rotor stages, their disks, the hollow outer shaft and the HPT rotor. Both turn about the same longitudinal axis.

The nozzle slider drives all 12 primary flaps and 12 primary seals at 0.28 degrees per native millimetre. The 12 divergent secondary flaps and 12 secondary seals are hinged to their corresponding primary sector and use -0.22 degrees per millimetre relative rotation. Consequently, each engine has 48 linked nozzle hinges. These are original demonstration ratios. The authored cam rails follow that demonstration relation; they are not a GE cam profile or nozzle schedule.

The two variable-guide control rings drive 140 individually hinged vanes per engine at a display ratio of 12 degrees of vane pitch per degree of control-ring rotation. The guide pitch range is therefore ±9 degrees. The common ring groups demonstrate coordinated motion; the ratio is not claimed to reproduce the engine controller.

The neutral nozzle is visually open, with authored throat radius 0.285 m and exit radius 0.345 m. It is suitable for the launch showcase without purporting to identify a real engine power setting. Animation frame counts do not imply real RPM.

### Inspection visibility

For a continuous top-half cutaway, hide these six components for each side:

- Port F404 casing Q1
- Port F404 casing Q2
- Port F404 combustor liner Q1
- Port F404 combustor liner Q2
- Port F404 afterburner liner Q1
- Port F404 afterburner liner Q2

Q1 and Q2 are the upper quadrants. Their complementary Q3 and Q4 sectors remain below. The casing groups also contain corresponding core pressure-shell sectors, so hiding the outer top does not leave a second opaque core wall in the way.

Every casing and liner quadrant also has a native slider named “[component name] inspection extraction”. Casing extraction range is 0–0.85 m; combustor liner 0–0.48 m; augmentor liner 0–0.55 m. These sliders are presentation tools for disassembly inspection, not maintenance handling procedures.

Useful component filters are “LP spool”, “HP spool”, “stators”, “bearing supports”, “combustor injectors”, “afterburner internals”, “accessories”, “nozzle mechanism” and “nozzle actuator ring”.

## Materials and their limits

The exact Solidcraft 0.40.0-rc.3 built-in physical palette was inspected. It contains Titanium, Aluminum, Steel and Stainless Steel, but does not contain a Nickel or Inconel physical entry.

| Part group | Assigned physical material | Basis / limitation |
|---|---|---|
| Fan blades and titanium outer duct/case categories | Titanium | Public production-family support for the fan/outer duct; exact alloy and all ancillary parts are not verified. [5, 6] |
| Front compressor visualization | Titanium | Closest plausible cold-section visual assignment; individual stage alloy specifications are not asserted. |
| Turbine blades, combustor liner, afterburner and nozzle hot surfaces | Stainless Steel | Explicit built-in proxy for unavailable hot-section alloy entries. Heat-tinted appearances do not change the physical proxy. |
| Shafts, bearing parts, bolts, actuator rods and pipes | Stainless Steel | Built-in metal proxy; exact steels are not claimed. |
| Accessory housings | Aluminum | Visual material interpretation, not a production bill of materials. |
| Bearing cages / small warm-toned service details | Copper | Built-in proxy for visually similar copper-alloy detail. |
| Flexible hose exterior | ABS Plastic | Built-in nonmetal proxy; real elastomer/composite composition is not represented. |

Warm brown, gray, darkened and blue heat-tinted appearances are separately defined in the source. They avoid implying that the unavailable physical material has been added to the built-in palette.

## Geometry validation

The source was compiled and rebuilt without rendering. The two-engine build, after articulation and detail generation, contains:

| Measure | Both engines |
|---|---:|
| Components | 424 |
| Material-separated bodies | 1,136 |
| Triangles | 1,563,136 |
| Vertices | 863,304 |
| Joints | 424 |
| Native motion links | 376 |
| Independently hinged variable guide vanes | 280 |

The numerical checks found no nonfinite vertices, degenerate triangles, missing parent/child components, missing link targets or duplicate driven link targets. Representative full and quarter perforated liners and a twisted blade have zero boundary edges and zero nonmanifold edges. This checks the intended solid topology; it does not certify engineering interference tolerances.

Both installed engine bounds run from X = 12.7684 m to 16.6800 m. Maximum radial extent in the neutral authored pose is approximately 0.44099 m, inside the GE-derived 0.4445 m maximum envelope. A separate integration audit checks aircraft-skin and firewall clearances.

The detailed machine-readable check is saved alongside this note as F404_GEOMETRY_VALIDATION.json. Native whole-aircraft joint motion is verified by the project integration process.

## Primary source register

1. **GE Aerospace, F404 Family datasheet, ©2020.** The F404-GE-402 application and dimensional table are on the two-page manufacturer datasheet.  
   https://www.geaerospace.com/sites/default/files/2022-01/F404%20Family%20Data%20Sheet_UPDATED.pdf

2. **James T. Walton and Frank W. Burcham Jr., NASA TM 88273, December 1986, _Exhaust-Gas Pressure and Temperature Survey of F404-GE-400 Turbofan Engine_.** Engine description and variable-nozzle/augmentor architecture; PDF pages 5–6.  
   https://ntrs.nasa.gov/api/citations/19880010923/downloads/19880010923.pdf

3. **Timothy R. Conners, NASA TM 4140, 1989, _Measurement Effects on the Calculation of In-Flight Thrust for an F404 Turbofan Engine_.** Family architecture and shaft/component naming.  
   https://ntrs.nasa.gov/api/citations/19900002425/downloads/19900002425.pdf

4. **US Government Accountability Office, PSAD-80-72, September 30, 1980, _Are Management Problems in the Acquisition of Aircraft Gas Turbine Engines Being Corrected?_** Labeled Navy/GE F404 component diagram, PDF page 53.  
   https://www.gao.gov/assets/psad-80-72.pdf

5. **D. L. McDanels, T. T. Serafini and J. A. DiCarlo, NASA TM 87132, 1985, _Polymer, Metal, and Ceramic Matrix Composites for Advanced Aircraft Engine Applications_.** Figure 13 identifies the production titanium F404 fan blade while comparing an experimental composite blade.  
   https://ntrs.nasa.gov/api/citations/19860003939/downloads/19860003939.pdf

6. **T. Stotler and S. Yokel / General Electric, NASA CR-182228, 1989, _PMR Graphite Engine Duct Development_.** Public GE-authored research comparing an experimental composite outer duct with the production titanium arrangement. The experimental composite is not assumed to be the showcase engine's material.  
   https://ntrs.nasa.gov/citations/19900000721

7. **B. A. Riemer and S. F. Powel IV / General Electric, ICAS-84-5.4.2, 1984, _F404 New Standards for Fighter Aircraft Engines_.** GE-authored family layout discussion and cross-section comparisons.  
   https://www.icas.org/icas_archive/ICAS1984/ICAS-84-5.4.2.pdf

8. **James Bridges, Mark P. Wernet and Franco C. Frate / NASA Glenn, 2011, _PIV Measurements of Chevrons on F400-Series Tactical Aircraft Nozzle Model_.** Additional manufacturer-model evidence for the 12-sector nozzle, PDF page 3. The experimental chevrons were not copied into the historic Hornet nozzle.  
   https://ntrs.nasa.gov/api/citations/20110008608/downloads/20110008608.pdf

9. **GE Aerospace / Cole Massie, October 7, 2020, _GE's Most Versatile Fighter Engine Is Ready for the Next Generation of U.S. Air Force Pilots_.** GE-published historical cutaway used as a visual reference, not a source of measured internal dimensions.  
   https://www.geaerospace.com/news/articles/people-product/ges-most-versatile-fighter-engine-ready-next-generation-us-air-force-pilots

10. **GE Aerospace F404 product page.** Secondary manufacturer cross-check of the overall family. A current application carousel contains a “F414-GE-402” naming typo; this model follows the correct F404-GE-402 identification in the datasheet, not that typo.  
    https://www.geaerospace.com/military-defense/engines/f404

Reference access and model note: 2026-11-09.
