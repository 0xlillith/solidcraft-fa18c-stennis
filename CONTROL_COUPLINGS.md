# Cockpit couplings and motion studies

`source/control_couplings.py` adds native geometric demonstration links after the aircraft, cockpit, internal mechanisms, engine assemblies and landing-gear refinement have been built. It exposes `connect(scene)` and `studies(scene)`. It does not change the generator or native builder.

These are controllable assembly relationships. They do not simulate the Hornet's flight-control computers, air data, engine-control schedules, avionics, loads or aerodynamic response. The ratios below are authored demonstration choices. Each input's complete permitted interval is checked against its followers' limits.

## Driver map

All equations in this table use native units: degrees for revolute joints and millimetres for sliders. Source slider limits and motion-study key values remain metres; the native builder performs that conversion.

| Cockpit driver | Input interval | Followers and relation |
|---|---:|---|
| `Control stick pitch`, P | −18°…+18° | Both stabilators = P − 4°. Result: −22°…+14°. |
| `Control stick roll`, R | −18°…+18° | Port aileron = 30° − 0.8R; starboard = 30° + 0.8R. Each remains within 15.6°…44.4°. |
| `Left rudder input`, Y | −45…+45 mm | Right pedal = −Y; both rudders = 2Y/3 degrees; nose-wheel steering = 0.9Y degrees. |
| `Flap selector cockpit handle motion`, F | −30°…+15° | Both trailing-edge flaps = F + 30°; all four leading-edge flaps = 0.4F + 12°. Authored selector positions: AUTO −30°, HALF 0°, FULL +15°. |
| `Landing gear cockpit handle motion`, G | −55°…0° | Each gear-root stow endpoint multiplied by G/−55. The endpoint is read from the final joint limits; no previous geometry's angle is hardcoded. The integrated target values are recorded with the gear verification; the latest refined nose target is +96°, with main targets ±78.0951354°. |
| `Arresting hook cockpit handle motion`, H | −50°…0° | Hook lowering = −0.84H; 0°…42°. |
| `Wing fold cockpit handle motion`, W | 0°…90° | Both wing folds = 100W/90; 0°…100°. |

All listed cockpit inputs default to zero. This gives the saved launch geometry: aileron and trailing-edge flap 30°, leading-edge flap 12°, stabilators −4°, gear extended, hook raised and wings spread.

The right pedal and exterior linked surfaces are followers. Their meshes and joints remain distinct; the links can be changed or removed in SolidCraft for independent surface posing. Toe brakes, launch bar and gear doors retain their independent joints. The four refined gear shrink/planing links and engine-internal links are preserved.

The throttles remain independently poseable controls. Engine shafts, nozzle actuator and variable-guide rings have their own demonstrable motion. A fixed throttle-angle-to-shaft-rotation or throttle-angle-to-nozzle law is not invented.

## Aileron mixing limitation established in RC3

The requested coaxial mechanism was tested in the official SolidCraft 0.40.0-rc.3 executable: a real carrier for droop, a second coaxial roll joint and a passive outer-wing-to-aileron total-stop joint. Although the loop remained geometrically closed, RC3 redistributed the other free control input when one input moved. On link creation, a requested 30° droop / 0° roll state settled at approximately 20.4266° / −1.7685°, moving both cockpit inputs. Sequentially driving the inputs did not preserve independent settings.

That loop is **not included**. The accepted direct linkage keeps independent roll and flap controls and keeps each aileron within the intended surface limits. **Automatic aileron/flap mixing is omitted:** the flap selector changes trailing- and leading-edge flaps, while ailerons respond to roll around their 30° launch reference. There is no uncapped sum of two rotations and no hidden claim of a functioning FLCS.

Evidence is retained under `verification/coaxial-aileron-smoke/`, including `explicit-drive/results.json`. The safe arrangement passed an exact-RC3 native build, independent driver probes, format-51 save, fresh-process reopen and five endpoint/default input combinations. Receipts are under `verification/aileron-safe-coupling-smoke/`.

## Motion studies

The helper returns thirteen named studies. The native builder additionally supplies its general launch-pose and articulation-inspection studies.

| Study | What it demonstrates |
|---|---|
| Cockpit access - slide then hinge | Lock lever, 38.1 mm canopy slide before opening, 68° canopy rotation and boarding ladder; reverse order on closure. |
| Cockpit flight controls - linked surfaces | Pitch, roll and reciprocal pedal travel, linked surfaces/NWS, independent toe brakes. |
| Flap selector - AUTO HALF FULL geometry | Three authored selector positions and their TE/LE geometry; roll input held at zero. |
| Wing fold - cockpit handle | Flaps first move to the authored AUTO geometry, then the handle folds both outer panels and returns. |
| Landing gear - cockpit lever and doors | Doors open by step 8; launch bar reaches its final limit-derived raised position by step 18; gear starts moving at step 20 and reaches stow at step 45; doors close at step 55. On return, doors are open by step 75, gear is down by 95, and the bar returns by 100. |
| Arresting hook - cockpit handle | Handle and hook move together and return. |
| Speedbrake and launch bar | Independent panel and launch-bar travel. |
| Refuelling probe and door | Door opens before probe extension; probe retracts before door closure. |
| Radar service and gimbals | Radome access, then separate azimuth and elevation travel. |
| Avionics trays and removable covers | Independent tray withdrawal and equipment-cover access. |
| F404 independent two-spool rotation | Each engine's N1 and N2 group rotates independently over 240 steps. Ten and fifteen turns are presentation choices; they do not imply RPM. |
| F404 nozzle and variable guide mechanisms | Common nozzle actuator and separate fan/HPC variable-guide drives, including their existing linked followers. |
| Throttle and HOTAS grip travel | Paired throttle movement, trigger and paddle travel. |

Studies contain only independent scalar joints, never duplicate keys for linked followers or passive actuator endpoints. Most return their named controls to defaults. The spool study ends at whole-turn rotations; its joint numbers retain those turns until the launch pose is restored. Start from the saved launch pose when comparing separate demonstrations.

The gear sequence reads the calibrated launch-bar stow pose supplied by the gear refinement: +117.26947198845808°. It does not substitute the slightly larger mechanical travel limit for that pose. Doors and the bar are independently keyed, so they are not given conflicting second drivers. These keyframes are visual sequencing, not a certified aircraft interlock or operating procedure.

## Initialization and validation

Nonzero link offsets feeding a passive hydraulic loop require explicit initialization of the cockpit input, including a zero-valued input. A dedicated RC3 fixture using the actual stabilator actuator showed that link creation alone could leave the input displaced. Explicitly driving the input to zero restored the intended −4° stabilator angle. Input values 0°, +18°, −18°, then 0° produced stabilator values −4°, +14°, −22°, then −4°, each within 1e−7 and without native errors or conflicts. The native builder initializes every independent scalar joint after links are created.

Evidence: `verification/control-actuator-offset-smoke/explicit-zero/results.json`. This determinate actuator loop remains in the model; it is different from the rejected redundant aileron stop loop.

The coupling module checks that targets exist, each follower has one driver, there are no link dependency cycles, defaults are consistent, every complete driver interval fits follower limits, and motion-study keyframes fit source limits. Calling `connect(scene)` again does not add duplicate links. It adds **20 cockpit links**. With the 376 engine links and four refined landing-gear links, the source integration contains **400 links** at this checkpoint. Machine-readable source validation is in `research/control_couplings_validation.json`.

These fixture/source checks do not replace whole-aircraft native verification. No render was generated.
