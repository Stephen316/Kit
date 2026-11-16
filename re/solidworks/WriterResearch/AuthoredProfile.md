# Generation 19000 authored rectangle opening

`WriteAuthoredOpen` constructs the first authored `moProfileFeature_c` through its owned `sgSketch` pointer and the sketch's initial point count. It consumes explicit profile name, document ID, node flags, feature state and point count. Its archive map must already contain the Origin sketch. It allocates a separate sketch object using the inherited `sgSketch` class. [Production typed profile reader](../../../src/convert/adapters/solidworks/Resolved/ProfileSketch.py)

## Pinned source fields

These are preferred virtual addresses in the installed SOLIDWORKS `34.4.1.1011` `sldmodu.dll`. Its SHA-256 is `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`.

| Span in the measured saves | Native store owner |
| --- | --- |
| 5554–5646 | `moProfileFeature_c` schema-1 definition, then the previously allocated `moNodeName_c` class and the lightweight node. `moNode_c::SerializeLWData` stores the flags at `0x4c178b38` and its document ID at `0x4c178b47`. The node flags are `0x40000000` or `0xc0000000` in these controls. The caller supplies the observed flag state. |
| 5646–5757 | The slot-5 profile serializer `0x4bb1b0b0` calls `moModelFeature_c` at `0x4bb1b101`. Its call at `0x4bb18590` enters the inherited feature serializer. `0x4bb10f0f` loads its `+0x1e0` double and `0x4bb10f1a` archives it. `moPart_c::getSumOfFeaturesRegenTime` at `0x4c1c52a0` delegates to the traversal that sums the same member at `0x4c03c6b0` and `0x4c03c736`. Its value is `0.016` in P01 baseline A and P03 YZ and `0.0` in the other 12 saves. |
| 5757–5771 | `moModelFeature_c` writes `+0x35c` at `0x4bb185c0`. The profile writes `AbsoluteRefPlaneByProj8000` at `0x4bb1b153`, the absent sub-sketch reference list at `0x4bb1b192`, and the `+0x3dc` selector at `0x4bb1b28c`. The controls use the ordinary zero branch. |
| 5771–5777 | The profile stores the sketch at owned data member `+0x80` via `0x4bb1b860`. The matching read is `0x4bb1bbcf`. The `sgSketch` point count is a dword. The independent measured graph has four corners and one distinct Origin proxy. [Sketch field store and read evidence](../authoring/RectangleFields.md) |

The observed P01 archive map runs 170→174 and P03 175→179 across this span. The document ID is 26 in both workloads. The profile tag consumes a class and object index. Its name and new sketch each consume an object index. The points have their own local indices. No document or archive index substitutes for a point identity.

## Reproduction

Run `python -B re/solidworks/WriterResearch/VerifyAuthoredProfile.py --read-only` on the 14 receipt-pinned P01/P03 discovery cases. The verifier follows the normal resolved reader through Origin, compares the ModelHeader feature ID and the independently decoded authored sketch allocation, and checks the local Origin proxy owner. It checks all 70 point incidences, 56 line incidences, 56 authored coordinate pairs and 56 directed line endpoint pairs against the licensed measurements. Receipt-order replay SHA-256 is `94e7a495ed5aab2ba98e8833c5154869c0d0678dc778e8ef2387d7b83b189156`. Hosted `CheckProfile` also compares the typed constructed opening and complete map.

The [local rectangle corner writer](RectangleCorners.md) continues from the first point at byte 5777 to the external Origin proxy. The return from parametric geometry still requires constructive rules and native open, rebuild and edit evidence.
