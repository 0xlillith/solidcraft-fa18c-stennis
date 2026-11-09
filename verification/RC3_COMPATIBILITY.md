# SolidCraft 0.40 RC3 compatibility proof

## Exact release and installed application

The target is the official prerelease tag **v0.40.0-rc.3**, published on 2026-11-07, commit **7001949c49e211a430fe4747221589b2b9384f2c**.

Primary release record:
https://github.com/tangency-labs/solidcraft/releases/tag/v0.40.0-rc.3

Official Linux x86_64 archive:
https://github.com/tangency-labs/solidcraft/releases/download/v0.40.0-rc.3/solidcraft-0.40.0-rc.3-linux-x86_64.tar.gz

| Artifact | SHA256 |
|---|---|
| Official tar.gz, 140,372,551 bytes | 75bafe8b13ae9b120ccc5487ba9f0745b942b4f794d2c4c87cd6c1151089a32b |
| Extracted official solidcraft-cli | 3f29f4cc262601f9b2e029745a9b56de6f959e14bec74003693d36be12c9f45a |
| Official installed AppImage | 67e8dea40b807217d6d6a88ff1f2b6433cdfbf4b475ee25195d3612d886b5f5b |

The installed /home/selune/Applications/solidcraft-0.40.0-rc.3-linux-x86_64.AppImage matched that official AppImage hash exactly. Its desktop launcher points to that file. No application window was opened, replaced or modified.

The official archive was downloaded and verified before extraction into this project's runtime/official-rc3 directory. The extracted CLI reports solidcraft-cli 0.40.0-rc.3. The builder checks its **binary hash as well as its version string**, because later development builds can retain the RC3 Cargo version label.

## Native format and successful executable tests

Official RC3 writes **solidcraft/51** inside **solidcraft-container/1**. No manual JSON downgrade, format-number alteration, application patch or new compilation is used.

The capability fixture and complete builder fixture were created through public commands, saved uncached, closed, and reopened with the same official executable. The builder starts a fresh separate process for the final read-only reopen. Both the full fixture and its derived inspection copy passed:

- Original OBJ mesh import and globally unique body names.
- Physical material assignment; opaque scalar PBR appearances; translucent appearance.
- Grounded components and native revolute/slider joints.
- Native motion links, including slider millimetres driving revolute degrees.
- A genuine passive telescoping closed loop.
- Native named views and keyed motion studies.
- Stored body hides and joint/origin glyph hides.
- Carrier component deletion from an aircraft inspection copy.
- Public read-only source open and Save As to a distinct output.
- Native solidcraft/51 header; no newer-file warning or evaluation error on reopen.
- Persisted geometry membership, poses, links, limits, studies, named views, visibility and metadata matching after reopen.
- Zero joint conflicts and zero floating assembly chains.

The public Save As command names a read-only-derived copy after its output filename. The builder records that expected title change and still compares every component body, joint pose, link, study and hide state.

## Actual closed-loop result

Fixture geometry: driven arm hinge H=(0,0,0)mm, fixed barrel pin A=(0,0,-100)mm, initial rod pin B=(100,0,0)mm. All hinges turn around Y. The barrel-to-rod slider points along initial A→B. Three follower joints are passive; the arm hinge is driven.

At arm **25 degrees**, official RC3 solved:

| Native joint | Solved value |
|---|---:|
| Barrel fixed pivot | 12.5 degrees |
| Telescoping travel | -33.9614345679 mm |
| Rod moving pivot | -12.5 degrees |

Both sides of the moving-pin joint resolve to (90.6307787037, 0, -42.2618261741)mm. There were no conflicts, floating chains, contact stops or loop stops. This loop and its pose survived native save and fresh-process reopen.

The separate motion-link fixture used b=1.5a: ring travel25mm produced petal37.5degrees, also retained on reopen.

## Builder invocation

Use the new standalone source/native_build_rc3.py. It never starts a render or writes rendering presets.

Official CLI relative to the project root:

runtime/official-rc3/solidcraft-0.40.0-rc.3-linux-x86_64/bin/solidcraft-cli

Build:

~~~bash
python3 source/native_build_rc3.py \
  --cli runtime/official-rc3/solidcraft-0.40.0-rc.3-linux-x86_64/bin/solidcraft-cli \
  --manifest scene_manifest.json \
  --output native/FA18C_Stennis_RC3_Master.sc
~~~

Derive a native inspection variant from its read-only master:

~~~bash
python3 source/native_build_rc3.py \
  --cli runtime/official-rc3/solidcraft-0.40.0-rc.3-linux-x86_64/bin/solidcraft-cli \
  --manifest scene_manifest.json \
  --input native/FA18C_Stennis_RC3_Master.sc \
  --variant "Twin F404 engines" \
  --output native/F404_RC3_Engines.sc
~~~

Resources default to two CPU threads, nice10, an isolated recovery directory and no GPU. Existing unrelated SolidCraft processes and GUI state are not reused.

## Manifest additions

motion_links:
~~~json
[
  {"a":"Nozzle actuator travel","b":"Nozzle petal 01","ratio":0.25,"offset":0}
]
~~~

Ratios and offsets use native **degrees and millimetres**. Geometry, joint origins, camera positions/distances and slider defaults/limits/pose values otherwise use the existing authored metre convention. Revolutes use degrees; camera yaw/pitch/fov use radians.

A closed-loop follower declares passive:true on its joint entry. Each independent driver is tested and restored. Linked followers are automatically excluded from direct drive/probe and keyframe creation, and their native relationship is checked while the driver moves.

inspection_variants can be a list of entries or a mapping keyed by name:

~~~json
{
  "name":"Engine inspection",
  "subset":"aircraft",
  "hide_components":["Airframe"],
  "hide_component_patterns":["Pilot*"],
  "hide_bodies":[],
  "hide_body_patterns":["Airframe__Skin*"],
  "pose":{"Canopy unlatch slide":0.0381,"Canopy open":68},
  "view":"Engine detail"
}
~~~

Pattern matching uses case-sensitive fnmatch. Unmatched patterns fail clearly. Pose dictionary order is preserved, so unlatch translation can precede canopy rotation. Hidden body names and every driven pose are enumerated in the receipt.

## RC3-specific limits relevant to this model

The exact RC3 OBJ importer ignores OBJ texture coordinates, authored normals and OBJ materials. It imports indexed positions/triangles and computes normals. Correct winding, shared smooth-surface vertices and duplicated hard-edge boundary vertices therefore matter; imported vn lines are not a compatibility guarantee.

Available built-in physical materials are: Default, Steel, Stainless Steel, Aluminum, Brass, Copper, Titanium, Cast Iron, ABS Plastic, PLA, Nylon, Polycarbonate, Oak and Glass. Nickel/Inconel are not built-ins. A documented Stainless Steel proxy is used where the catalog has no matching hot-section alloy; appearance does not imply certified alloy properties.

view.save persists named cameras. view.apply changes only the current viewport state, so the saved named view should be selected after opening when the desired inspection composition is needed. The variant's body visibility and articulation are persisted.

Primary command source at the exact release:
https://github.com/tangency-labs/solidcraft/blob/v0.40.0-rc.3/crates/engine/src/cmd/joints.rs
https://github.com/tangency-labs/solidcraft/blob/v0.40.0-rc.3/crates/engine/src/cmd/browser.rs
https://github.com/tangency-labs/solidcraft/blob/v0.40.0-rc.3/crates/io/src/obj.rs

## Evidence files

- verification/official-release-proof.json
- verification/rc3-capability-receipt.json
- verification/rc3-builder-smoke/fixture-receipts/build-receipt.json
- verification/rc3-builder-smoke/fixture-inspection-receipts/build-receipt.json
- Fresh-reopen subdirectories beside those receipts contain reopened native state.
- Every production native file receives its own output-stem-receipts directory with release proof, source hash, command journal, native state, joint probes and fresh-process reopen result.

These tests establish the builder's compatibility and mechanism support. Production-model body/joint counts and geometric checks come from its own build receipt after the detailed geometry is generated.
