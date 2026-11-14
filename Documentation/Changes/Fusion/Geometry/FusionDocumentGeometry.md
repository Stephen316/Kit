# Complete typed document geometry

`ReadDocument` and `EmitParsed` now compose the complete typed BRep journal with current geometry snapshots. Supported documents can contain open planar sheets, multiple body roots, general planar solids and multi-state history with archived revisions. Existing strict parsing for configuration, graphics, materials and parametric meshes remains active; unknown member and entity kinds still fail.

## Models and APIs

`DocumentBody.History` adds `JournalModel` alongside the existing cylinder, cuboid and frustum models. The reader parses the entire journal before selecting an analytic view. Those views require a complete two-state insertion profile and the supported analytic entity inventory. Histories with archived geometry, additional states or general topology retain their typed entities, identities, allocator, bulletin boards and state graph. No parser exception is used to choose a fallback.

`DocumentSnap.Snapshot` adds `GeometryState`. Its public functions live under `BrepCodec.Journal.Snapshot`:

| API               | Behavior                                                                                  |
| ----------------- | ----------------------------------------------------------------------------------------- |
| `ReadGeometry`    | Reads a complete BinaryFile8 current geometry stream into named typed fields              |
| `EmitGeometry`    | Derives every header, entity and termination byte from GeometryState                      |
| `PermuteGeometry` | Changes physical record allocation and remaps references while preserving body-root order |

`GeometryState` contains a header, provenance stamp and immutable semantic entity tuple. Positions and carrier dimensions explicitly use centimetres; direction vectors and parameter scales keep their distinct meanings. No original BRep bytes, token list, raw record or unknown field is retained. Existing circular and rectangular snapshot views remain available; single-body snapshots and mixed conical snapshots use the general typed model.

The header root count is validated against the number of body records plus the ASM header. One to 128 active bodies are bounded by the existing 1,024-record and 2 MiB quotas. Journals retain their existing linear-state, board, field and integer limits. The current geometry header uses unit metadata ten and no history; the journal header uses fifty and a complete history section.

## Boundaries and validation

An edge with one incident coedge has a null partner. An edge with two uses requires reciprocal partners. Both forms require an incident owning coedge and reciprocal next/prior links within their face loop. Edges with more than two uses are rejected. Null partners no longer incorrectly reject valid open sheets; removing a partner from a two-use edge remains an error.

Generic feature attributes may own vertices as well as the previously qualified topology classes. This is specifically proved by the native open base-feature control; other attribute-family target rules remain unchanged.

Serialization does not classify every preserved body as a closed solid. `ReadPlanarState` retains its stricter convex closed-shell qualification. Wire bodies, unknown carriers, pcurves, tolerant topology, nonmanifold edge uses and branched/merged journals remain unsupported. The public project adapter separately decides which document feature graphs it can project; adding typed document models does not silently register broader adapter support.

## Evidence and verification

`re/Fusion/Reconstruction/DocumentGeometry/PrepareProduction.py --only BaseClosed BaseOpen TwoBodies FacetedClosed FacetedOpen TriangularPipe` regenerates the six acceptance candidates. `--output <repository-relative-directory>` selects a separate preparation directory for further controls so accepted evidence is not overwritten.

The [field model](../../../../re/Fusion/Reconstruction/DocumentGeometry/Model.md), [native member inventory](../../../../re/Fusion/Reconstruction/DocumentGeometry/Inventory.json) and [compressed evidence index](../../../../re/Fusion/Reconstruction/DocumentGeometry/TokenIndex.json) cover closed/open mesh conversions, two converted bodies, a triangular pipe and native circular/conical snapshots. The open tetrahedron has three boundary uses. The two-body conversion has 107 current history records and root count three. A native circle-only snapshot has fourteen records; a conical extrusion snapshot has 59 records and three bodies.

Twenty-six new archive integration cases cover exact/permuted current geometry, a selected transformed history state exported as geometry and malformed framing/incidence. The cases also cover general and multi-state document history dispatch, and complete pipe/circle/frustum documents. Existing full mesh archive cases remain unchanged. Black, Ruff, mypy, strict Pyright and repository steering checks passed all 405 Python files in the expanded production/document/integration scope. No local tests ran.

[Complete native document acceptance](../../../../re/Fusion/LocalOracle/DocumentGeometry/NativeAcceptance.json), SHA-256 `58ca80b5234e03ce15b9c7a2127d9491084a25c47529d0a69b698469503d5692`, passed all six controls and six complete typed re-emissions in Fusion 2706.1.17. [Preparation.json](../../../../re/Fusion/LocalOracle/DocumentGeometry/Preparation.json), SHA-256 `052805bc32c4c87b7ce1c7d1ec7dbc25399e523ff8ec93cb5ec504149d04d6dc`, binds all source/output archives and member comparisons. All BRep history and snapshot members reconstructed exactly; material and parametric mesh members were emitted through their typed codecs. Native observations matched at initial open, every timeline rollback marker, restoration/rebuild and save/reopen. The triangular pipe's `d3` edit from 6 to 8 mm changed volume from 1.2470765814495923 to 2.2170250336881643 cm³ in both control and re-emission. Closed tetrahedra retained volume 4 cm³ and topology 4 faces/6 edges/4 vertices. Open tetrahedra retained 3 faces/6 edges/4 vertices, area 13 cm², vertex positions and bounds. Two-body geometry retained both independently identified tetrahedra. Zero native documents remained open.

Requesting BRep volume from the original open-sheet control raises in the native API. The acceptance driver records solid volume and solid-center observations as absent, and compares area, topology, vertices and bounds instead. This does not invent a closed volume or mass center. Native circle/cylinder/frustum whole-document acceptance is not established by this six-case result. Their current geometry has separate typed archive coverage, and additional graphics classes are being qualified separately.

See [the boundary and root-count gotcha](../../../Gotchas/Conversion/Fusion/Geometry/FusionBoundaryUses.md).
