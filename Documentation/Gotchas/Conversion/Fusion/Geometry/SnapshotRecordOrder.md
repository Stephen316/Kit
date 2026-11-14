# Fusion snapshot records follow one breadth-first walk

## Expectation

A `.smb` snapshot lists its records in the order of the history journal. `EmitStateSmb` writes that journal order, so an equal body gives equal bytes.

## Actual behavior

Fusion writes every snapshot record in one breadth-first walk. The walk starts from a root list at the front of the stream. It follows the references of each record in token order.

A root is a record that no earlier record references. Every root comes before every other record. The 62 corpus history archives gave these results.

| Snapshot property | Archives |
| --- | --- |
| Records equal a breadth-first walk from the leading roots | 62 of 62 |
| Roots are bodies only | 54 |
| Roots are bodies and one or two edges | 6 |
| Roots are bodies and eight faces | 2 |

Each edge or face root belongs to a sheet body outside the history. That sheet body is not a root. The walk reaches it later through the references of the edge or face.

| Root kind | Owner body | Archives |
| --- | --- | --- |
| Edge | Two-face sheet with `SketchAttrib` records | 6 loft archives |
| Face | One-face sheet | 2 rule fillet witness archives |

`EmitStateSmb` writes records in journal live-slot order. The first record that differs between the two streams is shown below.

| First differing record | Differing fields | Archives |
| --- | --- | --- |
| Body record | `Prefix`, `FirstLump` | 43 |
| Body record | `Prefix`, `FirstLump`, `TransformRef` | 17 |
| Face root in the snapshot, body record in the state | Record kind | 2 |

## Workaround

Compare a snapshot body with a history body through a walk from each body record. Do not compare stream positions.

Use `EmitStateSmb(Model, StateId, Snapshot=True)` to write the bodies of one state in the Fusion order. That form starts the walk from the body records only. It cannot write edge or face roots.

## Evidence

- [State and snapshot comparison](../../../../../re/Fusion/Reconstruction/ComplexGeometry/CompareStates.json), fields `snapshotRoots`, `snapshotRootsLead` and `snapshotBreadthFirst`
- [Comparison script](../../../../../re/Fusion/Reconstruction/ComplexGeometry/CompareStates.py)
- [Snapshot history identity](SnapshotHistoryIdentity.md)
- [Snapshot feature inputs](SnapshotFeatureInputs.md)
