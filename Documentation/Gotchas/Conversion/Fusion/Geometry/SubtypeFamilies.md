# Subtype references index a family slot in one stream table

## Expectation

A `ref N` scope inside a spline surface, curve or pcurve looks like a reference to entity `N`. In Form bodies, each reference also names a definition with the same subtype name.

## Actual behavior

`N` indexes one subtype table for the complete stream. Each inline subtype definition adds one entry in pre-order. A reference adds no entry. The target is always earlier in the stream.

The slot sets the family of the target, not its subtype name. A `surface` slot can name any earlier surface definition. The 113 byte-exact corpus members give these reference targets.

| Reference family | Target subtype | References | Members |
| --- | --- | --- | --- |
| `surface` | `srf_srf_v_bl_spl_sur` | 712 | 16 |
| `surface` | `sweep_sur` | 514 | 30 |
| `surface` | `VBL_SURF` | 400 | 8 |
| `surface` | `cyl_spl_sur` | 196 | 1 |
| `surface` | `loft_spl_sur` | 152 | 40 |
| `surface` | `exact_spl_sur` | 140 | 16 |
| `surface` | `cl_loft_spl_sur` | 40 | 10 |
| `surface` | `sum_spl_sur` | 16 | 2 |
| `surface` | `g2_blend_spl_sur` | 6 | 1 |
| `curve` | `par_int_cur` | 96 | 2 |
| `curve` | `exact_int_cur` | 49 | 1 |
| `pcurve` | `exp_par_cur` | 96 | 2 |

A change of entity order changes the table index of every later definition. A reference can then point at the wrong definition or at a later definition.

## Workaround

Keep each reference as `SubtypeRef(Family, Index)`. Use `PermuteJournal` or `PermuteGeometry` to move entities, because both renumber references through `ShiftSubtypes`. Use `EmitStateSmb` to select a subset, because it inlines missing definitions through `RelinkSubtypes`. `CheckSubtypes` rejects a forward reference and a family mismatch before emission.

An order that moves a reference before its definition cannot be renumbered. The emitter raises `ValueError` for that order. A stable order keeps the subtype-bearing entities in their relative order and is always valid.

## Evidence

- [Reference targets](../../../../../re/Fusion/Reconstruction/ComplexGeometry/SubtypeTargets.json)
- [Complex verification](../../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyComplex.json)
- Remote integration cases `TestMemberOrder` and `TestForwardRefs` reorder all 113 members and the 62 histories
- [Spline subtype table of Form bodies](../TSpline/SplineSubtypeTable.md)
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
