# Authored design acceptance in local Fusion

## Problem

Kit's design writer turns a `DocumentSpec` into an F3D with a parametric sketch, an extrusion and a
BRep body part. Nothing recorded whether Fusion loads that output, so an authored design was only
known to read back through Kit's own reader.

That is not acceptance. A reader agreeing with a writer proves the two agree, not that the format is
right.

## Change

The design writer now has a native acceptance harness under
[`re/Fusion/Reconstruction/Drawings/Native`](../../../../../re/Fusion/Reconstruction/Drawings/Native):

| Script          | Role                                                              |
| --------------- | ----------------------------------------------------------------- |
| `BuildDesign.py` | `EmitDocument` from a `DocumentSpec`, read it back, write a plan  |
| `OpenDesign.py`  | upload the F3D, open it in Fusion, report the parameter and body  |
| `OpenDesignEdit.py` | open it, change the parameter, save, reopen and read it back   |
| `ProbeState.py`  | report the Fusion version, offline flag, hub and project names    |

Both scripts run through `RunGuarded.mjs` and write a JSON report next to the plan.
The script refuses to accept unless Fusion reports one body and a volume that matches the spec, so a
mis-scaled extrusion or a dropped parameter fails the run instead of passing quietly.

## Recorded verification

Two documents, built and opened on 2026-11-14 in Fusion 2706.1.17:

| Case                    | Radius | Length | F3D bytes | Bodies | Volume cm³ (Fusion) | Volume cm³ (spec) | Error     |
| ----------------------- | ------ | ------ | --------- | ------ | ------------------- | ----------------- | --------- |
| `KitAuthoredCylinder`   | 12.5   | 40.0   | 84187     | 1      | 19.634954084935366  | 19.634954084936208 | 8.4e-13 |
| `KitAuthoredHeldOut`    | 8.0    | 27.5   | 84225     | 1      | 5.5292030703178     | 5.529203070318037  | 2.4e-13 |

Both opened with the authored parameter present and the authored names intact:

```
KitAuthoredCylinder  parameter kitLength        = "40.0 mm"  (4.0 cm)
                     bodies 1, features 1, sketches 1
KitAuthoredHeldOut   parameter kitHeldOutLength = "27.5 mm"  (2.75 cm)
                     bodies 1, features 1, sketches 1
```

The second case uses inputs the first did not, so the numbers come from the written BRep and not from
a fitted control.

The edit leg applied in Fusion as well:

```
edit requested 55.0 mm -> parameter.expression "55.0 mm"
saveAs returned True
new file after 240 seconds: none
```

That stall is the documented Personal Use edit limit, not a Kit result.
`DataFile.isReadOnly` was `True` for the upload, and the
[read-only save gotcha](../../../../Gotchas/Conversion/Fusion/Drawing/FusionPersonalReadOnlySave.md)
records the same behaviour for designs and drawings.

## Limits

The harness uploads to the cloud project, so it needs an online hub and a free editable document.
On a Personal Use license at the edit limit, opening still works and editing still applies, but the
save produces no version.

Uploaded files are read-only, so this harness verifies the open and the edit, not a Kit-written save.
A save-and-reopen that exercises Kit's bytes needs an editable file, which the current license does
not provide.
