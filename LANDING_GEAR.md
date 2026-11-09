# Landing-gear refinement and RC3 verification

## Scope and references

This is original procedural geometry for an exterior/inspection model, not an engineering replica. Public reference evidence supports the tire nominal sizes, overall retraction directions, trailing main-wheel arms, shock absorbers, brake assemblies and visible fittings. Individual pivot positions, linkage lengths, shrink/planing angles, stroke ranges and door timing are authored approximations chosen to fit the surrounding original airframe and to work in released SolidCraft 0.40 RC3.

- **NAVAIR 04-10-506, Aircraft Tires and Tubes, Table 4-1, 1 January 2007.** The cover states approved public release. F-18A–D main tire: 30×11.5-14.5. Nose tire: 22×6.6-10. Only nominal visual dimensions are used, not servicing procedures or pressures.
  https://navytribe.com/wp-content/uploads/2015/11/navair-04-10-506.pdf
- **Julian Herzog, Finnish F/A-18C HN-441 main gear, ILA 2012. CC BY 4.0.** Primary visual reference for the trailing arm, separate oleo, fork/planing hardware, hydraulic lines and fittings. Photograph used for observation; no pixels or meshes incorporated into the model.
  https://commons.wikimedia.org/wiki/File:HN-441_F-A-18C_Hornet_Finnish_Air_Force_ILA_2012_main_landing_gear.jpg
- **U.S. Navy, 110802-N-JI215-065, MC Timothy Aguirre, USS John C. Stennis. Public domain.** Visual reference for wheel hub and maintenance access.
  https://commons.wikimedia.org/wiki/File:Flickr_-_Official_U.S._Navy_Imagery_-_TX_native-Sailor_removes_the_main_landing_gear_tire_and_wheel_assembly_of_an_F-A-18C_Hornet.jpg
- **Eagle Dynamics, 16 February 2024 development update.** Context for the complexity of the F/A-18C shock/gear animation. No DCS assets were extracted or copied.
  https://www.digitalcombatsimulator.com/en/news/2024-02-16/

## Model content

The replacement adds 200 bodies distributed over articulated components, with 53 native scalar joints and four root-to-follower motion links. It includes twin nose wheels, main wheels with recessed circumferential tread grooves, split-rim fasteners, bearing bosses and valves, alternating visual brake rotor/stator stacks, hydraulic brake housings, trailing main suspension arms, telescoping oleos, shrink struts, main planing cradles, folding drag braces, nose torque scissors, steering fork, launch bar and actuated well doors.

Painted load-bearing parts use the available Steel physical material; wheel assemblies use Aluminum; polished rod/axle surfaces use Stainless Steel. Tire and seal appearance uses the available polymer proxy with dark rough shading because RC3 has no rubber catalog entry. Brake stack composition/count and small fittings are visual approximations; no certified alloy, mass, pressure or strength claim is made.

The R-S-R actuators and R-R-R folding braces are closed native coplanar mechanisms. Their passive joints follow their controlling hinge or oleo. Main wheel planing and shrink are calibrated native motion links. Free wheel spin, steering, suspension and door motion remain native joints. This is kinematic articulation, not a tire-contact or load simulation.

## Final coordinates and motion

Coordinates are metres: +X aft, +Y starboard, +Z up; deck is Z=0.

| Item | Value |
|---|---|
| Main tire radius / width | 0.381 / 0.2921 |
| Nose tire radius / width | 0.2794 / 0.16764 |
| Main trunnions | (10.40, ±0.74, 1.72) |
| Port main retract axis | (0.134665985, −0.860484273, 0.491357190) |
| Starboard main retract axis | (0.134665985, +0.860484273, 0.491357190) |
| Port / starboard retract endpoints | +78.095135401118° / −78.095135401118° |
| Linked main shrink | −0.164102662180 m |
| Linked main wheel planing | +124.209073869498° |
| Nose trunnion / axis | (5.45, 0, 2.04), +Y |
| Nose retract endpoint | +96° |
| Nose wheel steering | ±75° |
| Nose authored oleo travel | −0.12 to +0.08 m |
| Launch-bar pivot / stow | (5.70, 0, 0.60), +117.269471988458° |
| Unchanged shuttle pin | X4.71, Y±0.17, Z0.09 |

The stowed main tires occupy X10.829196..11.590969, |Y|0.419089..1.180862 and Z1.47395..1.76605. The stowed nose tires occupy X3.409288..3.967896, |Y|max0.28382 and Z1.845276..2.403885. The raked upper nose strut, folding braces and raised bar fit below the shallow rear well roof.

The main trunnion mounting heads intentionally pass through the wheel-well roof into the bearing support region: X10.271..10.529, |Y|0.587..0.893, maximum Z1.874081. The integrated duct must clear this local mounting region. This envelope is distinct from the stowed tire envelope.

Gear motion must open the doors and raise the launch bar first, then move the three retract drivers, and close doors only after the tires are inside. Reverse that sequence to extend. The control module reads scene.gear_retract_pose and implements this timing.

## Verification with the exact official release

The test used the SHA-pinned official Linux binary for v0.40.0-rc.3; the builder rejects a differently hashed executable even if its version string matches. Native document format is solidcraft/51.

- All generated coordinates finite; zero degenerate triangles; no body with negative signed volume.
- Geometrically welded main tire, nose tire and annulus tests: zero nonmanifold edges and zero inconsistent edge directions.
- Official RC3 import: 201 bodies including one fixed fixture datum, 53 joints, four motion links.
- All 16 independent driver probes moved and restored.
- Thirty-seven full-travel/intermediate drives exercised suspension extremes, launch bar, each gear root and each door, then returned to launch pose.
- No conflicts, floating chains, loop stops or contact stops.
- Maximum stowed revolute pin residual: 8.41e-8 mm.
- All restored world body bounds match the initial bounds within one micrometre.
- Format-51 save and fresh official RC3 process reopen preserve the model and its assembly state.

Evidence:

- verification/landing-gear-mechanism/geometry-checks.json
- verification/landing-gear-mechanism/gear-receipts/build-receipt.json
- verification/landing-gear-mechanism/full-stroke/full-stroke-receipt.json
- verification/landing-gear-mechanism/summary.json

No renders were produced.

## Integration

Call landing_gear_refinement.refine(scene) after the original aircraft geometry builder and before cockpit/control couplings and internal mounting details. The function removes the old simple gear components and replaces them while preserving root names Nose gear retract, Port main gear retract and Starboard main gear retract. It exposes scene.gear_retract_pose, scene.gear_dimensions and scene.gear_references.

The official native builder now explicitly drives every independent default, including zero, after motion-link creation. This is required when a nonzero link offset is combined with a passive actuator loop. An independent stabilator fixture verifies the fix; it prevents loop projection from leaving a zero-valued cockpit input displaced during initialization.
