# Spline subtype references index one table per stream

## Expectation

A `ref N` scope in a converted Form body looks like a reference to entity `N`. It could also look like the `N`th earlier definition of the same subtype name.

## Actual behavior

`N` indexes one subtype table for the complete SAB stream. Each inline definition of `t_spl_sur`, `t_spl_subtrans_object`, `exact_int_cur` or `exp_par_cur` adds one table entry in stream order. A `ref` scope adds no entry. The target entry is always earlier in the stream and always has the subtype name that the referencing slot expects.

The same rule applies in the `.smb` snapshot and in the `.smbh` history journal. The 64 BRep members of the 32 local Form archives give these definition and reference counts.

| BRep faces | Members | Definitions | References |
| --- | --- | --- | --- |
| 1 | 20 | 1 `t_spl_sur`, 1 `t_spl_subtrans_object`, 4 `exact_int_cur`, 4 `exp_par_cur` | 4 `t_spl_sur` |
| 2 | 4 | 2 `t_spl_sur`, 1 `t_spl_subtrans_object`, 7 `exact_int_cur`, 8 `exp_par_cur` | 8 `t_spl_sur`, 1 `t_spl_subtrans_object` |
| 6 | 40 | 6 `t_spl_sur`, 1 `t_spl_subtrans_object`, 12 `exact_int_cur`, 24 `exp_par_cur` | 24 `t_spl_sur`, 5 `t_spl_subtrans_object` |

Each `pcurve` support is a reference to an earlier `t_spl_sur` entry. Only the first `t_spl_sur` in stream order carries the inline T-spline program. The other faces refer to that program.

## Workaround

Keep a reference as the typed `SubtypeRef(Family, Index)` value. `PermuteGeometry` and `PermuteJournal` renumber references when entities move. Rebuild the table in stream order when you validate a stream. `CheckSubtypes` rejects a forward reference and a reference to an entry of a different subtype family. The emitters run this check, so they reject an order that puts a reference before its definition.

## Evidence

- [Spline census](../../../../../re/Fusion/Reconstruction/FormDocuments/SplineCensus.json)
- [Form round trip](../../../../../re/Fusion/Reconstruction/FormDocuments/RoundTrip.json)
- cadmpeg `docs/formats/asm.md` lines 490 and 524 at commit `de2726870ff728352163f601ab4e60bbd54fbade`, as cited in the [cadmpeg comparison](../../../../../re/Fusion/External/CadmpegComparison.md)
- [Form document change entry](../../../../Changes/Fusion/TSpline/FusionFormDocuments.md)
