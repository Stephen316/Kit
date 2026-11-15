# Fusion drawing acceptance record

This page records what is measured for the Fusion drawing codec against the
[CAD success criteria](CadSuccessCriteria.md), and what is not.
It is an attestation, not a completion claim.

Measured on 2026-11-14 and 2026-11-15 with Fusion 2706.1.17 on macOS arm64.

## C1. No donor data

| Check                                          | Result                              |
| ---------------------------------------------- | ----------------------------------- |
| `tools.Donors.CheckReplays src`                | no recorded payloads in 3078 files  |
| CAD files tracked under `src/`                 | 0                                   |
| Vendor binaries tracked anywhere               | 0                                   |
| Data files under `src/`                        | 16 class vocabularies and defaults  |

The 16 data files are class vocabularies and per-class default tables, not captured document rows.

One default was captured rather than derived: `ACDBASSOCINVENTORPERSSUBENTIDMANAGER.ManagerFlag` was
`1` because every Fusion save carries `1`, although Fusion also opens the drawing with `0`.
It is now the schema zero, so the table holds no value that only a save can justify.

## C2. No CAD runtime

The reader, the writer and the author are pure Python. The native runs use Fusion only as the
acceptance oracle, never as part of a conversion.

## C3. Lossless

| Check                                                     | Result     |
| --------------------------------------------------------- | ---------- |
| Fusion-saved DWG read and re-emitted byte-exactly          | 60 of 60   |
| Fusion-saved F2D drawing document re-emitted byte-exactly  | 248 of 248 |
| Fusion-saved DWG header typed into parametric variables    | 60 of 60   |

`ReadDrawing` projects the embedded DWG into the typed model and `EmitDrawing` rebuilds it from that
model, so the counts are a conversion and not a replay. One drawing projects to 1993 typed objects.

| Check                                                              | Result     |
| ------------------------------------------------------------------ | ---------- |
| F2D re-emitted byte-exactly through the typed DWG model             | 187 of 248 |
| F2D refused because the database is a draft or carries Kit's product | 60 |
| F2D refused because the database does not parse                      | 1 |
| Typed `LAYOUT` edit, emitted from the model, opened in Fusion       | 841 by 594 mm, 4.7 s |

The 187 that emit are Fusion saves with 77-bit header tails. The 60 refused are drafts and research
variants: their tail is under 72 bits or their product entry names Kit, and the writer refuses them
rather than emitting a drawing Fusion rejects. The one that does not parse is a research control with
an empty database.

C3 is met for drawings through the DWG model, with the limit that the model is the DWG model and not
a neutral interchange model.

## C4. Fully parametric

The design writer emits a parametric sketch, an extrusion and a BRep body part from a
`DocumentSpec`, and Fusion reports the authored parameter and an exact body volume:

| Case                  | Profile        | Parameter        | Bodies | Volume cm³ (Fusion) | Volume cm³ (spec) |
| --------------------- | -------------- | ---------------- | ------ | ------------------- | ----------------- |
| `KitAuthoredCylinder` | extrusion      | `kitLength` 40 mm | 1     | 19.634954084935366  | 19.634954084936208 |
| `KitAuthoredHeldOut`  | extrusion      | `kitHeldOutLength` 27.5 mm | 1 | 5.5292030703178 | 5.529203070318037 |
| `KitAuthoredCuboid`   | cuboid         | `kitCuboidLength` 20 mm | 1 | 24.0 | 24.0 |
| `KitAuthoredFrustum`  | frustum 10 deg | `kitFrustumLength` 30 mm | 1 | 15.289388972035598 | 15.289388972034654 |

Fusion also reports the authored sketch, feature and material on the frustum case:

```
material   Kit Generic Material
features   adsk::fusion::ExtrudeFeature
sketch     Kit Sketch, 1 curve, 1 profile, 2 points
```

The design side meets C4: a parameter drives the geometry, and Fusion rebuilds the body from it.
Editing `d1` from `20 mm` to `40 mm` doubled two bodies from `24.0` to `48.0` cm³ after
`computeAll()`.

The drawing side does not meet C4. Fusion applies a sheet extent, a view scale and a view position
that Kit writes, each verified with a one-input control, but a drawing has no feature tree and no
driving dimension that rebuilds geometry. Those controls show that Kit writes the fields Fusion
reads; they are not parametric history.

## Parameter reader cross-check

Kit reads the parameter records of a Fusion-saved design and Fusion reports the same expressions:

| File | Kit reads | Fusion reports |
| ---- | --------- | -------------- |
| `mirror_xy.f3d` | `d1` `20 mm`, `d2` `0.0 deg` | `d1` `20 mm`, `d2` `0.0 deg` |
| `analytic.f3d` | `d1` `360 deg`, `d2` `360 deg`, `d3` `360 deg` | the same three |

Kit also reads records Fusion does not list as parameters, such as a pattern count and a mirror stitch
tolerance, so its read is a superset of `Design.allParameters`.

## BRep reader cross-check

Kit reads the BRep journal of a Fusion-saved design and counts its topology entities. Fusion reports
the same totals for the same file:

| File | Kit journal | Fusion | Match |
| ---- | ----------- | ------ | ----- |
| `mirror_xy.f3d` | 12 face, 24 edge, 16 vertex | 2 bodies of 6, 12, 8 | yes |
| `analytic.f3d` | 4 face, 2 edge, 2 vertex | sphere 1/0/0, torus 1/0/0, cone 2/2/2 | yes |
| `shell_both.f3d` | 17 face, 36 edge, 24 vertex | 1 body of 11, 24, 16 | **no** |

The first two agree exactly. The third does not, and the reason is in the journal: `shell_both` carries
3 `DeltaState` records and 266 entities for an `ActiveCount` of 195, so a count over every entity
includes the pre-shell topology as well as the shelled result.

The journal is a history, not a snapshot. A topology count has to be resolved through the state links
before it can be compared with Fusion, and this record does not do that yet.

The journal header reports `FileVersion` 23200, `RootCount` 3, `Scale` 50.0 and tolerances of 1e-6 and
1e-10.

## C5 to C7. Loadable, usable, and measured

| Case                                   | Result                                        |
| -------------------------------------- | --------------------------------------------- |
| Kit-authored design, opened in Fusion  | accepted, parameter and volume exact          |
| Kit-modified drawing, opened in Fusion | accepted, sheet 841 by 594 mm, views `[5,4,4]` |
| Kit-modified drawing, view scale       | accepted, first view scale 4.0 to 2.0         |
| Kit-modified drawing, view position    | accepted, every curve moved exactly 20 mm     |
| Kit-authored drawing from nothing      | **not loadable**                              |

The last row is the failure. A DWG header ends with four shorts that Fusion checks, and they are an
encrypted vendor integrity check. The [Fusion donor ban](../../Research/FusionDonorBan.md) forbids
reproducing a vendor integrity check and forbids tracing the libraries that reveal it, so Kit writes
placeholder values and Fusion refuses the file.

## C8. Honest attestation

The loadable row above is a failure, not a partial pass. The save-and-reopen leg is proven through a local export rather than a cloud save.
`DataFile.isReadOnly` is true on this Personal Use license, and `saveAs` returns `True` and produces
no file for a design (240 s), a drawing (900 s), or a design imported into a new document (300 s), so
the limit is on the account.

Fusion can still export a design to a local F3D with `Design.exportManager`, which is Fusion's own
writer. Kit's authored cylinder was imported, exported to 54756 bytes, and read back by Kit with
`kitLength` `40.0 mm`, `d2` `kitLength`, `d3` `0 deg` and the same
`CylinderBody(Radius=12.5, Height=40.0)`. The parameters and the geometry survive a write by Fusion.

## C9. Complete implementation

Incomplete. The drawing writer cannot produce a loadable DWG from nothing, and the reason is a policy
prohibition rather than a missing rule.

## C10. Generalization

The design acceptance uses a held-out case with inputs the first case did not use.
The drawing controls change one input each, which is what separates a read value from a constant: all
247 Fusion-saved drawings in the corpus are A3 Landscape at 4:1, so the corpus alone cannot show that
the reader tracks the file.

## C11. Traceable knowledge

| Finding                                        | Record                                                    |
| ---------------------------------------------- | --------------------------------------------------------- |
| Header tail is an encrypted integrity check    | [gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingHeaderTail.md) |
| Sheet extent comes from the DWG `LAYOUT`       | [gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingSheetExtent.md) |
| View scale comes from `DRAWINGVIEW` and `SCALE` | [gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingViewScale.md) |
| View position comes from `VIEWPORT.Center`     | [gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingViewPosition.md) |
| Read-only uploads never save                   | [gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionPersonalReadOnlySave.md) |

## Known limits from review

Three limits were raised against this record and are accepted as limits, not fixed:

| Limit | Effect |
| ----- | ------ |
| Opaque class tails | The DWG projection keeps common-only objects with opaque class tails, so the model is typed where Kit knows the class and opaque where it does not. C3 covers the typed portion. Refusing those objects would make the reader unable to open most drawings. |
| Nonparametric drawings | A drawing has no feature tree, so `EmitDrawing` emits a drawing that is not parametric. C4 is not met for drawings, and the writer does not refuse them. Fusion's own saves carry no feature tree either, so refusing would refuse every drawing. |
| Authoring gate | Resolved: `EmitDrawing` refuses a database whose product entry names Kit, so no path emits a drawing Fusion rejects. |

The third limit is resolved. The criteria say a writer that cannot make a field from format knowledge
must refuse the input, and `BuildBundle` now refuses an authored database:

```
ValueError: Authored drawing databases cannot be made loadable, so the drawing is refused
```

C9 is therefore incomplete but honest: Kit refuses rather than emitting a file Fusion rejects.

## What would change the verdict

Either a document-level field that Fusion accepts in place of the integrity check, or an explicit
decision to lift the prohibition on reproducing vendor integrity checks.
An editable document slot would also let the save-and-reopen leg run.
