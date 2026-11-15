# Principal sketch support candidates in the 19000 generation

## Scope and source evidence

This A04c finding does not establish native conversion acceptance. The current reader still puts the three discovery YZ sketches on Front Plane. Complete constraints, P04 sketch ownership and P04 face identity remain open.

The source is PR #94 revision `c1c3fcce5b8b67373113ec44ad5d122a52bd7260`. The [remote discovery census](https://github.com/TryUniCAD/Kit/actions/runs/43656612973/job/132636421153) binds 25 P01/P03/P04 native inputs to their source measurements. The report has 634 matched, 110 different and 24 unobserved comparisons. The three principal-plane YZ variants disagree with their measured world endpoints and support names.

Read-only native container extraction on 2026-11-15 inspected the same 25 committed discovery files. It did not run a test suite, SDK neutral reader, CAD application or model. P02 and the P05 holdout were not inspected.

## Layout observations

Each of the 25 `RectangleSketch` native feature spans contains exactly one candidate with this shape:

| Relative offset | Width           | Observed value or meaning                         | Confidence |
| --------------- | --------------- | ------------------------------------------------- | ---------- |
| +0              | 4               | `u32` generation stamp, 19000                     | observed   |
| +4              | 4               | `u32` plane object id, 2 for Front or 4 for Right | candidate  |
| +8              | 4               | opaque `u32` tag, `0x6ad6426c` in these captures  | not found  |
| +12             | 2               | null child token                                  | observed   |
| +14             | 4               | `u32` axis code, `5 - plane id`                   | candidate  |
| +18             | 1               | basis-present flag, 0 or 1                        | observed   |
| +19             | 72 when flagged | nine row-major doubles                            | observed   |

The [earlier resolved-feature finding](Resolvedfeatures.md#2-mocomprefplane_c-run-1--a-conditional-basis-block-not-an-opaque-run) records the corresponding 18000-generation layout. Its named parent is `moCompRefPlane_c`, whose serializer calls `moCompFeature_c` as a base. The existing [feature-body findings](FeatureBody.md#2-mosketchchain_c--the-lead-run-is-closed) refute attributing the plane-id and basis fields to `moSketchChain_c`.

| Recipe        | Candidate stamp offset | Files | Front id / axis / flag | YZ id / axis / flag |
| ------------- | ---------------------: | ----: | ---------------------- | ------------------- |
| P01           |                  11474 |     6 | 2 / 3 / 0              | 4 / 1 / 1           |
| P03           |                  11573 |     8 | 2 / 3 / 0              | 4 / 1 / 1           |
| P04 rectangle |                   5957 |    11 | 2 / 3 / 0              | 4 / 1 / 1           |

P04 `CutSketch` has no candidate in its resolved native span. A plane-layout candidate must not replace its independently observed face support.

The YZ row-major matrix is `(-0, 0, 1), (-0, 1, 0), (-1, 0, 0)`. Its columns give local U `(0,0,-1)`, V `(0,1,0)` and normal `(1,0,0)`. This maps the observed local `(-Z,+Y)` coordinates to the independently measured YZ geometry. This agreement alone does not resolve class references.

## Refuted signature assumption

The current `SketchPlaneRef` scanner searches the bytes for generation 18000 and the fixed tag `f6 5a 1a 69`. Neither signature occurs in the P01/P03 user-sketch spans. The 19000 records instead carry tag `6c 42 d6 6a`. Retaining the old generation or the old capture's opaque tag prevents recognizing these directly serialized candidates.

Treating the tag as universal vocabulary is refuted by the two capture sets. Its semantic identity remains **not found**. It must not become another corpus-specific constant.

## Implementation and unresolved proof

[SolidworksSupportEvidence.py](../../automation/SolidworksSupportEvidence.py) records matching 18000/19000 layouts in each existing native sketch span. It checks bounds, principal ids, the null token, the axis relation, basis availability, finite values, orthonormality and orientation. Each candidate carries a hashed native source span and the explicit status `unqualified_layout_candidate`. The scanner does not alter the production reader, infer an owner from nearby dimensions or silently accept unknown support.

The discovery report now retains this inventory. Its `--check-support-evidence` boundary requires one measured principal-plane candidate for each of the 25 discovery rectangles, including the three YZ cases. It preserves the unresolved class-reference status and does not close A04c.

The remaining promotion requirement is to resolve the enclosing `moCompRefPlane_c` class token through the archive class map, establish the opaque tag's domain from the loader and verify the rule on independent inputs. Source timestamps, spatial proximity and agreement with the same reader do not replace that proof. The P04 face producer and persistent face reference require their own owner chain.
