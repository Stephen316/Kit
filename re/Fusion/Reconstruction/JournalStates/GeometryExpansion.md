# Next geometry families after linear journals

This analysis reuses the complete existing BRep corpus inventory instead of executing production codecs against new sources. [GeometryCoverage.json](GeometryCoverage.json) binds its calculations to the compressed input digest. [GeometryCoverage.py](GeometryCoverage.py) is the reproducible read-only analysis. The original inventory contains all 1,170 initial BRep tables from 582 of 712 indexed archives, with 1,083 distinct blob hashes.

## Initial vocabulary coverage

| Allowed initial record/attribute vocabulary | Members | Histories | Snapshots | Distinct blobs | Archives whose every BRep initial table meets that vocabulary |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing typed journal geometry and four custom attributes | 850 | 396 | 454 | 772 | 375 |
| Above plus transform | 1,007 | 462 | 545 | 921 | 476 |
| Above plus sphere and torus surfaces | 1,019 | 469 | 550 | 933 | 483 |
| Above plus FDM feature attributes | 1,035 | 485 | 550 | 949 | 499 |

These are opportunities, not product support counts. A known record name does not establish every subtype, reference field, attribute version, state journal, container part or native acceptance. Snapshot bodies can be profile and selection caches, not visible solids. This analysis does not label the 375 archives as readable documents.

The largest immediate vocabulary gap is `transform`: 157 initial tables need only that additional record kind. By comparison, sphere/torus vocabulary adds 12 tables after transforms. The largest deeper cluster combines intersection curves, pcurves and spline surfaces, with 103 members split across transformed and untransformed variants.

## Smallest useful next steps

1. **General closed planar polyhedra.** The existing field vocabulary already describes 102 single-body planar/straight histories. Forty are not axis-aligned box candidates. The smallest closed examples are the four-face/six-edge/four-vertex tetrahedra in `meshconvertoperations-5af73924aa60/base_feature_closed.f3d` and `meshconverts-4b42d39fb1d5/faceted_closed.f3d`, each with a 7,383-byte history member. A five-face/nine-edge/six-vertex triangular pipe follows at `pipemodes-87cfa7d8d82b/triangular.f3d`, 9,768 bytes. These need complete ownership/orientation/attribute and journal qualification, then independent semantic topology authoring and native acceptance. They need no new analytic carrier kind.
2. **Transforms and multiple bodies.** Decode the complete transform record with its mapping convention, scale and orientation flags; join it to body ownership and bounding geometry. Preserve all body roots and external keys. This matters more immediately than adding another small primitive family. A multi-body snapshot also needs sheet/profile semantics, so a generic solid-only root check must not be silently relaxed.
3. **Open planar sheets and profile bodies.** The smallest non-box histories include a one-face/four-edge open sketch surface and three-face open tetrahedral shells. Their null partner references and sidedness differ from closed solids. Model boundary coedges and shell closure explicitly, then demonstrate application-native open-body behavior.
4. **Mixed straight/circular planar boundaries.** Existing plane, ellipse and straight fields can describe more than boxes and full cylinders, but trim intervals, edge parameters and reciprocal half-edge orientation must be checked for finite arcs and holes. A familiar carrier name does not justify dropping these mappings.
5. **Small additional analytic families and native attributes.** Sphere and torus surfaces, then `FDM_feature_attrib_def`, have limited but concrete incremental coverage. Their full field semantics and Design joins need native proof. Twelve members also need `no_merge_attribute-st-attrib`; it must not be treated as ignorable metadata.
6. **Spline/intersection and tolerant topology.** The remaining initial tables include 2,076 pcurves, 1,242 intersection curves, 475 spline surfaces and tolerant edge/coedge/vertex classes. These require explicit nested subtypes, knot/weight arrays, trim mappings and tolerances. No raw-token fallback is an acceptable completion path.

The initial type histogram also includes 305 transforms, 14 torus surfaces, 10 sphere surfaces, five wire records and small system-attribute families. Counts include repeated blobs. Full counts and exact smallest source/member identities are in the JSON report.

## Qualification boundary

The new linear journal serializer supplies typed field models for its known families and a complete revision graph, but it deliberately retains the accepted single-active-solid framing and explicit null reserved fields. Its two controlled three-state families do not establish all planar or multi-body behavior. The next implementation should use a separately qualified topology profile rather than weakening journal invariants simply to increase these inventory counts.
