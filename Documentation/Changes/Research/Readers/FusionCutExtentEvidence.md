# Fusion P04 cut extent evidence

The A05c archive study compares the eleven P04 Fusion discovery exports from build `2706.1.17`. The evidence command reads the exact committed archive bytes from `89c25945f5833ad9c3a1c6c683df510b5702dd54`. It verifies the discovery recipe, capture receipt, measurement digest and full variant roster through the paired intake. Fusion, P02 qualification files and P05 holdout files are outside the archive scan.

Run the command from the repository with Python 3.14 or later for ZIP Zstandard support. It emits the source pins, active Design stream digests, MetaStream-indexed record bounds, extrusion controls and parameter binding sites as JSON.

```powershell
python -B re/automation/FusionCutExtentEvidence.py > FusionCutExtentEvidence.json
```

The application-side authoring code uses `DistanceExtentDefinition` for the blind cuts and `ThroughAllExtentDefinition` with explicit negative extent direction for the through-all variant. This records the authored intent independently of the saved Design stream. [P04 capture generator](../../../../re/automation/PairedCaptures/FusionCapture.py), [Autodesk through-all API example](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/extrudeFeaturesThroughAllExtent_add_Sample.htm)

All eleven archives contain one Cut with stored operation code `2` and a companion New Body with operation code `4`. Both features store mode `1` and have the second extent disabled. The companion boss remains a distance extrusion. Only the authored boss-depth edit changes its distance, from 10 mm to 12 mm.

| Cut variants | Count | Primary end code | Stored vector | Bound along distance |
| --- | ---: | ---: | --- | --- |
| Both baselines, other size edits, inch display | 8 | `1` | `[0, 0, 1]` | `-0.4 cm` |
| Cut-depth edit | 1 | `1` | `[0, 0, 1]` | `-0.5 cm` |
| YZ basis | 1 | `1` | `[1, 0, 0]` | `-0.4 cm` |
| Through-all | 1 | `4` | `[0, 0, -1]` | Absent |

The blind cuts have a reciprocal `AlongDistance` binding to `cut_depth_mm`. The 4 mm value has little-endian float64 bytes `9a9999999999d9bf`. The independently authored 5 mm variant changes the value bytes to `000000000000e0bf` and the expression to `-( 5 mm )`. The inch-display export retains the 4 mm parameter value and expression. [Autodesk database units](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Units_UM.htm)

The through-all cut has an empty along reference and no owned `AlongDistance` parameter. It retains first-side flags `2` and a reference to object `461`, with primary class `2CA5A1CD-C99B-4C9B-91AF-57989148E841`. Those fields remain unresolved. Object `461` resolves to the depth parameter in the blind baselines, so the ID alone cannot establish its role across exports. [Fusion cut extent controls](../../../Gotchas/Research/FusionCutExtentControls.md)

The capture receipt SHA-256 is `8f0c62e6e12cca0b41e91009f929e5d8d823b8977d6344856e6c56a630e05080`. The through-all archive SHA-256 is `5aacebd98ea8fa101d070572091fbd1b2270b496c2facc7e9125049082b2506f`. Its generator measurements and saved records establish this archive-level contrast. Fresh-process native readback, supporting-face identity, body scope, sketch constraints and editable native acceptance remain open for A05c.

The command ran on Python 3.14.6 against all eleven pinned archives. The production Fusion reader and writer are outside the study.
