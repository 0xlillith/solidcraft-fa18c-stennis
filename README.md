# F/A-18C / USS John C. Stennis for SolidCraft

An original detailed visual and kinematic assembly of a Legacy Hornet in a Stennis launch setting, with an articulated cockpit, internal airframe structure, installed equipment, landing gear, and two F404-family engine assemblies.

**Target application: SolidCraft 0.40.0-rc.3.** The released native files use `solidcraft/51` and were created, saved, closed, and reopened with the official RC3 executable. See [compatibility evidence](verification/RC3_COMPATIBILITY.md) and the [final native validation record](verification/FINAL_VALIDATION.json).

## Open the model

Download a native `.sc` file from [release v0.1.0](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/tag/v0.1.0) and open it in SolidCraft 0.40.0-rc.3. The native documents embed their geometry, materials, joints, motion studies, and saved views; Python and the OBJ files are only needed for rebuilding or editing the procedural geometry.

| Native download | Starting inspection state |
| --- | --- |
| [FA18C_Stennis_RC3_Master.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C_Stennis_RC3_Master.sc) | Complete aircraft on USS John C. Stennis, in the launch configuration |
| [FA18C_RC3_Aircraft.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C_RC3_Aircraft.sc) | Aircraft alone, retaining the complete internal assemblies |
| [FA18C_RC3_Cockpit.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C_RC3_Cockpit.sc) | Canopy open and pilot hidden, with the cockpit accessible |
| [FA18C_RC3_Internal_Systems.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C_RC3_Internal_Systems.sc) | Selected skins removed to expose installed systems |
| [FA18C_RC3_Structure.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C_RC3_Structure.sc) | Additional equipment hidden to reveal structural members |
| [F404_RC3_Engines.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/F404_RC3_Engines.sc) | Both engine cores exposed through casing and liner cutaways |

Start with **FA18C_Stennis_RC3_Master.sc** and apply the saved **Launch aircraft** view. Other useful views include **Cockpit overhead**, **Cockpit pilot eye**, **Wing structure**, and **Twin F404 cutaway**. The **Launch pose** motion study restores the launch configuration.

Inspection files retain their hidden aircraft parts. Show those bodies again in the browser to restore the installation context. Aircraft inspection copies omit the carrier; the engine copy retains the hidden aircraft assembly.

### Complete project bundles

- [Complete TAR.XZ bundle](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C-Stennis-RC3-Realism-20261109.tar.xz) — compact download, approximately 43 MB.
- [Complete ZIP bundle](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C-Stennis-RC3-Realism-20261109.zip) — the same project payload in ZIP format.
- [Release asset SHA-256 checksums](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/SHA256SUMS.txt).

Both bundles include all six native scenes, per-component OBJ geometry, the scene manifest, procedural Python source, delivery documentation, compact verification records, and the selected NASA reference PDFs. Manufacturer, simulator, conference, and other link-only references are listed in [REFERENCE_LINKS.md](REFERENCE_LINKS.md).

The Git repository keeps the source, documentation, manifest, and compact metadata. Generated native models, OBJ meshes, PDFs, and archive files are distributed as release assets. This keeps ordinary source checkouts small while preserving the complete model in the release.

For command-line downloads, see [native/README.md](native/README.md).

## Model contents

### Cockpit

The cockpit includes separate DDI, AMPCD, UFC, HUD-control and instrument groups; organized console panels; 60 independently articulated display perimeter buttons; UFC keypad and option controls; toggles, rotary controls, guards and circuit breakers; movable instrument needles; stick, throttle, HOTAS, rudder-pedal and toe-brake controls.

Instrument backs, connector shells and pins, representative circuit boards, and looms are modeled behind the faceplates. The NACES-style seat exterior includes cushions, harnesses, buckles, restraints, hoses, fittings, and height adjustment. The pilot is a separate component with independent visibility.

Selected instrument and panel envelopes use measurements from public OpenHornet replica references. The DCS public guide supplies instrument-identification and layout cross-checks. Replica dimensions and aircraft production dimensions are distinguished in [COCKPIT_REFERENCE.md](COCKPIT_REFERENCE.md).

### Engines

Each F404-family assembly contains three fan stages, seven high-pressure compressor stages, single high- and low-pressure turbine stages, stator rows, disks, hubs, bearing supports, and concentric shafts. The low- and high-pressure spools rotate independently.

The modeled hardware includes annular combustion components, perforated liners, bypass passages, afterburner components, linked variable vanes, primary/divergent nozzle flaps and seals, casing quadrants, accessory housings, pipes, flanges, fasteners, and mounting details. Across both engines there are 280 individually hinged variable vanes.

The GE -402 overall envelope is combined with public F404-family internal references, many of which describe the earlier -400. Blade counts, profiles, detailed internal stations, and demonstration travel remain authored estimates. See [F404 reference and modeling notes](research/F404_REFERENCE_AND_MODELING_NOTES.md).

### Structure, equipment, and landing gear

The airframe has hollow removable skin sections, continuous intake ducts, frames, longerons, center-barrel members, attachment fittings, spars, ribs with lightening holes, stringers, and removable wing skins. Installed equipment includes shaped fuel-cell envelopes, pumps, valves, linework, electrical looms, environmental-control equipment, engine-bay firewalls and mounts, an articulated radar antenna assembly, and sliding avionics trays.

The nose gear retracts forward. The main gear uses compound folding, shortening, and wheel-planing motions. Separate oleos, braces, scissors, brake hardware, wheels, doors, and actuator parts are present. The landing-gear study sequences the doors and launch bar around retraction and extension.

See [LANDING_GEAR.md](LANDING_GEAR.md) and [CONTROL_COUPLINGS.md](CONTROL_COUPLINGS.md) for the mechanisms, input mappings, and limits.

### Carrier and historical setting

The carrier geometry and NG301 marking interpretation were inherited from the first showcase model. The broad setting is VFA-146 / CVW-9 aboard USS John C. Stennis around 2009–2010. Overall ship dimensions follow published Nimitz-class scale anchors; detailed deck offsets, equipment positions, markings, and fittings are visual reconstructions.

The [inherited aircraft/carrier source register](docs/research/INHERITED_AIRCRAFT_CARRIER_REFERENCES.md) and [inherited Stennis notes](docs/research/stennis_references.md) preserve the original historical reference trail. They are historical design notes; current geometry and compatibility claims are governed by this revision's documentation and validation records.

## Articulation and materials

Native motion studies cover cockpit access, stick and pedal movement, flap selection, wing fold, gear sequencing, hook, speedbrake, radar/avionics access, and engine mechanisms. The engine driver names include:

- `Port F404 N1 shaft rotation` and `Port F404 N2 shaft rotation`.
- `Port F404 nozzle actuator travel`.
- `Port F404 fan variable guide control drive`.
- `Port F404 HPC variable guide control drive`.

Replace `Port` with `Starboard` for the other engine. Native revolute values are degrees; native slider values are millimetres. The generator represents linear dimensions in metres and converts them during native construction.

Every body has an available physical material assignment and an authored appearance. Unavailable alloys, elastomers, and composites use documented catalog proxies. [MATERIALS.md](MATERIALS.md) records the actual assignments.

Functional means connected, articulated model mechanisms. Avionics, combustion/thrust, and the real flight-control computer are outside the simulation scope. Automatic aileron/flap mixing is not implemented; the documented bounded RC3 mapping supplies the demonstration motion.

## Verified RC3 release

The native builder verifies the official Linux x86_64 RC3 binary by both its version and SHA-256. The target release is [v0.40.0-rc.3](https://github.com/tangency-labs/solidcraft/releases/tag/v0.40.0-rc.3), commit `7001949c49e211a430fe4747221589b2b9384f2c`.

| Complete master | Recorded result |
| --- | ---: |
| Named components | 914 |
| Material-separated bodies | 3,208 |
| Triangles | 3,151,204 |
| Assembly joints | 931 |
| Articulated joints | 800 |
| Native motion links | 400 |
| Independently driven mechanisms checked | 343 |
| Saved views | 20 |
| Motion studies | 15 |

All 343 independent movement-and-restoration checks passed. All six final native files reopened in fresh official RC3 processes with matching persisted state, including material assignments, joint state, visibility, views, and studies. The native checks reported zero joint conflicts and zero floating assembly chains.

The checks establish compatibility and the tested geometric mechanisms. Internal manufacturing dimensions, exact wire/pipe routes, blade profiles, wall gauges, and some small linkage geometry remain authored estimates. The model is intended for visual inspection, articulation demonstrations, and future showcase work.

The [archive provenance directory](archive-provenance/README.md) retains the original portable-payload index and checksums. Those describe the packaged delivery, rather than subsequent repository documentation edits. The release-level checksum file covers the downloadable asset files themselves.

## Rebuild from source

Geometry generation requires Python 3.10 or later and its standard library. Native construction additionally requires the official **Linux x86_64 SolidCraft 0.40.0-rc.3 CLI**. The supplied builder is pinned to that executable; it does not rewrite a newer native format into an older one.

From the repository root, generate into a separate build directory:

```bash
python3 source/generate.py --out build

SOLIDCRAFT_CLI=/absolute/path/to/official-rc3/solidcraft-cli
python3 source/native_build_rc3.py \
  --cli "$SOLIDCRAFT_CLI" \
  --manifest build/scene_manifest.json \
  --output build/native/FA18C_Stennis_RC3_Master.sc \
  --view "Launch aircraft"
```

Then derive all five inspection documents from the master:

```bash
while IFS='|' read -r variant filename; do
  python3 source/native_build_rc3.py \
    --cli "$SOLIDCRAFT_CLI" \
    --manifest build/scene_manifest.json \
    --input build/native/FA18C_Stennis_RC3_Master.sc \
    --variant "$variant" \
    --output "build/native/$filename"
done <<'VARIANTS'
Aircraft|FA18C_RC3_Aircraft.sc
Cockpit access|FA18C_RC3_Cockpit.sc
Internal systems|FA18C_RC3_Internal_Systems.sc
Airframe structure|FA18C_RC3_Structure.sc
Twin F404 engines|F404_RC3_Engines.sc
VARIANTS
```

The builder saves and reopens each generated native file. Add `--force` to a native-build command when intentionally replacing a generated output from an earlier run. The source coordinate convention is +X aft, +Y starboard, +Z up; generated OBJ coordinates are millimetres.

## References and attribution

Start with [REFERENCES.md](REFERENCES.md) for the current source map and the inherited historical reference trail. [ATTRIBUTIONS.md](ATTRIBUTIONS.md) records project and third-party attribution scope. No open-source or Creative Commons license has been selected for the original project work.

The source-generated meshes, geometric lettering, and display graphics are original to this project. DCS/OpenHornet meshes, CAD paths, textures, screenshots, and artwork are not embedded. Referenced organizations and photographers are credited as sources; the project does not imply their endorsement.
