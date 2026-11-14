# Fusion snapshots drop history identity from history bodies

## Expectation

A snapshot body that is also a history body has the same records as that body in the history state.

## Actual behavior

Fusion removes history identity when it writes a body into a `.smb` snapshot. The 62 corpus history archives hold 317 snapshot bodies. Of these, 91 match a body of a retained history state. The remaining 226 are outside the history.

| Record difference | Snapshot | History state |
| --- | --- | --- |
| Entity tag of every record | -1 in all 62 snapshots | Allocated on 89 body, 46 face, 63 edge and 35 vertex records of matched bodies |
| `TimeAttrib` with `Timestamp_attrib_def` on a body | Absent on 85 matched bodies | Present on those 85 bodies |
| `TagAttrib` with `generic_tag_attrib_def` on a body | Absent on 85 matched bodies | Present on those 85 bodies |
| `TrackAttrib` with `FPM_tracked_attrib_def` on an edge | Absent in all 62 snapshots | Present 9 times on matched bodies |
| Other attributes on faces, edges, coedges and vertices | Equal | Equal |

The 91 matched bodies fall into these comparison modes.

| Comparison mode | Snapshot bodies |
| --- | --- |
| Entity tags cleared, body `TimeAttrib` and `TagAttrib` and all `TrackAttrib` removed | 85 |
| Entity tags cleared only, body attributes kept | 4 |
| Exact, sheets without body attributes or entity tags in the history | 2 |

The 4 exceptions are in the 4 solid sweep archives. Each snapshot holds the same 6-face body twice. One copy keeps the body `TimeAttrib` and `TagAttrib`. The other copy omits them.

Body attributes also occur on 7 two-face sheets outside the history. These sheets own the edge roots of 6 loft snapshots.

## Workaround

Do not compare snapshot records and history records field by field. Clear entity tags and remove these attributes first, then compare.

Use `EmitStateSmb(Model, StateId, Snapshot=True)` to write a state in this form. It clears every entity tag and removes body-owned `TimeAttrib` and `TagAttrib` and every `TrackAttrib`. It splices each attribute chain around a removed record. It writes the records in the [Fusion record order](SnapshotRecordOrder.md).

This form reproduced the snapshot bytes of every archive whose snapshot holds only history bodies.

| Archive | State | Snapshot SHA-256 |
| --- | --- | --- |
| `namedvertexprobe-8d81619f74e6/construction_polynomial_vertex0.f3d` | 6, current | `69f18a6e33a9b6394735da932faa06e0a0b0c630458a638aa6491f06e0b1c75f` |
| `namedvertexprobe-8d81619f74e6/scale_rational_vertex2.f3d` | 6, current is 7 | `28e0dc351e51905e8f566586d4c0ca5c7a1fac010ffb78ee88e913187e857ceb` |
| `pipepaths-3d11bd427946/spline_circular.f3d` | 3, current | `3359ef54e272c8319a9e1c8ff72887861a80fa5f174bbf6995f8c3d802ec5a27` |
| `splinepatches-900d152c2380/splinepatches.f3d` | 6, current | `9a5beecb39e5d0e571c757ee3c9c027540cda671225ba2f93de93b8233509a57` |
| `splinepatches-ac5e846e59c0/splinepatches.f3d` | 4, current | `66d4067e255cba13ff93a6cc565b22430f82481a505ef7f06fd6b4448257c083` |

The form does not reproduce the 4 solid sweep bodies that keep their body attributes. It also does not write bodies that are outside the history.

## Evidence

- [State and snapshot comparison](../../../../../re/Fusion/Reconstruction/ComplexGeometry/CompareStates.json), summary fields `snapshotBodyMatches`, `stateOnlyAttributes`, `entityTagDifferences` and `rebuiltBytesEqual`
- [Comparison script](../../../../../re/Fusion/Reconstruction/ComplexGeometry/CompareStates.py)
- [Snapshot bodies](FusionSnapshotBodies.md)
- [Snapshot feature inputs](SnapshotFeatureInputs.md)
