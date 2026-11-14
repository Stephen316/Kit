# Drawing files carry private paths and cloud identities

A captured F2D is not safe to commit without normalization.
Private values occur in two members.

| Member                               | Private values                                                    |
| ------------------------------------ | ----------------------------------------------------------------- |
| Root `Manifest.dat`                  | Absolute cache paths of the drawing, the design and its XRef copy |
| Root `Manifest.dat`                  | Design version URN, lineage URNs and the per-account cache folder |
| Root `Manifest.dat` save label       | Drawing lineage URN after a cloud save                            |
| Embedded DWG, `AcDb:AcDbObjects`     | Account display name and login path                               |
| Embedded DWG, `AcDb:SummaryInfo`     | `LastSavedBy` user name                                           |

The entity segments, sheet manifest, settings and images held no such value in the three Kit controls.
The DWG object data is compressed, so a plain byte search does not find these strings.
The [DWG inventory](../../../../../re/Fusion/Reconstruction/Drawings/Dwg/InspectDwg.py) decompresses every section before it scans.

The historical installed example has the same layout.
Its manifest paths name a Windows profile, and its DWG names two Windows profiles.
Do not copy that example into the repository.

`BuildFixtures.py` replaces the manifest paths and URNs with fixed placeholders.
It also removes the DWG member, because Kit has no DWG writer that can redact it.
The fixtures are therefore codec fixtures, not files that Fusion opens unchanged.
Fusion cannot open a drawing without its DWG, as the [missing DWG gotcha](FusionDrawingMissingDatabase.md) records.
