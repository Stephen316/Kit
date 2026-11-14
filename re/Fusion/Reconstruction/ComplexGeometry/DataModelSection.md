# Draft section for the Fusion data model: complex surface geometry

This draft is for a new section after "Authored round bodies and trimmed round histories" in `Documentation/Reference/Research/FusionDataModel.md`.
The section text starts at the next heading.
Links are relative to `Documentation/Reference/Research/`.
The draft also proposes one row for the tag table in "ASM envelope".

| Tag | Observed payload | Interpretation |
| --- | --- | --- |
| 8 | Unsigned 16-bit length and UTF-8 bytes | String token above 255 bytes |

## Complex surface geometry and explicit NURBS bodies

Spline surfaces, interpolated curves and parameter-space curves are subtype scopes inside ordinary ASM records.
Kit reads and writes them in the typed journal codec.
It also authors explicit NURBS sheets and closed solids.
The [complex geometry entry](../../../../Documentation/Changes/Fusion/Geometry/FusionComplexGeometry.md) gives the API, the limits and the native acceptance.

### Record kinds

| Entity | Subtype slot | Other fields |
| --- | --- | --- |
| `spline-surface` | `surface` | Reversal flag, four optional parameter bounds |
| `intcurve-curve` | `curve` | Reversal flag, two optional parameter bounds |
| `pcurve` | `pcurve` for form 0 | Form, reversal flag, U and V offsets |
| `tcoedge-coedge` | None | Coedge fields, parameter range, curve reference, curve form, inline curve, stamp |
| `tedge-edge` | None | Edge fields, tolerance, save version, stamp |
| `tvertex-vertex` | None | Vertex fields, sentinel, two tolerances, stamp |
| `stitch_hint-sys-attrib` | None | System attribute links, three doubles |
| `vertedge-sys-attrib` | None | System attribute links, count, edge pointer and version-gated integer pairs |
| `wire` | None | Next wire, first coedge, owner shell, a reserved reference and an out or in logical |
| `FDM_feature_attrib_def` attribute | None | Data name, feature tag, flags, layout count, type code, points and a tail value |
| `no_merge_attribute-st-attrib` | None | System attribute links only |

A `pcurve` of form -2, -1, 1 or 2 has no subtype scope.
It names an `intcurve-curve` record that holds the parameter curve.
The absolute form selects the first or second 2D B-spline block of that intcurve.
A negative form reverses the selected curve.
In the corpus, negative forms occur only on reversed coedges and positive forms only on forward coedges.
A coedge record keeps a pointer to its `pcurve` record, and -1 means no pcurve.
Shell slot 6 is the first wire of the shell.
`FDM_feature_attrib_def` carries a `feature_data` or a `thread_face_data` layout.
A live edge record can have a null curve when it closes a cone face at its apex, and its start vertex is its end vertex.
The [wire shell gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/WireShellSlots.md), the [degenerate edge gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/DegenerateHoleEdges.md) and the [thread attribute gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/ThreadAttributeLayouts.md) give the layouts.

The 8 corpus `tvertex-vertex` records have a tolerance equal to the largest tolerance of their `tedge-edge` records plus 1e-10.
Kit refuses a tolerant vertex that is tighter than one of its tolerant edges.
It also refuses a referenced form whose sign disagrees with the coedge sense.
The [referenced pcurve form gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/ReferencedPcurveForms.md) and the [tolerant vertex gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/TolerantVertexOrder.md) give the corpus counts and the native cases.

### Subtype grammar

A subtype scope opens with tag 15 and a name and closes with tag 16.
The name selects a fixed field sequence.
The sequence can contain nested subtype scopes, B-spline blocks and optional fields.
Every field of the 116 complex corpus members is consumed by a typed rule.

| Family | Subtype names |
| --- | --- |
| `surface` | `exact_spl_sur`, `cyl_spl_sur`, `sum_spl_sur`, `helix_spl_line`, `sweep_sur`, `loft_spl_sur`, `cl_loft_spl_sur`, `srf_srf_v_bl_spl_sur`, `VBL_SURF`, `g2_blend_spl_sur`, `t_spl_sur` |
| `curve` | `exact_int_cur`, `par_int_cur`, `int_int_cur`, `spring_int_cur`, `helix_int_cur` |
| `pcurve` | `exp_par_cur` |
| `subtrans` | `t_spl_subtrans_object` |

Every corpus subtype except `helix_int_cur` and `helix_spl_line` contains at least one B-spline block.
In `exact_spl_sur`, `exact_int_cur` and `exp_par_cur`, the B-spline is the definition itself.
In the procedural subtypes, B-spline blocks are approximations or nested definitions beside the defining data.
Earlier binary inspection suggested the field order of `exp_par_cur`, `exact_spl_sur` and the shared `spl_sur` data.
That evidence was removed.
The order is confirmed only by complete decoding of the corpus members.

Eleven subtypes read into frozen records with named fields.
The grammar rules still define the byte layout, and no rule changed.
`CurveContext` holds the shared intcurve data, and `SplineCommon` holds the shared spline-surface data.
`BlendFrame` holds the shared blend data.
`BlendSupport`, `OffsetRadius` and `InterpRadius` hold the blend supports and radii.
The 157 field names in 27 record classes came from earlier binary inspection.
That evidence was removed, so the names are research labels.
They are not confirmed by a black-box experiment.
`cl_loft_spl_sur`, `cyl_spl_sur`, `sum_spl_sur` and the helix subtypes keep the positional tree.
The [typed field order gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/TypedSubtypeFieldOrder.md) gives the rule for edits.

### Subtype references

A `ref N` scope indexes one table for the complete stream.
Each inline definition adds one entry in pre-order, and a reference adds none.
The target is always earlier in the stream.
The slot sets the family of the target, but not its subtype name.
A surface slot of the corpus names nine different surface subtypes.
The [reference targets](SubtypeTargets.json) give the counts.

An entity permutation must renumber every reference.
A subset of entities must inline each definition that it no longer contains.
An order that puts a reference before its definition cannot be written.
The [subtype family gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/SubtypeFamilies.md) gives the workaround.

### B-spline blocks

| Item | Stored form |
| --- | --- |
| Header | Rational form, degrees, closure and singularity codes |
| Knots | Distinct values with their multiplicities |
| Clamped end | Multiplicity equal to the degree |
| Pole count | `sum(multiplicity) - degree + 1` in each direction |
| Surface poles | V rows, with U changing fastest inside each row |
| Weights | Separate from the Euclidean poles |
| Surface rational form | `both`, `u` or `v` |

The Fusion API uses p+1 end copies and a U-major pole order.
The [end knot gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/SplineEndKnots.md) and the [pole order gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/SplinePoleOrder.md) give the conversions.

### Pcurve sense

A pcurve runs on the edge range when the coedge and pcurve reversal flags agree.
It runs on the negated edge range when they differ.
The [pcurve sense gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/PcurveSense.md) gives the corpus counts and the exceptions.

### Seams and collapsed sides

A seam edge of a closed spline face has two uses in one loop with opposite senses.
Each use has its own `pcurve` record.
One of the two records has an `OffsetU` or `OffsetV` of one period, and the other has none.
The 31 corpus seams put the offset on the forward use 21 times and on the reversed use 10 times.
A collapsed side of a B-spline surface has no edge.
Each of the 4 corpus faces with a collapsed side has one seam edge and one closed edge.
Coedges on plane, cone and torus faces store no `pcurve`.
The [seam gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/SeamPcurveOffsets.md), the [collapsed side gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/SingularSplineSides.md) and the [analytic coedge gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/AnalyticFacePcurves.md) give the counts and the native results.

### Corpus coverage

712 study archives contain 1083 unique BRep members.
116 of them contain complex records, and all 116 round-trip byte for byte.
1020 of the 1083 members round-trip byte for byte.

| Record | Active records | Members |
| --- | --- | --- |
| `pcurve` | 2076 | 116 |
| `intcurve-curve` | 1242 | 112 |
| `spline-surface` | 475 | 116 |
| `tcoedge-coedge` | 16 | 2 |
| `tedge-edge` | 8 | 2 |
| `tvertex-vertex` | 8 | 2 |
| `stitch_hint-sys-attrib` | 4 | 4 |
| `vertedge-sys-attrib` | 4 | 2 |

The largest corpus record has 6687 tokens, and the largest bulletin board has 2224 changes.

### Native evidence

Fusion 2706.1.17 accepted three authored NURBS bodies, one typed pole edit, eight byte-exact snapshots and six byte-exact histories in the first pass.
The authored bodies reported `adsk::core::NurbsSurface` faces with zero pole, knot and weight drift.
Fusion reported their straight cubic edges as `Line3D`.

Fusion did not repeat its own rebuild of a rule fillet.
Two control runs differed by a relative 5.06e-5.
The [rule fillet gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/RuleFilletRebuildDrift.md) gives the comparison rule.
The `.smb` snapshot of a fillet archive holds the bodies before the fillet.
The [snapshot gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/SnapshotFeatureInputs.md) gives the measured bodies.

Nine corpus histories with helix subtypes, thread attributes, wire records, a degenerate edge or the largest records were re-emitted byte for byte.
Fusion opened each one and its control with equal values at every stage within 1e-8.

The second pass sent 11 consistent edits.
A knot insertion in a `cl_loft_spl_sur`, `sum_spl_sur`, `cyl_spl_sur`, `par_int_cur`, `int_int_cur` or `exp_par_cur` B-spline kept the shape.
A refined `cyl_spl_sur` profile reached through a `curve` reference changed the reported edge.
Fusion reported the refined B-spline pole for pole in each edited face, coedge or edge, except one pcurve.
Fusion reported that refined `int_int_cur` pcurve as the same curve with the inserted knot at full multiplicity.
The [refined pcurve knots gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/RefinedPcurveKnots.md) gives the comparison.
Fusion reported an edited tolerant edge and tolerant vertex with the stored values.
An edited stitch hint survived a Fusion export.

Fusion accepted five more authored bodies in the second pass.
They are two sheets with an inner loop or a collapsed side, two seamed solids with plane faces and a doubly closed torus.
Each kept its topology, area and surface poles through save and reopen, and each solid kept its volume.
Fusion reported each seam coedge curve with its offset added.
It also reported coedge curves on plane and cylinder faces that store no `pcurve`.
`BRepBody.volume` of two seamed solids differed by up to 3.26e-5 relative, and the very high accuracy volume agreed within 2.4e-10.
The [body volume gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Geometry/BodyVolumeAccuracy.md) gives the values.

### Boundaries

Kit does not evaluate procedural surfaces or curves.
An edit of a procedural field does not update the stored approximation, and no native case changed a procedural field.
The authoring path writes exact B-spline subtypes, plane and cone records only.
`helix_int_cur`, `helix_spl_line` and `wire` records went to Fusion only as byte-identical re-emissions.
`vertedge-sys-attrib` records have byte-level evidence only.
57 of the 62 history snapshots hold bodies that are outside the history.
Fusion exited once in a run whose next case had a form sign against its coedge sense.
No consistent input repeated the exit, and Kit now refuses that edit.
