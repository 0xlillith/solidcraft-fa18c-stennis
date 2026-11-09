> Reference availability: the Git repository keeps source links and notes. Only the four NASA PDFs listed in [REFERENCE_LINKS.md](../REFERENCE_LINKS.md) are included in the complete release bundles. Manufacturer, simulator, conference and externally authored NASA-hosted works remain link-only.

# Primary-source index

Access/checkpoint date: **2026-11-09**. This is the compact source map for the RC3 reconstruction. Detailed cockpit measurements and their provenance are in [COCKPIT_REFERENCE.md](../COCKPIT_REFERENCE.md); engine-specific reasoning and caveats are in [F404_REFERENCE_AND_MODELING_NOTES.md](F404_REFERENCE_AND_MODELING_NOTES.md). The first showcase model's [inherited aircraft/carrier/livery register](../docs/research/INHERITED_AIRCRAFT_CARRIER_REFERENCES.md) and [Stennis research notes](../docs/research/stennis_references.md) are retained as historical source records. They add documentation and attribution only, with no geometry change.

The scene contains original procedural geometry. References establish selected dimensions, identities, broad arrangements and visible construction; they do not certify the authored internal station positions, blade profiles, routing, clearances, physical material grades, joint limits or demonstration linkage ratios. No DCS or OpenHornet mesh, texture, SVG path or electrical design is imported.

## Airframe structure and fuel-system context

| Source | Published | Model use / distinction |
|---|---|---|
| [NAVAIR — FRCSE repairs broken wings of a Hornet](https://www.navair.navy.mil/node/10056) | 2009-09-18 | Describes aluminum inner-wing spars and metal ribs beneath composite covering. Supports construction categories; exact spar/rib stations and section geometry remain authored. |
| [NAVAIR — FRCSW Center Barrel Program: The Lifeline of Legacy Hornets](https://www.navair.navy.mil/node/24741) | 2017-03-09 | Identifies the Legacy Hornet center barrel as the wing/main-gear attachment region and discusses dorsal decks and longerons. The article also discusses Super Hornet repairs; those variant-specific manufacturing breaks are not assumed to describe a Legacy Hornet. |
| [NAVAIR — FRCSW Fuel Cell Shop Fuels Readiness](https://www.navair.navy.mil/node/23811) | 2016-06-09 | Supports four main fuel cells plus vent-tank context, wing fuel spaces and rubber Legacy-Hornet bladders. It does not supply exact cell shapes, capacities, internal station coordinates or plumbing diagrams. |
| [S. P. Garbo / McDonnell Aircraft — Design and analysis of composite structures with stress concentrations, NASA record 19830025689](https://ntrs.nasa.gov/citations/19830025689) | 1983-08-01 | PDF page 4, printed p.98, shows an F/A-18A wing-structure plan and describes composite skins attached to aluminum spar/rib substructure. Used as Legacy-family structural arrangement context, not an exact F/A-18C structural blueprint. [Source URL — link only](https://ntrs.nasa.gov/api/citations/19830025689/downloads/19830025689.pdf). |
| [NASA — F/A-18 aircraft fact sheet](https://www.nasa.gov/wp-content/uploads/2021/09/fs-006-afrc_0.pdf) | Date printed in source | Aircraft-family exterior scale and three-view context. Included in the complete release bundles as `research/primary/nasa-fa18-reference.pdf`. |

## Cockpit and seat

| Source | Version/date | Model use / distinction |
|---|---|---|
| [Eagle Dynamics — DCS F/A-18C public guide](https://www.digitalcombatsimulator.ru/upload/iblock/ea9/lxf69u2uk1fhqq7ndb55z9egzabe8hdg/DCS%20FA-18C%20Early%20Access%20Guide%20EN.pdf) | Existing downloaded edition; SHA-256 recorded | Cockpit component identification, panel arrangement, control families, UFC selectors and DDI button numbering. [Source URL — link only](https://www.digitalcombatsimulator.ru/upload/iblock/ea9/lxf69u2uk1fhqq7ndb55z9egzabe8hdg/DCS%20FA-18C%20Early%20Access%20Guide%20EN.pdf). Reference only; no extracted simulator assets. |
| [OpenHornet public repository](https://github.com/jrsteensen/OpenHornet/tree/77c7b2c07240d9d6062c16ed6e533bf2ed8bfce6) and [hardware documentation](https://docs.openhornet.com/hardware/) | Commit 77c7b2c07240d9d6062c16ed6e533bf2ed8bfce6 | Explicit SVG page dimensions and 3MF outer bounds inform DDI, AMPCD, UFC and console envelopes. This is a home-cockpit replica reference. Source is CC BY-NC-SA 4.0; its geometry/artwork is not copied or bundled. Exact measured paths and envelopes are recorded in COCKPIT_REFERENCE.md. |
| [Martin-Baker — Mk14 NACES](https://martin-baker.com/ejection-seats/mk14-naces/) and [manufacturer data sheet](https://martin-baker.com/wp-content/uploads/2023/11/NACES-2025-Data-Sheet-2.pdf) | Data-sheet filename: 2025 | External seat shell, headbox, cushion, harness and fitting appearance. [Source URL — link only](https://martin-baker.com/wp-content/uploads/2023/11/NACES-2025-Data-Sheet-2.pdf). Current product imagery is not a guarantee of a particular historical aircraft fit. |

## F404 engine family

The -402 identity and overall dimensional envelope come from GE's model-specific data sheet. Detailed public internal descriptions are largely from the earlier -400 family. The scene preserves that distinction; authored blade counts, profiles, internal station positions and mechanism travel are not described as production data.

| Source | Published | Model use / local reference |
|---|---|---|
| [GE Aerospace — F404 Family datasheet](https://www.geaerospace.com/sites/default/files/2022-01/F404%20Family%20Data%20Sheet_UPDATED.pdf) | ©2020 | F404-GE-402 application and overall size group. [Source URL — link only](https://www.geaerospace.com/sites/default/files/2022-01/F404%20Family%20Data%20Sheet_UPDATED.pdf). |
| [Walton and Burcham / NASA TM 88273 — Exhaust-Gas Pressure and Temperature Survey of F404-GE-400 Turbofan Engine](https://ntrs.nasa.gov/api/citations/19880010923/downloads/19880010923.pdf) | 1986-12 | Family stages, variable geometry, augmentor/nozzle arrangement; -400 applicability. Included in the complete release bundles as `research/primary/nasa-tm88273-f404-survey.pdf`. |
| [Conners / NASA TM 4140 — Measurement Effects on the Calculation of In-Flight Thrust for an F404 Turbofan Engine](https://ntrs.nasa.gov/api/citations/19900002425/downloads/19900002425.pdf) | 1989 | Family shaft/stage nomenclature. Included in the complete release bundles as `research/primary/nasa-tm4140-f404-measurement.pdf`. |
| [GAO PSAD-80-72 — Are Management Problems in the Acquisition of Aircraft Gas Turbine Engines Being Corrected?](https://www.gao.gov/assets/psad-80-72.pdf) | 1980-09-30 | Labeled public F404 component diagram, PDF p.53; retained as a URL reference. |
| [McDanels, Serafini and DiCarlo / NASA TM 87132 — Polymer, Metal, and Ceramic Matrix Composites for Advanced Aircraft Engine Applications](https://ntrs.nasa.gov/api/citations/19860003939/downloads/19860003939.pdf) | 1985 | Production titanium fan-blade context distinguished from experimental composite specimens. Included in the complete release bundles as `research/primary/nasa-tm87132-materials.pdf`. |
| [Stotler and Yokel / GE, NASA CR-182228 — PMR Graphite Engine Duct Development](https://ntrs.nasa.gov/citations/19900000721) | 1989 | Experimental composite duct compared with production titanium arrangement. Large report retained by URL; not assumed to establish a production composite outer duct. |
| [Riemer and Powel / GE — F404 New Standards for Fighter Aircraft Engines, ICAS-84-5.4.2](https://www.icas.org/icas_archive/ICAS1984/ICAS-84-5.4.2.pdf) | 1984 | GE-authored layout/cutaway context and support-frame discussion. Its older overall-length figure is not mixed into the later -402 datasheet dimension. [Source URL — link only](https://www.icas.org/icas_archive/ICAS1984/ICAS-84-5.4.2.pdf). |
| [Bridges, Wernet and Frate / NASA — PIV Measurements of Chevrons on F400-Series Tactical Aircraft Nozzle Model](https://ntrs.nasa.gov/api/citations/20110008608/downloads/20110008608.pdf) | 2011 | Additional model-family nozzle-sector context. Experimental chevrons are not copied into the historic Hornet nozzle; URL reference. |
| [GE Aerospace / Cole Massie — GE's Most Versatile Fighter Engine Is Ready for the Next Generation of U.S. Air Force Pilots](https://www.geaerospace.com/news/articles/people-product/ges-most-versatile-fighter-engine-ready-next-generation-us-air-force-pilots) | 2020-10-07 | Manufacturer-published visual cutaway reference; no image embedded and no internal dimensions derived from image scaling. |
| [GE Aerospace — F404 product page](https://www.geaerospace.com/military-defense/engines/f404) | Accessed 2026-11-09 | General manufacturer cross-check. Correct engine identity follows the datasheet; see engine note regarding a naming error in a current application carousel. |

## Saved source handling

The portable reference inventory is recorded in [PRIMARY_SOURCE_DOWNLOADS.json](PRIMARY_SOURCE_DOWNLOADS.json). Only the selected NASA PDFs are included as complete documents in the release bundles. Other works remain source links. The Git checkout retains the source metadata and does not include reference PDFs.

The large experimental duct report and additional web references remain URL references. No broad web scrape, simulator assets, cockpit replica CAD archive or private technical manual is included. Original source notices and copyright statements remain with each downloaded document. Research-file availability does not grant rights in third-party photographs, diagrams or trademarks; the scene's own geometry, labels and symbology are independently authored.
