# Cockpit reference and implementation notes

This cockpit is an original, reference-guided reconstruction of a single-seat Legacy Hornet interior for the RC3 project. It replaces the earlier oversized generic panels and long instrument-to-seat gap with separately measured instrument envelopes, named panel families, physical control caps and instrument housings. It remains a visual and articulated assembly. Public replica dimensions and photographs do not establish certified aircraft manufacturing dimensions, electrical routing or avionics behavior.

## Sources and provenance

| Primary public source | Used for | Scope and restrictions |
|---|---|---|
| [Eagle Dynamics F/A-18C public guide](https://www.digitalcombatsimulator.ru/upload/iblock/ea9/lxf69u2uk1fhqq7ndb55z9egzabe8hdg/DCS%20FA-18C%20Early%20Access%20Guide%20EN.pdf) | Main, left, right and center cockpit arrangements; instrument identification; DDI numbering; UFC keypad and option-selector arrangement; console families. Particularly the cockpit section around printed pp. 38–66. | Reference viewing only. No DCS mesh, texture, screenshot, font or screen artwork is embedded in the deliverable. Simulator documentation describes a particular represented configuration and is not a manufacturing drawing. |
| [OpenHornet source at pinned commit](https://github.com/jrsteensen/OpenHornet/tree/77c7b2c07240d9d6062c16ed6e533bf2ed8bfce6) | Numeric envelope dimensions from explicitly declared SVG page units and 3MF mesh bounds; physical layout cross-check. | OpenHornet describes a 1:1 F/A-18C home cockpit replica. Its source carries CC BY-NC-SA 4.0 terms. The project does not copy or bundle its SVG paths, meshes, CAD, electronics design, artwork or build drawings. Only measured dimensional facts and layout observations inform independently authored geometry. Replica dimensions are not warranted as aircraft production dimensions. |
| [OpenHornet hardware documentation](https://docs.openhornet.com/hardware/) | Assembly names and intended hardware organization. | Home-simulator structure and materials do not establish actual aircraft structure or materials. |
| [Martin-Baker Mk14 NACES](https://martin-baker.com/ejection-seats/mk14-naces/) | Exterior seat shell, headbox, cushion, harness, leg-restraint and visible fitting appearance. | Manufacturer photographs are visual references. No photograph is embedded. Current product imagery can differ from the aircraft's historical seat equipment. Internal firing or ejection mechanisms are not modeled. |
| [Martin-Baker NACES data sheet](https://martin-baker.com/wp-content/uploads/2023/11/NACES-2025-Data-Sheet-2.pdf) | Seat identification and broad external assembly context. | Identification/reference only. Authored seat dimensions and mounting details remain estimates. |
| [NASA F/A-18 aircraft fact sheet](https://www.nasa.gov/wp-content/uploads/2021/09/fs-006-afrc_0.pdf) | Aircraft-family scale and three-view context coordinated with the exterior model. | No cockpit station or internal structural measurement is claimed from this source. |

OpenHornet reference commit: `77c7b2c07240d9d6062c16ed6e533bf2ed8bfce6`. Assembly drawings marked “DO NOT SCALE” were not treated as dimensional scale drawings. The measurements below came from explicit artifact units and outer envelopes. All resulting panel outlines, lettering, fasteners, switches, screen marks, housings and cable routes in `source/cockpit.py` were written procedurally for this project.

### Measured reference envelopes

Dimensions are width × height. The extra decimal places identify the measurement conversion, not a claim of equal accuracy in the real aircraft.

| Part | Envelope, mm | Measurement source within the pinned OpenHornet release |
|---|---:|---|
| DDI bezel | 163.5125 × 172.7200 | `OH1_Upper_Instrument_Panel/OH1A3 - ASSY, DDIv2/Manufacturing/FDM_OH1A3-10_DDI BEZEL_-_V8.3mf`; inch-unit outer bounds |
| AMPCD bezel | 167.0050 × 182.6228 | `OH2_Lower_Instrument_Panel/OH2A3A1 - ASSY, AMPCD MODULE/Manufacturing/FDM_OH2A3A1-14_AMPCD BEZEL_-_V16.3mf`; inch-unit outer bounds |
| UFC main legend face | 173.0375 × 114.3000 | `OH1_Upper_Instrument_Panel/OH1A8 - ASSY, UPFRONT CONTROL PANEL/Manufacturing/RMRK_OH1A8A1-114_UFC LEGEND PLATE_-_V44.svg`; declared centimetre page dimensions |
| Central upper panel face | 535.9400 × 230.1875 | `OH1_Upper_Instrument_Panel/Manufacturing/ACRL_.25_OH1A1-12_UPPER INSTRUMENT PANEL FACE_-_V105.SVG`; declared centimetre page dimensions |
| Landing gear panel | 88.1063 × 64.2938 | Corresponding lower-instrument-panel legend SVG envelope |
| Select-jettison panel | 165.1000 × 132.6404 | Corresponding lower-instrument-panel legend SVG envelope |
| Fuel panel | 144.4625 × 74.6125 | Corresponding left-console legend SVG envelope |
| APU/engine-crank panel | 118.7450 × 49.7840 | Corresponding left-console legend SVG envelope |
| FCS panel | 144.4625 × 55.5625 | Corresponding left-console legend SVG envelope |
| Communications panel | 144.4625 × 179.3875 | Corresponding left-console legend SVG envelope |
| Electrical panel | 144.4625 × 65.0779 | Corresponding right-console legend SVG envelope |
| ECS panel | 144.4625 × 93.6625 | Corresponding right-console legend SVG envelope |
| Interior-lighting panel | 144.4625 × 84.1375 | Corresponding right-console legend SVG envelope |
| Sensor panel | 144.4625 × 74.6125 | Corresponding right-console legend SVG envelope |

The full physical panel arrangement is an authored fit within the retained aircraft shell. Relative positions, slopes, thicknesses, screw locations, control travel and internal clearance openings are reconstruction choices. They should not be quoted as measured aircraft dimensions.

## Geometry and arrangement

All source coordinates are metres: +X aft, +Y starboard, +Z upward from deck height. DDI centers are at X4.752, Y±0.1855, Z2.864, with a 12° inclined face. The UFC face is at X4.747, Y0, Z2.893. The AMPCD is at X4.914, Y0, Z2.554, inclined 23°. The central panel has mounting apertures behind the instrument modules, rather than a solid backing wall passing through all housings.

The reference panel widths constrain the cockpit arrangement. The DDI/UFC group is approximately 0.54 m wide; the outboard cheek panels extend beyond that group. The pilot's torso is around X5.56 and the main face around X4.75, replacing the former face near X4.10. The pedal hinge centers are at X4.575, Y±0.157, Z2.176. Side-console fields are pitched and rolled, with individual panels concentrated mainly between X5.10 and X5.90. The exterior-light panel runs along the outboard side of the throttle quadrant.

The main panel includes left and right DDIs, UFC, HUD control strip, AMPCD, IFEI, standby attitude/flight instruments, RWR face, warning panels, heading/course controls and lower ECM/RWR controls. The cheek and vertical panels include master arm, air-to-air/air-to-ground selectors, emergency/select jettison, gear, flap, anti-skid, hook bypass, brake-pressure/parking-brake, hook/hydraulic, wing-fold, HMD and spin controls.

The left console contains distinct fire-test, exterior-light, fuel, APU/crank, FCS, communications, OBOGS, MC/hydraulic-isolation, antenna-selection and generator-tie panels. The right console contains electrical, ECS, interior-light, sensor, crypto and defog panels. Small sidewall breaker rows, the canopy switch and canopy lock lever are separate features.

Each DDI and the AMPCD has twenty individually articulated perimeter buttons. The UFC uses a 3×4 keypad, five option selectors, seven function buttons, radio-channel and volume controls, scratchpad and option windows. Labels and display line work are original geometric lettering. Their content is an illustrative static state, not a simulated avionics page or an indication linked to aircraft physics.

### Backs, structure and inspection

Instrument housings include rear plates, open side rails, cooling details, representative circuit boards, connector shells, pins and routed looms. Console switch backs include terminal stems, short wires and grouped harnesses. These are original illustrative packaging; they do not reproduce a real F/A-18 electrical schematic, verified connector assignment or internal avionics design.

Independent visibility groups include:

- `Pilot`: hide for an unobstructed cockpit inspection.
- `Ejection seat`: exterior NACES-style seat shell, cushion, harness and fittings.
- `Cockpit liners`: removable side/rear lining, floor finish and heel plates.
- `Cockpit fixed`: floor base, rails, console bearers, seat tracks, ducts, fixed wiring and instrument support.
- `Panel ...`: individual visible instrument/console faces.
- `... electronics`: instrument backs and their external looms.
- `... underside`: each console panel's switch backs and wiring.
- `HUD assembly` and `Standby compass`: separate fixed assemblies.

Hiding a component does not necessarily hide its descendants in every SolidCraft visibility command. For an inspection, hide the matching child controls as well if the native command does not recurse.

## Articulation interface

The source uses metres for slider ranges; the native exporter converts sliders to millimetres. Revolute joints use degrees. Every row below has default 0. The central generator calls source/control_couplings.py after the cockpit is built; that module applies the integrated driver limits below and adds the documented geometric links. See CONTROL_COUPLINGS.md. The cockpit geometry module itself does not impose external links.

| Stable joint name | Native range | Parent / purpose |
|---|---:|---|
| `Control stick pitch` | −18° to +18° | Cockpit fixed → pitch cradle |
| `Control stick roll` | −18° to +18° | Pitch cradle → stick |
| `Left rudder input` | −45 to +45 mm | Cockpit fixed → left pedal carriage |
| `Right rudder input` | −45 to +45 mm | Cockpit fixed → right pedal carriage |
| `Left toe brake`, `Right toe brake` | −4° to +18° | Respective carriage → pedal |
| `Left throttle travel` | −25° to +40° | Cockpit fixed → left throttle |
| `Right throttle travel` | −25° to +40° | Cockpit fixed → right throttle |
| `Landing gear cockpit handle motion` | −55° to 0° | Landing-gear panel → handle |
| `Arresting hook cockpit handle motion` | −50° to 0° | Hook/hydraulic panel → handle |
| `Flap selector cockpit handle motion` | −30° to +15° | Landing-gear panel → switch |
| `Wing fold cockpit handle motion` | 0° to +90° | Wing-fold panel → handle |
| `Canopy manual lock lever` | −35° to +35° | Cockpit fixed → lever |
| `Seat height adjustment` | −60 to +60 mm | Cockpit fixed → seat; optional pilot follows seat |

Pushbuttons generally move 0–2.5 mm inward, rotary knobs use authored limits, guarded switches have separate guard hinges, and breakers pull out 0–6 mm. HOTAS hats have two orthogonal axes; trigger, paddle and throttle switches move with their parent grips. Eight analog gauge needles have independent indicator joints. These joints provide controllable mechanical poses. Detents, interlocks, avionics logic, loads, force feedback and physiological/ejection behavior are not simulated.

## Materials

Catalog physical materials and visible appearance are independent. The alias names preserve intended surface distinction, while the native builder resolves the closest available catalog entry. A painted aluminum panel can therefore have a nearly nonmetallic black or gray visible coating.

| New alias family | Requested physical catalog material | Visual interpretation / limitation |
|---|---|---|
| `cockpit_gray`, `panel_black`, `seat_black` | Aluminum | Painted structure, black instrument panels and painted seat shell. Exact alloys and coating specifications are not established. |
| `button_gray`, `warning_dim`, `indicator_green` | ABS Plastic | Molded caps and colored lenses; appearance is illustrative. |
| `display_dark`, `display_green`, `instrument_glass` | Glass | Opaque display/instrument-face appearance with separate graphic marks. These aliases do not create nested transparent volumes. |
| `connector_blue` | Aluminum | Dark blue/gray connector shells. |
| `pcb_green` | ABS Plastic | Visual proxy for coated circuit-board material; not FR-4 material certification. |
| `wire_blue`, `wire_red` | Nylon | Insulation appearance only; real insulation construction is unspecified. |
| `seat_cushion`, `harness_olive` | Nylon | Fabric appearance; cushion foam and webbing are not materially homogeneous nylon in reality. |
| `pilot_visor` | Polycarbonate | Opaque dark visor appearance. |
| Existing `hud_glass` | Glass, inherited project optical settings | The HUD combiner remains a separate transparent solid. |

## Validation checkpoint

The cockpit-only source build contains **335 components, 886 bodies, 335 joints, 269 moving joints, 401,026 triangles and 4,263 modeled detail instances**. The source geometry check found no nonfinite vertices, invalid mesh indices, degenerate triangles, missing component references or joint cycles. These are source-build checks, not a claim that the final full native assembly has passed every SolidCraft test.

HUD transparent bounds are X4.470–4.573, Y−0.091–0.091 and Z3.105–3.255 m. Against the current generated closed windscreen/canopy meshes, the minimum surface distances are **92.209 mm to the windscreen** and **143.020 mm to the canopy**, with no tested HUD-edge crossings. The check uses triangle/segment distances on the actual source meshes. It is not a swept collision test of every possible canopy or seat pose.

Machine-readable results and stable control axes are in `research/cockpit_validation.json`. The source hash at this checkpoint is `2a11d67ee4d002bcb058785d11af6be46b69c658a3f58d79bcbd7d89d6fae0d9`. No beauty render was produced for this revision.
