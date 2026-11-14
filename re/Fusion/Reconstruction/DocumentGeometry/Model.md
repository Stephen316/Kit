# Complete document geometry states

## Scope and evidence

This extension composes the existing named-field journal and geometry models with the complete F3D document reader and writer. It does not retain raw BRep payloads or add an unparsed fallback. The read-only `InspectGeometry.py` inventory covers nine native archives and fourteen geometry members. `Tokens.json.xz` contains their complete decoded wire records; `TokenIndex.json` binds that evidence by SHA-256. `Inventory.json` records exact source/member identities, root counts, geometry inventories, boundary coedges and history frames.

The native mesh conversion controls distinguish three independent properties:

| Control | Current history records | Snapshot records | Body roots | Boundary coedges |
| --- | ---: | ---: | ---: | ---: |
| Base feature, closed tetrahedron | 54 | 52 | 1 | 0 |
| Base feature, open tetrahedron | 53 | 51 | 1 | 3 |
| Two converted tetrahedra | 107 | absent | 2 | 0 |
| Parametric closed tetrahedron | 54 | absent | 1 | 0 |
| Parametric open tetrahedron | 47 | absent | 1 | 3 |
| Triangular pipe | 74 | 72 | 1 | 0 |

Each binary header counts the ASM header in addition to body roots. Thus the two-body conversion has root count three, with both bodies in the same entity table and the same complete insertion journal. The reader validates the declared root count against the actual active BodyNode inventory; root count is not an assumed profile identifier.

The open tetrahedron's three boundary coedges have null partner references. Their next/prior links still form closed face-loop rings, their owning edges identify incident coedges, and all remaining interior edges have two reciprocal partners. Faces use the same single-sided record flags as the closed tetrahedron. The single-sided flag does not prove shell closure.

Base feature open geometry also has generic feature tags on three vertices. History attributes 42, 47 and 49 own vertices 31, 35 and 38; corresponding snapshot attributes 40, 45 and 47 own vertices 29, 33 and 36. These are existing generic-tag fields, not a new attribute encoding. Only `generic_tag_attrib_def` receives the newly proved vertex target class; timestamp, sketch and tracking attributes retain their earlier allowed classes.

## Current geometry without a journal

`GeometryState` stores a typed BrepHeader, GeometryStamp and immutable tuple of semantic entity values. Geometry scalars retain the journal models' explicit centimetre field roles. Header units remain ten, flags two and version 23200. The reader consumes the complete stream through End-of-ASM-data and requires EOF.

Native circle-only snapshots have fourteen records, one body, one plane face and one closed elliptical boundary use without a partner. There is no wire entity. Native circular extrusion snapshots have 59 records and three bodies: the solid, double-sided planar profile and single-sided sketch sheet. A frustum uses the same topology inventory with a nonzero cone sine. Its upper and lower rims, normals, directions, parameter ranges and face flags remain individually typed values; they are not replaced with cylinder geometry.

The serializer supports the existing plane, cone, ellipse and straight carrier families, topology records, transforms and four custom attribute families. Null partners are legal exactly for an edge used by one coedge. Two-use edges require reciprocal partners and matching edge ownership. More than two uses remain unsupported. Next/prior loop links must be reciprocal and remain in their declared loop. Every non-null reference resolves to a live compatible record class.

Physical allocation permutations preserve the relative serialized order of body roots. Snapshot body tags can all be -1, and an external Design body-map association must not be assumed independent of that root order. Non-root entities and their references may be freely remapped within the qualified table.

Multiple body roots do not change reference namespaces. Physical record ordinals address the shared geometry table; snapshot body tags may be -1. History entity tags and allocator limits remain separate from physical allocation, body-root count, Design identities and delta-state node ordinals.

## Document dispatch

ReadDocument reads every history through the full typed journal reader before choosing a view. Existing cylinder, cuboid and frustum views require a two-state insertion history with no archived table, the exact supported stream/state framing and the declared analytic entity inventory. General planar bodies, multiple-body histories and histories with archived revisions remain JournalModel. Geometry count alone never discards a journal section. An analytic reader failure remains an error; it is not caught and replaced with a permissive representation.

Snapshot dispatch first reads the complete typed current geometry. Previously supported cylinder and rectangular profile models retain their existing views. Single-body geometry and mixed conical snapshots expose GeometryState. EmitParsed writes each selected immutable model through its complete serializer. Strict container member routing, typed configuration, material, graphics and parametric mesh joins remain active.

Serialization qualification does not imply closed-solid geometry qualification. ReadPlanarState continues to require a closed convex shell with reciprocal paired uses, planar single-loop faces and positive volume. Open sheets can be preserved by the geometry serializer without receiving an invented volume or closed-body classification. Wire bodies, spline/pcurve/tolerant records, sphere/torus carriers, nonmanifold edges and branched journals remain outside this extension.

## Verification boundary

Static Black, Ruff, mypy, strict Pyright and repository steering checks passed the expanded production/document/integration scope. No local tests ran. The new archive cases exercise exact and permuted geometry, open boundaries, multiple body roots, three-state journal dispatch, complete pipe/circle/frustum documents and malformed incidence. Existing full mesh document cases remain unchanged.

`PrepareProduction.py` prepares complete ReadDocument → EmitParsed archives for the native application. It never copies selected source archive members into a new archive. Its report records source/output hashes, model selections, entity counts and changed member hashes. Native execution was coordinated separately by the parent agent. The six complete document controls and re-emissions passed initial open, all rollback markers, restore/rebuild and save/reopen. The pipe edit d3=6→8 mm also matched. `../../LocalOracle/DocumentGeometry/NativeAcceptance.json` has SHA-256 `58ca80b5234e03ce15b9c7a2127d9491084a25c47529d0a69b698469503d5692`; `Preparation.json` has SHA-256 `052805bc32c4c87b7ce1c7d1ec7dbc25399e523ff8ec93cb5ec504149d04d6dc`. The application had zero documents open afterward. The native volume accessor raises for the original open-sheet controls. The driver leaves volume and solid-center observations absent for both controls and outputs, comparing area, topology, vertices and bounds instead. This result does not qualify the three rotational complete documents, which require additional graphics classes beyond the six accepted cases.
