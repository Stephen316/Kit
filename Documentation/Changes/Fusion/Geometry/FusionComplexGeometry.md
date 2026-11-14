# Complex ASM surface geometry and explicit NURBS bodies

The typed BRep journal codec now reads and writes spline surfaces, interpolated curves, parameter-space curves and tolerant topology. Eleven procedural subtypes have named fields. The codec also reads wire records, thread and no-merge attributes, degenerate edges and records up to 16384 tokens. It authors NURBS sheets and closed solids with holes, seams, collapsed sides and plane or cylinder faces. Before this change, 113 corpus members stopped with `Unsupported Fusion journal entity kind: spline-surface`.

## Usage

`ReadJournal`, `ReadGeometry`, `EmitJournal`, `EmitGeometry`, `EmitStateSmb`, `PermuteJournal` and `PermuteGeometry` accept the new entities. There is no new reader entry point. Module paths in this entry are relative to `convert.formats.Fusion.BrepCodec.Journal`.

`EmitStateSmb(Model, StateId, Snapshot=True)` writes the bodies of one history state in the record order of a Fusion `.smb` snapshot. The [snapshot record order gotcha](../../../Gotchas/Conversion/Fusion/Geometry/SnapshotRecordOrder.md) gives the rule.

| ASM entity | Class | Module | Fields |
| --- | --- | --- | --- |
| `spline-surface` | `SplineNode` | `Spline.SplineNode` | `Prefix`, `Reversed`, `Surface`, `ULower`, `UUpper`, `VLower`, `VUpper` |
| `intcurve-curve` | `IntcurveNode` | `Spline.IntcurveNode` | `Prefix`, `Reversed`, `Curve`, `Lower`, `Upper` |
| `pcurve` | `PcurveNode` | `Spline.PcurveNode` | `Prefix`, `Reversed`, `Curve`, `OffsetU`, `OffsetV`, `Form`, `CurveRef` |
| `tcoedge-coedge` | `TcoedgeNode` | `Complex.Nodes.TcoedgeNode` | `Base`, `RangeLower`, `RangeUpper`, `CurveRef`, `CurveForm`, `Curve`, `Stamp` |
| `tedge-edge` | `TedgeNode` | `Complex.Nodes.TedgeNode` | `Base`, `Tolerance`, `SaveVersion`, `Stamp` |
| `tvertex-vertex` | `TvertexNode` | `Complex.Nodes.TvertexNode` | `Base`, `Sentinel`, `Tolerance`, `SavedTolerance`, `Stamp` |
| `stitch_hint-sys-attrib` | `StitchAttrib` | `Attributes.StitchAttrib` | `Links`, `HintValues` |
| `vertedge-sys-attrib` | `VertedgeAttrib` | `Attributes.VertedgeAttrib` | `Links`, `EdgeSlots` |
| `wire` | `WireNode` | `Geometry.WireNode` | `Prefix`, `NextWire`, `FirstCoedge`, `OwnerShell`, `Inside` |
| `FDM_feature_attrib_def` attribute | `FeatureAttrib` | `Attributes.FeatureAttrib` | `Links`, `DataName`, `FeatureTag`, `Flags`, `TypeCode`, `Points`, `TailCode` |
| `no_merge_attribute-st-attrib` | `NoMergeAttrib` | `Attributes.NoMergeAttrib` | `Links` |

`KComplexTypes` in `Complex.ComplexEntity` lists the first six classes. `CoedgeNode.Pcurve` keeps the coedge reference to its `pcurve` entity, and -1 means no pcurve. `ShellNode.FirstWire` is shell slot 6, and -1 means no wire. A live edge can have no curve when it closes a cone face at its apex. `Validation.IsApexEdge` defines this shape.

### Subtype values

`Surface` and `Curve` hold one subtype value. `SubtypeNode(SubtypeName, Body)` is an inline definition. `SubtypeRef(Family, Index)` refers to the `Index`th definition of the stream. `TsplineSurf` is the typed T-spline definition from the [Form document entry](../TSpline/FusionFormDocuments.md).

`KSubtypeRules` in `Complex.Grammar.SubtypeRules` gives the field sequence of each subtype. For eleven subtypes, `Body` is a frozen record with named fields. For the other subtypes, `Body` is a tree of `KGrammarValue` values from `Complex.Grammar.GrammarValue`. The tree uses tuples, `ChoiceValue`, nested subtype values, `LoftSubdata`, `BsCurve` and `BsSurface`.

| Subtype | Record | Module |
| --- | --- | --- |
| `exact_spl_sur` | `ExactSplSur` with `SplineCommon` | `Complex.Typed.SurfaceRecords` |
| `exp_par_cur` | `ExpParCur` | `Complex.Typed.CurveRecords` |
| `exact_int_cur`, `par_int_cur`, `int_int_cur`, `spring_int_cur` | `ExactIntCur`, `ParIntCur`, `IntIntCur`, `SpringIntCur`, each with `CurveContext` | `Complex.Typed.CurveRecords` |
| `sweep_sur` | `SweepSur`, `SweepProfile` and the path records of `Complex.Typed.SweepPaths` | `Complex.Typed.SweepRecords` |
| `loft_spl_sur` | `LoftSplSur`, `LoftSection`, `LoftPiece` | `Complex.Typed.LoftRecords` |
| `srf_srf_v_bl_spl_sur`, `g2_blend_spl_sur` | `SrfSrfBlend`, `GtwoBlend`, with the parts of `Complex.Typed.BlendParts` | `Complex.Typed.BlendRecords` |
| `VBL_SURF` | `VblSurf`, `VblBoundary` | `Complex.Typed.VertexRecords` |

`KTypedCodecs` in `Complex.Typed.TypedCodecs` maps each of these names to its two converters. The reader converts the grammar tree to the record, and the writer converts it back, so the bytes do not change. The field names, 92 derived and 65 inferred in 27 records, came from binary inspection of the installed ASM kernel. That evidence was removed at the tip, and a black-box experiment does not confirm the names. The byte-exact round trip does not depend on them. `cl_loft_spl_sur`, `cyl_spl_sur`, `sum_spl_sur`, `helix_spl_line` and `helix_int_cur` keep the tree form.

| Family | Subtype names |
| --- | --- |
| `surface` | `exact_spl_sur`, `cyl_spl_sur`, `sum_spl_sur`, `helix_spl_line`, `sweep_sur`, `loft_spl_sur`, `cl_loft_spl_sur`, `srf_srf_v_bl_spl_sur`, `VBL_SURF`, `g2_blend_spl_sur`, `t_spl_sur` |
| `curve` | `exact_int_cur`, `par_int_cur`, `int_int_cur`, `spring_int_cur`, `helix_int_cur` |
| `pcurve` | `exp_par_cur` |
| `subtrans` | `t_spl_subtrans_object` |

A `pcurve` with `Form` 0 holds its curve inline. With `Form` -2, -1, 1 or 2, `Curve` is `None` and `CurveRef` names an `intcurve-curve` entity.

| Function | Module | Result |
| --- | --- | --- |
| `ListSubtypes(Entity)` | `Spline.ListSubtypes` | `(name, None)` for each definition and `(family, index)` for each reference, in stream order |
| `CheckSubtypes(Entities)` | `Spline.CheckSubtypes` | `ValueError` for a forward reference or a family mismatch |
| `ListTsplines(Entities)` | `Spline.ListTsplines` | Each `TsplineSurf` in stream order |
| `WalkSubtypes(Value)` | `Complex.Subtypes.WalkSubtypes` | Each definition and reference inside one value, in pre-order |
| `MapSubtypes(Value, Mapping)` | `Complex.Subtypes.WalkSubtypes` | The value with its reference indexes replaced |
| `RelinkSubtypes(Entities, Chosen)` | `Complex.Subtypes.RelinkSubtypes` | The chosen entities with each missing definition inlined at its first reference |
| `ShiftSubtypes(Entities, Order)` | `Complex.Subtypes.ShiftSubtypes` | The entities with their references renumbered for a new order |

`EmitStateSmb` calls `RelinkSubtypes`. `PermuteJournal` and `PermuteGeometry` call `ShiftSubtypes`. The emitters run `CheckSubtypes`.

### NURBS authoring

`CreateNurbsBody(Model, History, Stamp)` in `Complex.Authoring.CreateNurbsBody` returns a complete `JournalModel`. `Model` is a `NurbsBody`. `History.MaxStateId` must be explicit. Emit the model with `EmitJournal` for an `.smbh` history and with `EmitStateSmb` for an `.smb` body.

| Class | Module | Fields |
| --- | --- | --- |
| `BsCurve` | `Complex.Spline.BsCurve` | `Rational`, `Degree`, `Closure`, `Knots`, `Multiplicity`, `Dimension`, `Poles`, `Weights` |
| `BsSurface` | `Complex.Spline.BsSurface` | `Rational`, `RationalForm`, `UDegree`, `VDegree`, `UClosure`, `VClosure`, `USingular`, `VSingular`, `UKnots`, `UMultiplicity`, `VKnots`, `VMultiplicity`, `Poles`, `Weights` |
| `PlaneCarrier` | `Complex.Authoring.NurbsBody` | `OriginCm`, `Normal`, `ReferenceAxis` |
| `CylinderCarrier` | `Complex.Authoring.NurbsBody` | `OriginCm`, `AxisVector`, `MajorAxisCm` |
| `NurbsEdge` | `Complex.Authoring.NurbsBody` | `StartVertex`, `EndVertex`, `Curve`, `Bounds` |
| `NurbsUse` | `Complex.Authoring.NurbsBody` | `EdgeIndex`, `Reversed`, `Pcurve`, `OffsetU`, `OffsetV` |
| `NurbsFace` | `Complex.Authoring.NurbsBody` | `Surface`, `Uses`, `Holes` |
| `NurbsBody` | `Complex.Authoring.NurbsBody` | `PointsCm`, `Edges`, `Faces`, `EntityTag` |

`NurbsFace.Surface` is a `BsSurface`, a `PlaneCarrier` or a `CylinderCarrier`. The writer emits `exact_spl_sur` in a `spline-surface`, a `plane-surface` or a `cone-surface` record with a unit radius ratio and no bounds. `Uses` is the outer loop and each tuple in `Holes` is an inner loop. `NurbsEdge.Bounds` limits the edge to part of its curve, and `None` uses the full knot range.

The B-spline values use the ASM storage conventions.

| Item | Convention |
| --- | --- |
| Knots | `Knots` holds distinct values. `Multiplicity` holds the count of each value. |
| End multiplicity | Equal to the degree for a clamped curve |
| Pole count | `sum(Multiplicity) - Degree + 1` in each direction |
| Surface pole order | U changes fastest inside each V row |
| Weights | Separate from the poles. Empty for a nonrational value. |
| `RationalForm` | `both`, `u` or `v` for a rational surface. Empty for a nonrational surface. |
| Units | Centimeters for 3D poles. Surface parameters for 2D pcurve poles. |

Give each `NurbsUse.Pcurve` in the direction and range of its edge curve. The writer negates the pcurve of a reversed use. A use on a plane or cylinder has no pcurve. `OffsetU` and `OffsetV` move the pcurve by whole periods of a closed surface direction.

| Topology | How to model it |
| --- | --- |
| Inner loop | A tuple in `NurbsFace.Holes`, clockwise in the surface parameters |
| Seam of a closed direction | One edge with two uses in the same face and opposite senses. One use has `OffsetU` or `OffsetV` of plus or minus one period, so the two pcurves lie one period apart. |
| Collapsed surface side | `USingular` or `VSingular` 1 for the low side or 2 for the high side. The loop has no use on that side. |
| Closed edge | `StartVertex` equal to `EndVertex`, with a closed or periodic curve |
| Mixed solid | NURBS, plane and cylinder faces that share edges, each edge with two uses |

| Helper | Module | Result |
| --- | --- | --- |
| `PatchSheet(Surface, EntityTag)` | `Complex.Authoring.PatchSheet` | A one-face open sheet with four boundary edges and linear pcurves |
| `BoundaryCurve(Surface, SideIndex)` | `Complex.Authoring.PatchSheet` | Side 0 is the low V row, 1 the high U column, 2 the high V row and 3 the low U column |
| `NegateCurve(Curve)` | `Complex.Authoring.NegateCurve` | The curve on the negated, reversed parameter range |
| `PointOnCurve`, `PointOnSurface` | `Complex.Authoring.SplineEval` | Rational de Boor evaluation |
| `ExactSurface`, `ExactCurve`, `ParamCurve` | `Complex.Authoring.ExactSubtypes` | `exact_spl_sur`, `exact_int_cur` and `exp_par_cur` subtype nodes |
| `SplineSurface`, `SplineCurve`, `PcurveSpline` | `Complex.Authoring.ExactSubtypes` | The B-spline inside those three subtype nodes |

## Semantic checks

The reader consumes each subtype with an exact field sequence. It raises `ValueError` for an unknown subtype, a subtype in the wrong family and a reference before its definition. B-spline blocks must have a degree from 1 to 25 and 2 to 4096 strictly increasing finite knots. Each multiplicity is from 1 to the degree plus 1. Poles must be finite and match the knot count. Weights must be positive and finite.

`CreateNurbsBody` adds these checks before it writes records.

| Check | Rule |
| --- | --- |
| Shell | Each edge has one or two uses. A closed shell has two uses for each edge. |
| Shared edge | The two uses have opposite senses |
| Vertices | 1 to 4096 points, and each point bounds an edge |
| Edge curve | The ends of the edge range are within 1e-6 cm of their vertices. `Bounds` stays inside the curve knot range. |
| Pcurve range | The pcurve knot range equals the edge range |
| Pcurve position | The surface point of the pcurve plus its offsets is within 1e-6 cm of the edge point at 17 samples and every knot |
| Pcurve offset | Finite, and only in a closed surface direction |
| Closed direction | The end pole columns or rows and their weights are equal |
| Singular side | All poles of the collapsed side are within 1e-6 cm of one point |
| Analytic face | No pcurve or offset. The edge is within 1e-6 cm of the plane or cylinder at every sample. |
| Analytic frame | Unit direction, perpendicular reference axis, positive cylinder radius |
| Loop | Each loop has at least one use. Each use ends where the next use starts. |
| Seam | The two pcurves of an edge used twice in one spline face start one period apart in exactly one closed direction |

The readers and the emitters also check two rules that all 116 complex corpus members obey.

| Rule | Error |
| --- | --- |
| A referenced `pcurve` form is positive on a forward coedge and negative on a reversed coedge | `Fusion pcurve form sign disagrees with its coedge sense` |
| A `tvertex-vertex` tolerance is at least the tolerance of each `tedge-edge` that ends at it | `Fusion tolerant vertex is tighter than its tolerant edge` |

`StitchAttrib` requires three finite doubles. `VertedgeAttrib` admits at most `KVertedgeCap` (64) edge slots. A vertex with a `vertedge-sys-attrib` can omit its edge reference. A `sketch_attrib_def` custom attribute can name a vertex.

## Reconciliation with Form documents

The Form document change added the `Spline` package with narrower classes. This change keeps its class names, module paths and joins. `CheckDocForms` still uses `ListPrograms`.

| Form model | This change | Reason |
| --- | --- | --- |
| `SubtypeRef(Index)` | `SubtypeRef(Family, Index)` | Corpus references also name other surface subtypes, `curve` definitions and `pcurve` definitions |
| `PcurveNode.Curve` as `ParCurve` with `Support` | `exp_par_cur` `SubtypeNode`, plus `Form` and `CurveRef` | Corpus supports include `plane` surfaces and procedural `spline` surfaces. 372 corpus pcurves use the referenced forms. |
| `IntcurveNode.Curve` as `ExactCurve` | Any curve subtype value | `ExactCurve` admitted null supports only |
| `ExactCurve`, `ParCurve`, `NubsCurve`, `ListSurface` | Removed | The general grammar reads the same records |
| `ListSubtypes` with subtype names for references | Families for references | A reference slot accepts any definition of its family |
| None | `ListTsplines` | Gives the Form joins the T-spline definitions in stream order |

`TsplineSurf`, `SubtransNode`, `NubsSurface`, `PatchCell`, wide text and `CoedgeNode.Pcurve` keep their Form definitions. `Complex.Authoring.ExactSubtypes.ExactCurve` is a new builder function and not the removed class.

## Corpus coverage

The study corpus has 712 F3D archives, and 582 of them contain BRep members. These give 1170 members and 1083 unique members. The [inventory](../../../../re/Fusion/Reconstruction/ComplexGeometry/InventorySummary.json) gives these active record counts.

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

The next table counts the outer subtype scope of each active record. Nested scopes are not in these counts.

| Subtype | Count | Subtype | Count |
| --- | --- | --- | --- |
| `exp_par_cur` | 1612 | `cyl_spl_sur` | 43 |
| `par_int_cur` | 572 | `loft_spl_sur` | 40 |
| Referenced `pcurve` form | 372 | `exact_spl_sur` | 37 |
| `exact_int_cur` | 234 | `cl_loft_spl_sur` | 10 |
| `intcurve` reference | 194 | `srf_srf_v_bl_spl_sur` | 8 |
| `spline` reference | 167 | `helix_int_cur` | 8 |
| `spring_int_cur` | 160 | `sum_spl_sur` | 4 |
| `sweep_sur` | 102 | `helix_spl_line` | 4 |
| `pcurve` reference | 96 | `g2_blend_spl_sur` | 1 |
| `int_int_cur` | 74 | `VBL_SURF` | 60 |

The [complete verification](../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyAll.json) read and re-emitted every unique member with Python 3.14. The reader at the base commit `5a7949c81` read 820 members. The [bounds verification](../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyBounds.json) repeated the run after the record limits, wires and attributes were added.

| Base result | Members | Result now |
| --- | --- | --- |
| `spline-surface` entity kind | 113 | Byte-exact |
| `intcurve-curve` entity kind | 1 | Byte-exact |
| `vertedge-sys-attrib` entity kind | 1 | Byte-exact |
| Historical reference absent or class-incompatible | 9 | Byte-exact |
| Oversized journal entity table | 13 | Byte-exact |

| Verification | Byte-exact members | Complex members byte-exact |
| --- | --- | --- |
| Complete verification | 943 of 1083 | 113 of 116 |
| Bounds verification | 1020 of 1083 | 116 of 116 |

The bounds verification changed these 77 members to byte-exact.

| Former error | Members |
| --- | --- |
| `Missing required Fusion topology reference`, an edge without a curve | 28 |
| `Unsupported Fusion journal attribute family` | 18 |
| `Unsupported Fusion journal entity kind: no_merge_attribute-st-attrib` | 12 |
| `Oversized Fusion bulletin board` | 8 |
| `Oversized Fusion ASM record` | 6 |
| `Unsupported Fusion journal qualified field`, the shell wire slot | 5 |

The largest corpus record has 6687 tokens, and the largest bulletin board has 2224 changes. Both are in `rectsymholdouts-cf85ce4a0382/multiple_bodies.f3d`.

## Limits

- 63 corpus members still stop with an error. The largest groups are 18 generic tags with an attribute pointer, 23 root count disagreements and 9 `int64_attrib` records.
- `cl_loft_spl_sur`, `cyl_spl_sur`, `sum_spl_sur`, `helix_spl_line` and `helix_int_cur` bodies keep the positional tree form. 65 typed field names describe only what is stored.
- Kit does not evaluate procedural surfaces or curves. An edit of a procedural field does not update the stored approximation. The authoring path writes `exact_spl_sur`, `exact_int_cur`, `exp_par_cur`, plane and cone records only.
- Kit does not check that a `tcoedge-coedge` range spans its edge. It does not check that a `vertedge-sys-attrib` names every edge at its vertex.
- The readers do not check seam offsets. Only `CreateNurbsBody` requires the two uses of a seam to lie one period apart.
- Fusion lists no separate body for a wire. Wire records have archive-level native evidence only.
- `EmitStateSmb` with `Snapshot=True` starts from body records only. 57 of the 62 corpus snapshots also hold bodies outside the history, such as sketch sheets. Kit cannot write those bodies from the history.
- The entity table limit is 4096 entities. A record can have 16384 tokens, and a bulletin board 4096 changes.

## Verification evidence

### First pass

[Native acceptance](../../../../re/Fusion/LocalOracle/ComplexGeometry/NativeAcceptance.json), SHA-256 `6e9a616056ae539b3c6ee6caf22f3f0fc8ad35b6dfa68cec322da9291a55a4e4`, has status `accepted` in Fusion 2706.1.17. Zero documents were open before and after the run. The [preparation](../../../../re/Fusion/LocalOracle/ComplexGeometry/Preparation.json), SHA-256 `5a5de5583d81de989688909dbc08870cca8b9ac74542160f0aa009140ab8cad9`, binds each input and output hash.

Each authored body went through `TemporaryBRepManager` import, a persisted body, save and reopen. The values after reopen were equal to the values before.

| Body | Topology | Area (cm²) | Volume (cm³) | Native surface | Native edges |
| --- | --- | --- | --- | --- | --- |
| `AuthoredPatch`, bicubic 5×4, interior U knot | 1 face, 4 edges, 4 vertices | 7.366308780834109 | None, open sheet | `NurbsSurface` | 4 `NurbsCurve3D` |
| `AuthoredRational`, rational biquadratic | 1 face, 4 edges, 4 vertices | 11.361644058057117 | None, open sheet | `NurbsSurface` | 4 `NurbsCurve3D` |
| `AuthoredPillow`, six bicubic faces | 6 faces, 12 edges, 8 vertices | 25.0885564915581 | 10.501319359009246 | 6 `NurbsSurface` | 12 `Line3D` |

| Body | Area relative error | Volume relative error | Worst sample drift (cm) | Pole, knot and weight drift | Bounds excess (cm) |
| --- | --- | --- | --- | --- | --- |
| `AuthoredPatch` | 1.29e-9 | None | 5.24e-16 | 0 | 8.1e-5 |
| `AuthoredRational` | 8.6e-13 | None | 1.40e-15 | 0, edge poles 4.4e-16 | 2.1e-4 |
| `AuthoredPillow` | 1.43e-7 | 3.18e-8 | 1.83e-15 | 0 | 0 |

The expected values come from an independent research evaluator. The pillow centroid differs by 1.10e-8 cm. Every sample point was on its face, and each body was valid.

`EditedPatch` changes pole 4 (u=1, v=1) of a corpus `exact_spl_sur` from z 1.2 cm to z 2.0 cm. Fusion accepted it with area 6.782947284786066 cm² against 6.432285222128447 cm² for the control. The changed surface had zero pole, knot and weight drift.

Eight decoded corpus snapshots were byte-exact. Each imported as valid bodies and gave equal values after save and reopen. Six corpus histories were re-emitted byte-exact. Each control and re-emitted history went through every rollback marker, rebuild, a parameter edit, save and reopen.

| History | Subtypes other than `exp_par_cur` | Edit | Volume before edit (cm³) | Volume after edit (cm³) | Comparison |
| --- | --- | --- | --- | --- | --- |
| `LoftDirection` | `loft_spl_sur`, `exact_int_cur` | `d1` ×1.25 | 7.113009471009052 | 9.124514387086997 | Equal within 1e-8 |
| `SweepRail` | `sweep_sur`, `par_int_cur` | `d2` ×0.8 | 0.31536 | 0.26929152 | Equal within 1e-8 |
| `SolidSweep` | `sweep_sur`, `exact_spl_sur`, `par_int_cur` | `d5` ×0.8 | 143.08127683038546 | 143.24915129513576 | Equal within 1e-8 |
| `ChordFillet` | `srf_srf_v_bl_spl_sur`, `exact_int_cur`, `int_int_cur`, `spring_int_cur` | `d4` ×1.25 | 23.987122505214554 | 23.97987969406579 | Equal within 1e-8 |
| `CurvatureFillet` | `g2_blend_spl_sur`, `int_int_cur` | `d4` ×1.25 | 23.974732651090335 | 23.960519767328645 | Equal within 1e-8 |
| `RuleFillet` | `VBL_SURF`, `srf_srf_v_bl_spl_sur`, `par_int_cur`, `spring_int_cur` | `d7` ×1.5 | 37.96756373315546 | 37.95187567917283 | Relative drift 4.24e-5 against a control self drift of 5.06e-5 |

The [rule fillet gotcha](../../../Gotchas/Conversion/Fusion/Geometry/RuleFilletRebuildDrift.md) explains the last row. The [native coverage](../../../../re/Fusion/Reconstruction/ComplexGeometry/NativeCoverage.json) lists the subtypes in every member that Fusion opened.

Binary inspection first matched the field order of `exp_par_cur`, `exact_spl_sur`, `spl_sur`, `TCOEDGE`, `TEDGE`, `TVERTEX`, `ATTRIB_STITCH_HINT`, `ATTRIB_VERTEDGE` and `ATTRIB_SYS` to kernel save routines. That evidence was removed at the tip. The stored order keeps saved-document support: Kit re-emits the corpus members byte for byte, and Fusion opened them.

### Lifted bounds

[Bounds acceptance](../../../../re/Fusion/LocalOracle/ComplexGeometry/Bounds/NativeAcceptance.json), SHA-256 `d44670ba057d49a737a3b2a53135367bcf84f8d4c0b0e7e1e38b9fedf16d3af8`, has status `accepted` in Fusion 2706.1.17. Zero documents were open before and after the run. Each case opened the corpus archive and a copy with its BRep members re-emitted by Kit. Every member was byte-exact. Every stage of the two copies was equal within 1e-8.

| Case | Content | Edit |
| --- | --- | --- |
| `ModeledThread` | `helix_int_cur`, `helix_spl_line`, thread attributes | Parameter `d1` from 2.0 cm to 3.0 cm. The thread extent grew by the expected 1.0 cm. |
| `TappedHole` | `helix_int_cur`, `helix_spl_line`, thread attributes, a degenerate edge | Parameter `d7` from 1.0 cm to 0.8 cm. The thread extent shrank by the expected 0.2 cm. |
| `AlongVector`, `ClosestPoint` | `wire`, a wire shell, a no-merge attribute | None |
| `SketchLine`, `OffsetPositive`, `ReversedNegative` | `wire`, a wire shell | None |
| `TwoTexts` | A history record above 4096 tokens | None |
| `MultipleBodies` | The largest record and bulletin board of the corpus | None |

A first run of these cases stopped when Fusion exited during the `TwoTexts` control. The [crash record](../../../../re/Fusion/LocalOracle/ComplexGeometry/Bounds/CrashRecord.json) gives the last step. Two probe runs and the accepted run of the same control did not repeat the exit.

### Second pass

The [second-pass preparation](../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Preparation.json), SHA-256 `74cd0b937bad6350e28d2e49bd36b79f52988732179d193501b93a35a836e570`, binds each input and output hash. It holds 11 consistent edits and 7 edits that are inconsistent by construction. A knot insertion adds one knot and recomputes the poles, so the shape stays the same. The largest shape drift of an insertion was 3.8e-15.

Each consistent edit went through `TemporaryBRepManager` import, a persisted body, save and reopen, together with its unedited original. Each body was valid, and the values after reopen were equal to the values before. Fusion 2706.1.17 reported these results for the edited body.

| Case | Edited record | Edit | Result |
| --- | --- | --- | --- |
| `ClLoftRefine` | `cl_loft_spl_sur` approximation | V knot 0.5, 148 to 185 poles | 1 face with the refined poles |
| `SumSplRefine` | `sum_spl_sur` approximation | U knot 0.25, 6 to 9 poles | 1 face with the refined poles |
| `CylSplRefine` | `cyl_spl_sur` approximation | U knot 0.5, 6 to 8 poles | 1 face with the refined poles |
| `CylSplCurveRefine` | `cyl_spl_sur` profile curve, reached by a `curve` reference | Knot 0.5, 3 to 4 poles | 1 edge with the refined curve |
| `PcurveFormRefine` | First pcurve of a `par_int_cur`, used by forms 1 and -1 | Knot 0.5, 2 to 3 poles | Both coedges with the refined pcurve |
| `TolerantFormRefine` | Second pcurve of an `int_int_cur`, used by form 2 | Knot -2.3126131813790116, 4 to 5 poles | The same curve with the knot at multiplicity 3 |
| `PcurveRefine` | `exp_par_cur` definition reached by a `pcurve` reference | Knot 0.5, 2 to 3 poles | 2 coedges with the refined pcurve |
| `CurveRefine` | `par_int_cur` definition reached by a `curve` reference | Knot 0.18692982572692135, 10 to 11 poles | 2 edges with the refined curve |
| `TolerantEdge` | `tedge-edge` tolerance | 1.6486711089754196e-05 to 2e-05 | 1 edge with tolerance 2e-05 |
| `TolerantVertex` | `tvertex-vertex` `Tolerance` and `SavedTolerance` | 2.325530054202186e-05 to 6e-05 | Vertex tolerance 6e-05 |
| `StitchHint` | `stitch_hint-sys-attrib` first value | 0.0011554212243761065 to 0.12615542122437612 | The exported body holds the new value |

The [refined pcurve knots gotcha](../../../Gotchas/Conversion/Fusion/Geometry/RefinedPcurveKnots.md) explains the `TolerantFormRefine` row. The API gives no attribute values, so `StitchHint` exported both bodies with `TemporaryBRepManager.exportToFile`. Kit read both exports and re-emitted them byte for byte. The `PcurveRefine` and `CurveRefine` original is the `EmitStateSmb` output of a corpus history. Fusion opened it as a valid body.

Kit refuses three of the inconsistent edits on read and on emit. The other four pass the Kit checks and have digests only.

| Case | Edit | Kit result |
| --- | --- | --- |
| `PcurveFormSign` | Form 1 to -1 on a forward coedge | `ValueError`, form sign |
| `TolerantFormTwo` | Form 2 to -2 on a forward coedge | `ValueError`, form sign |
| `TolerantOrder` | Vertex tolerance 2.325530054202186e-05 to 1e-05, below an edge tolerance | `ValueError`, tolerant vertex |
| `PcurveFormOffset` | `OffsetU` -2π to 0 on a seam pcurve | Accepted |
| `CylSplAxis` | `cyl_spl_sur` axis (0, 0, 1) to (0.25, 0, 1) | Accepted |
| `TolerantCoedge` | `tcoedge-coedge` range 0 to 5 changed to 0 to 4 | Accepted |
| `VertedgeSlots` | One edge slot of a `vertedge-sys-attrib` cleared | Accepted |

An earlier run queued the `PcurveFormSign` edit before the form check existed. Fusion exited during that run. The last checkpoint of the [crashed run](../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Crashed.json) holds 5 authored and 5 subtype cases, and `PcurveFormSign` was the next case. The step at which Fusion exited is not known. The [edited body](../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/CrashedPcurveFormSignMutant.smb) has SHA-256 `be312ee6bf41e33c4af93bf13deb7d155b763c3002ab34a3604f12b04642e93d`. No consistent input repeated the exit, and the edit was not sent again.

The second pass also authored five bodies with `CreateNurbsBody`. Each went through `TemporaryBRepManager` import, a persisted body, save and reopen. Each body and face was valid, and the values after reopen were equal to the values before.

| Body | Content | Topology | Native faces |
| --- | --- | --- | --- |
| `HoledPatch` | Bicubic sheet with a rectangular inner loop | 1 face, 8 edges, 8 vertices | `NurbsSurface` |
| `CollapsedPatch` | Bicubic sheet with a collapsed high V side | 1 face, 3 edges, 3 vertices | `NurbsSurface` |
| `CappedTube` | Rational U-closed side with one seam, and two plane caps | 3 faces, 3 edges, 2 vertices | `NurbsSurface`, 2 `Plane` |
| `DomedCylinder` | Cylinder face with two loops, a plane bottom and a U-closed dome with a collapsed side | 3 faces, 3 edges, 3 vertices | `Cylinder`, `NurbsSurface`, `Plane` |
| `NurbsTorus` | One rational face closed in U and V, with two seams and one vertex | 1 face, 2 edges, 1 vertex | `NurbsSurface` |

| Body | Area relative error | Volume relative error | Centroid drift (cm) | Worst sample drift (cm) | Coedge curves equal to the prediction |
| --- | --- | --- | --- | --- | --- |
| `HoledPatch` | 1.40e-9 | None, open sheet | None | 5.24e-16 | 8 of 8 |
| `CollapsedPatch` | 2.7e-14 | None, open sheet | None | 5.09e-16 | 3 of 3 |
| `CappedTube` | 3.69e-10 | 2.30e-11 | 1.21e-11 | 5.66e-16 | 4 of 4 |
| `DomedCylinder` | 8.4e-15 | 7.31e-11 | 5.68e-11 | 7.02e-16 | 3 of 3 |
| `NurbsTorus` | 2.34e-10 | 2.34e-10 | 5.1e-16 | 6.66e-16 | 4 of 4 |

The pole, knot and weight drift of each NURBS face was 0, and each vertex was at its expected point. Fusion reported every edge as `NurbsCurve3D`. The area, volume and centroid come from `getPhysicalProperties` at `VeryHighCalculationAccuracy`. These gotchas give the other observations.

| Observation | Gotcha |
| --- | --- |
| Each seam coedge curve includes its offset | [Seam pcurve offsets](../../../Gotchas/Conversion/Fusion/Geometry/SeamPcurveOffsets.md) |
| A collapsed side has no edge | [Collapsed spline sides](../../../Gotchas/Conversion/Fusion/Geometry/SingularSplineSides.md) |
| Plane and cylinder coedges have a curve that the stream does not store | [Coedge curves on analytic faces](../../../Gotchas/Conversion/Fusion/Geometry/AnalyticFacePcurves.md) |
| `BRepBody.volume` of two solids differs by up to 3.26e-5 relative | [Body volume accuracy](../../../Gotchas/Conversion/Fusion/Geometry/BodyVolumeAccuracy.md) |

All three run reports completed after the relaunch that followed the crashed run. Zero documents were open before and after each run. The [analysis](../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Analysis.json), SHA-256 `4a311525eb1a710d6e8bb83c0856e03bbc5186847af1124475992020d570d52d`, decodes the stitch exports and compares the reported representations and authored measures.

| Run report | SHA-256 | Cases |
| --- | --- | --- |
| [Subtypes](../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Subtypes.json) | `b7e5f02c83cbf4b7a6d68b30c951d14f1ad5deb8e4ad4332df9f9bef9937a5dc` | 9 subtype cases. `StitchHint` stopped on an export argument, and `TolerantFormRefine` had another representation. |
| [Diagnose](../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Diagnose.json) | `70c0540137ae0d490a3acf9ad2d5e34cb118829644d48a885c4d447c17ba1cd5` | `StitchHint` with the export corrected, and `TolerantFormRefine` with the reported curves kept |
| [Remaining](../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Remaining.json) | `04331a7d4b3f497dea32f9b2af296a6799e8a38d7f0430abb9ff94ba35af72fd` | The 5 authored bodies, `CylSplRefine` and `CylSplCurveRefine`, with status `accepted` |

### History snapshots

The [state comparison](../../../../re/Fusion/Reconstruction/ComplexGeometry/CompareStates.json) covers the 62 corpus histories with a `.smb` snapshot. No default `EmitStateSmb` output equals its snapshot. The snapshot holds its records in a breadth-first order. It drops the body time and tag attributes and the edge track attributes. Of the snapshots, 5 hold only history bodies, and `Snapshot=True` rebuilt all 5 byte for byte. The other 57 also hold 226 bodies that no retained history state contains. The [snapshot record order gotcha](../../../Gotchas/Conversion/Fusion/Geometry/SnapshotRecordOrder.md) and the [snapshot identity gotcha](../../../Gotchas/Conversion/Fusion/Geometry/SnapshotHistoryIdentity.md) give the rules.

### Boundaries

- Only the authored bodies, `EditedPatch` and the second-pass edits hold bytes that Fusion did not write. The other native inputs are byte-identical re-emissions.
- The four fillet snapshots contain no complex records. Their complex subtypes were opened through the history members only.
- `helix_int_cur`, `helix_spl_line`, `wire` records and the thread and no-merge attributes went to Fusion only in byte-identical re-emissions.
- Each subtype edit inserts a knot into a stored B-spline. No native case changed a procedural field, such as the axis of a `cyl_spl_sur`.
- `tcoedge-coedge` records went to Fusion unedited only. `vertedge-sys-attrib` records did not occur in a native case. The prepared edit of each was inconsistent and was not sent.
- `EmitStateSmb` output of one corpus history went to Fusion, as the `PcurveRefine` original. Of the 62 snapshots, 57 hold bodies that Kit cannot write from the history.
- The authored bodies have `exact_spl_sur`, plane and cylinder faces only. Kit does not author other analytic carriers or procedural subtypes.
- The Fusion exit in the run with the `PcurveFormSign` case has no known cause.

### Tests

Remote integration cases in `tests/convert/formats/FusionCodec/Brep/Complex/` cover these items.

| Test file | Cases |
| --- | --- |
| `ComplexCorpusTests.py` | 113 complex members byte for byte and in a stable reorder. A forward-reference reorder and the state of each of the 62 histories. The 3 lifted complex members and their complex records. |
| `BoundMemberTests.py` | The 9 lifted histories and their states, the largest record and board, and both limits |
| `FeatureAttribTests.py`, `WireRecordTests.py` | Thread layouts, no-merge attributes, a degenerate edge, wire records and their faults |
| `TypedFieldTests.py` | Named blend, sweep, loft and NURBS fields, an edit, three faults, a record walk and the positional subtypes |
| `SnapshotFormTests.py` | 5 snapshots rebuilt byte for byte, the snapshot form of the 62 histories and the 3 first-pass bodies, and the faults |
| `SystemAttribTests.py`, `SubtypeTableTests.py` | Stitch hints, vertex edges and the subtype table |
| `AuthoredNurbsTests.py`, `WiderNurbsTests.py` | 3 first-pass and 5 second-pass authored bodies against the committed fixtures, 9 and 13 faults, and the guards |
| `ComplexChecksTests.py` | A flipped form sign and a tolerant vertex below its edge |

Local tests did not run. Black, Ruff, Mypy, Pyright, steering, rationale and path checks passed.

## Related information

- [Pole order](../../../Gotchas/Conversion/Fusion/Geometry/SplinePoleOrder.md)
- [End knot multiplicity](../../../Gotchas/Conversion/Fusion/Geometry/SplineEndKnots.md)
- [Pcurve sense](../../../Gotchas/Conversion/Fusion/Geometry/PcurveSense.md)
- [Subtype families](../../../Gotchas/Conversion/Fusion/Geometry/SubtypeFamilies.md)
- [Straight spline edges](../../../Gotchas/Conversion/Fusion/Geometry/StraightSplineEdges.md)
- [Snapshot feature inputs](../../../Gotchas/Conversion/Fusion/Geometry/SnapshotFeatureInputs.md)
- [Rule fillet rebuild drift](../../../Gotchas/Conversion/Fusion/Geometry/RuleFilletRebuildDrift.md)
- [Typed subtype field order](../../../Gotchas/Conversion/Fusion/Geometry/TypedSubtypeFieldOrder.md)
- [Wire shell slots](../../../Gotchas/Conversion/Fusion/Geometry/WireShellSlots.md)
- [Degenerate edges](../../../Gotchas/Conversion/Fusion/Geometry/DegenerateHoleEdges.md)
- [Thread attribute layouts](../../../Gotchas/Conversion/Fusion/Geometry/ThreadAttributeLayouts.md)
- [Snapshot record order](../../../Gotchas/Conversion/Fusion/Geometry/SnapshotRecordOrder.md)
- [Snapshot history identity](../../../Gotchas/Conversion/Fusion/Geometry/SnapshotHistoryIdentity.md)
- [Referenced pcurve forms](../../../Gotchas/Conversion/Fusion/Geometry/ReferencedPcurveForms.md)
- [Refined pcurve knots](../../../Gotchas/Conversion/Fusion/Geometry/RefinedPcurveKnots.md)
- [Tolerant vertex order](../../../Gotchas/Conversion/Fusion/Geometry/TolerantVertexOrder.md)
- [Seam pcurve offsets](../../../Gotchas/Conversion/Fusion/Geometry/SeamPcurveOffsets.md)
- [Collapsed spline sides](../../../Gotchas/Conversion/Fusion/Geometry/SingularSplineSides.md)
- [Coedge curves on analytic faces](../../../Gotchas/Conversion/Fusion/Geometry/AnalyticFacePcurves.md)
- [Body volume accuracy](../../../Gotchas/Conversion/Fusion/Geometry/BodyVolumeAccuracy.md)
- [Spline subtype table of Form bodies](../../../Gotchas/Conversion/Fusion/TSpline/SplineSubtypeTable.md)
