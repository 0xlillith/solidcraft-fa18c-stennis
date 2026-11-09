# Native SolidCraft model downloads

The six validated native documents are distributed with [release v0.1.0](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/tag/v0.1.0). Open them in **SolidCraft 0.40.0-rc.3**. Each document embeds its own geometry, materials, articulation, saved views, and studies.

| Native download | Starting inspection state |
| --- | --- |
| [FA18C_Stennis_RC3_Master.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C_Stennis_RC3_Master.sc) | Complete aircraft on USS John C. Stennis, in the launch configuration |
| [FA18C_RC3_Aircraft.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C_RC3_Aircraft.sc) | Aircraft alone, retaining the complete internal assemblies |
| [FA18C_RC3_Cockpit.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C_RC3_Cockpit.sc) | Canopy open and pilot hidden, with the cockpit accessible |
| [FA18C_RC3_Internal_Systems.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C_RC3_Internal_Systems.sc) | Selected skins removed to expose installed systems |
| [FA18C_RC3_Structure.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C_RC3_Structure.sc) | Additional equipment hidden to reveal structural members |
| [F404_RC3_Engines.sc](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/F404_RC3_Engines.sc) | Both engine cores exposed through casing and liner cutaways |

## Download through GitHub CLI

Run these commands from the repository root, using a GitHub account with access to this repository:

```bash
gh release download v0.1.0 \
  --repo 0xlillith/solidcraft-fa18c-stennis \
  --pattern '*.sc' \
  --dir native
```

For the complete project, including OBJ geometry and the reference-document selection:

```bash
gh release download v0.1.0 \
  --repo 0xlillith/solidcraft-fa18c-stennis \
  --pattern 'FA18C-Stennis-RC3-Realism-20261109.tar.xz' \
  --dir downloads
```

The [ZIP bundle](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/FA18C-Stennis-RC3-Realism-20261109.zip) is also available. Download [SHA256SUMS.txt](https://github.com/0xlillith/solidcraft-fa18c-stennis/releases/download/v0.1.0/SHA256SUMS.txt) to check the release assets.

For a quick native-file integrity check after downloading the six scenes into `native/`:

```bash
gh release download v0.1.0 \
  --repo 0xlillith/solidcraft-fa18c-stennis \
  --pattern SHA256SUMS.txt \
  --dir native

(cd native && sha256sum --check --ignore-missing SHA256SUMS.txt)
```

## Inspect the model

The master starts in the launch configuration on Stennis. Apply its saved **Launch aircraft** view for an aircraft-focused position. **Cockpit overhead** and **Twin F404 cutaway** are useful close inspection views. The **Launch pose** motion study restores the launch configuration.

Hidden bodies in the inspection files are retained, so their visibility can be restored. The aircraft inspection documents omit the carrier. The engine document retains the hidden aircraft assembly.

See the [main README](../README.md) for rebuild commands, the [compatibility evidence](../verification/RC3_COMPATIBILITY.md), and the [final validation record](../verification/FINAL_VALIDATION.json). The native files are generated outputs and are intentionally excluded from Git history.
