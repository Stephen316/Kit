# Principal sketch support candidates in the 19000 generation

## Scope and source evidence

The current reader puts the three discovery YZ rectangle sketches on Front Plane. The licensed loader resolves the support class and transform for the samples below. Production decoding still needs a structural walk to the sketch occurrence. The discovery candidates remain unqualified.

The source is PR #94 revision `c1c3fcce5b8b67373113ec44ad5d122a52bd7260`. The [remote discovery census](https://github.com/TryUniCAD/Kit/actions/runs/43656612973/job/132636421153) binds 25 P01/P03/P04 native inputs to their source measurements. The report has 634 matched, 110 different and 24 unobserved comparisons. The three principal-plane YZ variants disagree with their measured world endpoints and support names.

Read-only container extraction on 2026-11-15 inspected the same 25 committed discovery files. The separate licensed loader traces used fresh processes and scratch copies of four of these inputs. P02 and the P05 holdout were outside both observations.

## Layout observations

Each of the 25 `RectangleSketch` native feature spans contains exactly one candidate with this shape:

| Relative offset | Width           | Observed value or meaning                         | Confidence |
| --------------- | --------------- | ------------------------------------------------- | ---------- |
| +0              | 4               | `u32` generation stamp, 19000                     | observed   |
| +4              | 4               | `i32` referenced feature ID, 2 for Front or 4 for Right | loader |
| +8              | 4               | `su_CTime` from the inline feature reference    | loader     |
| +12             | 2               | null child token                                  | observed   |
| +14             | 4               | `u32` plane axis code, `5 - feature ID` in these files | loader |
| +18             | 1               | enclosing profile transform's matrix-present flag | loader    |
| +19             | 72 when flagged | nine row-major doubles in that transform          | observed   |

The earlier resolved-feature finding records the corresponding 18000-generation layout, including the conditional 72-byte span. The native trace below resolves the modern ownership boundary between the plane record and the profile transform. [Historical layout](Resolvedfeatures.md#2-mocomprefplane_c-run-1--a-conditional-basis-block-not-an-opaque-run)

| Recipe        | Candidate stamp offset | Files | Front id / axis / flag | YZ id / axis / flag |
| ------------- | ---------------------: | ----: | ---------------------- | ------------------- |
| P01           |                  11474 |     6 | 2 / 3 / 0              | 4 / 1 / 1           |
| P03           |                  11573 |     8 | 2 / 3 / 0              | 4 / 1 / 1           |
| P04 rectangle |                   5957 |    11 | 2 / 3 / 0              | 4 / 1 / 1           |

P04 `CutSketch` has no candidate in its resolved native span. A plane-layout candidate must not replace its independently observed face support.

The YZ row-major matrix is `(-0, 0, 1), (-0, 1, 0), (-1, 0, 0)`. Its columns give local U `(0,0,-1)`, V `(0,1,0)` and normal `(1,0,0)`. This maps the observed local `(-Z,+Y)` coordinates to the independently measured YZ geometry.

## Refuted signature assumption

The current `SketchPlaneRef` scanner searches the bytes for generation 18000 and the fixed tag `f6 5a 1a 69`. Neither signature occurs in the P01/P03 user-sketch spans. The 19000 records instead carry tag `6c 42 d6 6a`. Retaining the old generation or the old capture's opaque tag prevents recognizing these directly serialized candidates.

## Feature reference timestamp

The matching SOLIDWORKS build `34.4.1.1011` identifies this word as the `su_CTime` field of `moFRData_c`. The `moCompRefPlane_c` constructor at `sldmodu.dll` RVA `0x138fb0` installs the vtable at `0x1c4a220`. Its archive slot 5 at `0xa66060` calls the reference-geometry base at `0xa65f10`, which calls the component-feature serializer at `0xa65530`.

The component-feature serializer first calls `moCompRef_c::Serialize` at `0xa66160`. The modern read branch at `0xa66eda` reads the last base word into the field returned by `getMoVersionCreated`. The feature-reference-present branch at `0xa65923` then calls the serializer at `0x9f3e50`. That serializer reads a signed feature ID and an archived `su_CTime`. The `swccu.dll` operator at RVA `0x1bc60` consumes one unsigned 32-bit word. The following object reference in the enclosing record is read at `0xa65fef`. [Historical feature reference layout](FeatureBody.md#4-mocompfeature_c--the-array-geometry-is-measured-the-entry-body-is-open), [historical class trace](../../data/segments/Streams/SegmentsBaseline.json)

In the historical baseline, `moCompRefPlane_c` node 211 contains the aligned reference at offsets 7,958 and 7,962, immediately before its null child at 7,966. The time `0x691a5af6` represents 2025-11-16 23:15:02 UTC. A read-only container audit of all 25 receipt-pinned 19000-generation discovery files found `0x6ad6426c` at the corresponding offset in the candidate, representing 2026-10-19 16:16:44 UTC. The reference timestamp can vary with the source history. The candidate JSON retains `opaque_reference_tag_u32` for compatibility.

Build binary SHA-256 pins for the offline inspection are `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99` for `sldmodu.dll` and `7254b30f4eb77fd5b49fdbb0a7ab499ba3bf1d39a3f8f18d72090c2568967b49` for `swccu.dll`.

## Licensed loader observations

Four independently opened captures used SOLIDWORKS `34.4.1.1011` with the build pins above. Each observed full `Contents/Config-0-ResolvedFeatures` buffer matched the corresponding capture stream byte for byte. All four scratch parts retained their hashes after the owning processes exited.

In each capture the plane serializer's body began immediately after a two-byte class reference. At its entry the archive's live class map resolved the token to `moCompRefPlane_c`. The same receiving object was observed when the nested feature-reference serializer read the ID and time and when the plane serializer read the axis code. Offsets in this table are decimal and refer to the decompressed stream.

| Capture | Class token at offset | Class map index | Feature ID at offset | Axis code at offset | Profile matrix flag at offset |
| ------- | --------------------- | --------------- | -------------------- | ------------------- | ----------------------------- |
| P01 YZ | `0x80a7` at 11391 | 167 | 4 at 11478 | 1 at 11488 | 1 at 11492, traced |
| P03 YZ | `0x80ac` at 11490 | 172 | 4 at 11577 | 1 at 11587 | 1 at 11591, traced |
| P04 baseline A | `0x8152` at 5874 | 338 | 2 at 5961 | 3 at 5971 | 0 at 5975, adjacent byte |
| P04 YZ | `0x8152` at 5874 | 338 | 4 at 5961 | 1 at 5971 | 1 at 5975, adjacent byte |

All four call stacks return to the profile serializer after the plane pointer read at `sldmodu.dll` RVA `0x9dbdc6`. The enclosing profile calls `mgXform_c::restore` at `0x9dbe34` in the modern-version branch. The P01 and P03 traces also hit that call with the cursor at the matrix-present flag, four bytes after the plane's axis code. The restore routine reads one flag, the optional nine-double matrix, three translation doubles, one scale double and then the flag for a further optional reference. The resolved class and ownership follow from the archive and call path. The token values are capture-specific map indices.

## Implementation and unresolved proof

[SolidworksSupportEvidence.py](../../automation/SolidworksSupportEvidence.py) records matching 18000/19000 layouts in each existing native sketch span. It checks bounds, principal ids, the null token, the axis relation, basis availability, finite values, orthonormality and orientation. Each candidate carries a hashed native source span and the explicit status `unqualified_layout_candidate`. The scanner does not alter the production reader, infer an owner from nearby dimensions or silently accept unknown support.

The discovery report's `--check-support-evidence` boundary requires one measured principal-plane candidate for each of the 25 discovery rectangles, including the three YZ cases. Its candidates still carry unresolved class-reference status because the scanner does not traverse the archive class map.

Promotion to the production reader requires carrying the class and object maps to the correct profile occurrence and verifying the resulting world geometry on independent inputs. The licensed P04 readback provides the boss occurrence and persistent supporting-face identity for the eleven P04 variants. The face reference's archive encoding still requires its own owner chain. [Native P04 observations](../../../Documentation/Changes/Research/Workers/SolidWorksCutFaceReadback.md)
