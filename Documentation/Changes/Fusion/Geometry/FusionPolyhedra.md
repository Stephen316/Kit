# Typed convex polyhedra and body transforms

The Fusion journal codec now interprets closed convex planar bodies independently of a cuboid's face count or axis alignment. It also constructs complete topology from explicit vertices and outward face loops, and emits a selected history state as a standalone SMB body.

## APIs and units

The additions live under `convert.formats.Fusion.BrepCodec.Journal`:

| API                         | Behavior                                                                                                              |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `Planar.ReadPlanarState`    | Resolves a requested journal state and returns its qualified planar bodies                                            |
| `PolyAuthor.CreatePolyBody` | Creates a complete two-state journal from `Polyhedron`, explicit `HistoryState`, provenance and an optional placement |
| `EmitStateSmb`              | Emits the selected live entity state with all references compacted and no history section                             |
| `Geometry.TransformNode`    | Retains the complete body transform as named fields                                                                   |

`Polyhedron.PointsMm` is an immutable tuple of three-dimensional points in millimetres. `FaceLoops` contains vertex-index rings with outward winding. The constructor allocates each body, lump, shell, face, loop, coedge, edge, vertex, point, plane and straight carrier from those values. It derives reciprocal edge partners, incident owner pointers, carrier origins and directions, endpoint parameters and the complete insertion journal. `EntityTag` is an explicit body identity; the supplied history allocator must exceed it. No source file, captured record, runtime CAD library or fixture is required.

The constructor qualifies four to 128 vertices and four to 128 faces within the existing 1,024-entity quota. Faces are strictly convex, planar, single-loop polygons. The shell must be closed and convex, with positive volume. It does not author Design features or generic/sketch provenance attributes: those require a separate semantic feature contract. The resulting journal and standalone geometry contain fully derived native topology.

`ReadPlanarState` uses the history's replacement aliases and selected revisions, including archived geometry. `PlanarShell` exposes the state ID, body reference and entity tag, vertex/face references, world-space points in centimetres, outward face rings and volume in cubic centimetres. It also retains the optional typed placement. An initial state with no body returns an empty tuple. `EmitStateSmb` rejects that empty state because its standalone-body profile requires a live root.

## Validation

The planar reader checks the complete ownership chain from body through lump, shell, face and loop. It verifies reciprocal loop links, coedge partners, exactly two oppositely directed uses per edge, incident vertex owners, and connected polygon endpoints. Every straight edge is evaluated at its declared endpoint parameters, including reversed curve sense, and checked against vertex positions and optional carrier bounds.

Face points must lie in their declared plane. Ring orientation must agree with the face's surface sense. Each face and the complete shell must be convex; the Euler characteristic must be two. Finite-result checks cover normal construction, carrier evaluation, placement and signed volume. These checks intentionally reject open sheets, holes, non-convex shells, multiple lumps or shells, curved boundaries and degenerate geometry. They do not silently flatten or approximate those shapes.

The underlying typed journal still preserves its full supported record values. The planar view is a qualified semantic interpretation, not a fallback for unknown records or an assertion that every wire-valid model is a valid solid.

## Transform semantics

A `TransformNode` has an attribute reference, entity tag, three basis columns, translation in centimetres and one scale factor. It also has three independent classification flags: rotation, reflection and shear. It has no third reserved reference between its entity tag and the first basis vector.
The flag names came from binary inspection and are not confirmed by a black-box experiment.

The placed tetrahedron confirms this mapping for one rotation, scale and translation:

`world = scale × (x × columnX + y × columnY + z × columnZ) + translationCm`

The scale applies to the matrix product before translation. The serializer retains the three classification flags independently; it does not regenerate them from matrix values. The planar view scales volume by the absolute determinant of the complete linear mapping and reverses output polygon winding when the determinant is negative. A singular or nonfinite placement is rejected by that view.

## Evidence and verification

[The two native controls](../../../../re/Fusion/Reconstruction/PlanarTopology/ControlSummary.json) are a four-face tetrahedron with volume 4 cm³ and a five-face triangular pipe with volume approximately 1.2470765814495919 cm³. Their complete histories have 54 and 74 active records respectively. Body tags are 30 and 0; state intervals are `2→4` and `2→3`. [Design joins](../../../../re/Fusion/Reconstruction/PlanarTopology/DesignStatesSummary.json) identify the mesh-conversion and pipe features and their real parameter bindings.

[Transform evidence](../../../../re/Fusion/Reconstruction/PlanarTopology/TransformEvidence.json) completely decodes 290 transform records from 208 distinct source blobs. All of those sampled transforms are identity placements. Binary inspection first gave the field order and the evaluation of nonidentity placements. That evidence was removed at the tip. The placed tetrahedron below confirms one nonidentity transform by a black-box experiment.

The acceptance preparation creates source-specific exact and permuted history replacements for both controls. It separately creates source-free tetrahedron and triangular-prism bodies with dimensions different from the controls. The preparation also creates a tetrahedron with a 90° Z rotation, scale 1.25 and translation `(11,-7,5)` mm. [Native acceptance](../../../../re/Fusion/LocalOracle/PlanarTopology/NativeAcceptance.json), SHA-256 `9974d4d3abb6305e21d3a843e8bbd19defbad1d4d49830de9b21fa4e95e0976d`, passed both source controls, all four exact/permuted history candidates and all three source-free bodies. [The preparation report](../../../../re/Fusion/LocalOracle/PlanarTopology/ProductionPreparation.json) binds every artifact to its input and output digests. Exact source-history outputs matched the original bytes; permutations changed them. All rollback markers, restore/rebuild and save/reopen observations matched the controls, including the pipe section edit from 6 to 8 mm. The standalone bodies reopened with volumes 2.0201666666666673, 4.5695 and 3.945638020833335 cm³, correct topology, analytic centroids and bounds. The placed tetrahedron reopened at centroid `(0.38125,-0.16875,1.46875)` cm and bounds `(-1.775,-0.7,0.5)..(1.1,1.425,4.375)` cm. Zero documents remained open. Preparation and native execution were separate from tests.

Eleven remote archive/process-boundary cases cover native complete histories, changed allocation, independently authored solids, a nonidentity transform and the empty initial state. The cases also cover inconsistent face winding, carrier origins, direction and singular placement. Black, Ruff, mypy, strict Pyright and repository steering checks passed the 164 production/integration modules in scope. No local tests ran.

See [the body-transform gotcha](../../../Gotchas/Conversion/Fusion/Geometry/FusionBodyTransforms.md). Complete document routing remains separate. The tetrahedron archive also has a parametric mesh part, and the pipe archive has a single-body snapshot that requires its own typed wrapper.
