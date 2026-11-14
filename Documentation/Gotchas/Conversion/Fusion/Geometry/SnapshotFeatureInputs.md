# The snapshot member of a feature archive is not the final body

## Expectation

An archive with one `.smbh` history and one `.smb` snapshot stores the final body twice. The snapshot equals the current state of the history.

## Actual behavior

In the four fillet archives below, the `.smb` snapshot holds the bodies before the fillet and planar sheet bodies. Fusion 2706.1.17 imported these byte-exact snapshots with these results.

| Archive | Final body in the design | Bodies in the snapshot |
| --- | --- | --- |
| `fillet_chord.f3d` | 7 faces, 51.80932 cm², 1 NURBS face | 6-face box of 52.0 cm² and 24.0 cm³, two sheets |
| `fillet_curvature.f3d` | 7 faces, 51.729132 cm², 1 NURBS face | 6-face box of 52.0 cm² and 24.0 cm³, two sheets |
| `rule_asymmetric.f3d` | 31 faces, 96.59657 cm², 20 NURBS faces | Two boxes of 24.0 cm² and 82.0 cm², four sheets |
| `one_quarter.f3d`, variable fillet | 7 faces, 51.670676 cm², 1 NURBS face | 6-face box of 52.0 cm² and 24.0 cm³, two sheets |
| `solid_aligned.f3d`, solid sweep | 15 faces, 220.613782 cm², 3 NURBS faces | Eight bodies, including a 9-face sweep body of 8.613782 cm² and a 6-face body of 212.0 cm² |

The four fillet snapshots contain no complex records. The loft and rail sweep snapshots contain the final body and extra planar sheets.

`EmitStateSmb` writes the current state of a history. For all 62 corpus history archives with complex records, those bytes differ from the archive snapshot. The stamps are equal in all 62. The header differs only in the root count, in 55 archives.

Each snapshot body was compared with every body of every retained history state. The comparison clears entity tags and removes body attributes, as the [history identity gotcha](SnapshotHistoryIdentity.md) describes. The archives fall into these classes.

| Snapshot content | Archives |
| --- | --- |
| Every current-state body, plus sheets outside the history | 35 |
| Every current-state body and nothing else | 4 |
| Current-state bodies without one current sheet, plus sheets outside the history | 2 |
| Bodies of one earlier state, plus sheets outside the history | 9 |
| Bodies of one earlier state, plus sheets and solids outside the history | 7 |
| Bodies of one earlier state, a second copy of one of them, plus sheets and solids outside the history | 4 |
| Bodies of one earlier state and nothing else | 1 |

In the 21 earlier-state archives, the snapshot state precedes the current state by these steps.

| Current state minus snapshot state | Archives |
| --- | --- |
| 1 | 15 |
| 2 | 4 |
| 10 | 2 |

The 317 snapshot bodies include 226 bodies that match no body of any retained state.

| Body outside the history | Count |
| --- | --- |
| One-face sheet with `SketchAttrib` records | 206 |
| Two-face sheet with `SketchAttrib` records | 9 |
| Six-face solid with `SketchAttrib` records | 7 |
| Solid of 22, 9 or 8 faces in a solid sweep archive | 4 |

Every face surface of the 11 solids outside the history equals a surface record of the current state. This includes all 33 spline surfaces of these solids. Of the 215 sheets outside the history, 141 have only surfaces that equal a current-state surface.

## Workaround

Do not use the `.smb` snapshot as the final body of a feature archive. Read the `.smbh` history and use `EmitStateSmb` for the current state. Do not use a snapshot import to test a fillet surface codec, because the snapshot has no fillet surface.

A snapshot that holds only history bodies can be written with `EmitStateSmb(Model, StateId, Snapshot=True)`. Pass the state whose bodies the snapshot holds. A history cannot reproduce sheets or solids that are outside it.

## Evidence

- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/NativeAcceptance.json), section `geometry`
- [State and snapshot comparison](../../../../../re/Fusion/Reconstruction/ComplexGeometry/CompareStates.json), fields `differenceClass`, `statesHoldingAllHistoryBodies` and `surfacesInCurrentState`
- [State comparison](../../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyStates.json)
- [Snapshot record order](SnapshotRecordOrder.md)
- [Native coverage](../../../../../re/Fusion/Reconstruction/ComplexGeometry/NativeCoverage.json)
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
