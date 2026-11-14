# Converted Form records follow a breadth-first walk

## Expectation

A converted Form body lists its records face by face. Each face spline record defines its `t_spl_sur` inline, and the pcurves refer to it.

## Actual behavior

Fusion writes the records of a converted Form body in breadth-first order. The walk starts at the body record and follows each record reference in field order. The `.smbh` history and the `.smb` snapshot use the same rule.

The first record in stream order that carries a face surface defines that `t_spl_sur` inline. This record can be a pcurve of a neighbor face, not the face spline record. Later records refer to the definition. Only the first inline `t_spl_sur` carries the inline `t_spl_subtrans_object`.

The native box history shows this placement. The `t_spl_sur` face index is the patch program index of the face.

| `t_spl_sur` face index | Inline definition record | Record type |
| --- | --- | --- |
| 5 | 10 | `SplineNode`, with the inline patch program |
| 4 | 14 | `SplineNode` |
| 3 | 19 | `SplineNode` |
| 2 | 29 | `SplineNode` |
| 1 | 46 | `PcurveNode` |
| 0 | 71 | `PcurveNode` |

The shell face chain lists the faces in reverse patch program order. The box chain starts at patch program 5 and ends at patch program 0.

`CreateFormBrep` reproduces the native records of nine local archives with this rule. The only difference is the body tag of the four plane primitives that the API made.

| Archive | History records | Snapshot records | History | Snapshot |
| --- | --- | --- | --- | --- |
| `Plane1x1`, `Plane3x2`, `Plane4x4`, `Plane2x5` | 38 | 36 | Equal except body tag 9 | Equal |
| `TSpline/Plane` | 38 | 36 | Equal | Equal |
| `Box`, `SymmetricBox` | 118 | 116 | Equal | Equal |
| `vendor_BoxCreasedControl` | 123 | 121 | Equal | Equal |
| `vendor_PlaneCreasedControl` | 62 | 60 | Equal | Equal |

The comparison sets entity tags to -1 on both sides, except the body tag. The source-free builder writes body tag 0, as the interactive archives do.

## Workaround

Build the records in any order. Then put them in breadth-first order with `OrderFormNodes`. It places each inline surface definition at its first carrier and writes later uses as `SubtypeRef("surface", N)`. Do not put the inline surface on the face spline record when an earlier pcurve uses that surface.

## Evidence

- [BRep rebuild comparison](../../../../../re/Fusion/Reconstruction/FormDocuments/Sourceless/BrepRebuild.json)
- [Rebuild script](../../../../../re/Fusion/Reconstruction/FormDocuments/Sourceless/CompareBrep.py)
- [Spline subtype table](SplineSubtypeTable.md)
