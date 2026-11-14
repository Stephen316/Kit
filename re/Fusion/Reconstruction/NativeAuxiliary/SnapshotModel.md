# Native snapshots and configuration sidecars

## Evidence boundary

`Inventory.json` records three complete native archives and every ZIP member, hash, compression method and size. `SnapshotTokens.json.xz` contains the complete raw research token inventory; its compressed SHA-256 is `3f27f34a17b22ffc6db559cd7d38bf1a0ee9dc805a83e49177f72c449b3e2d22`. Production code does not read these files or retain raw token arrays.

The ordinary rectangle control and Fusion-saved independently authored cuboid each have one 16,557-byte snapshot with the same topology grammar and different dimensions, carrier values, identities and provenance. Both carry 168 entities followed by `End-of-ASM-data`. The cylinder control has the separately qualified 59-entity profile.

## Header and roots

The qualified binary prefix is `ASM BinaryFile8`, version 23200, stored count 0, root count 4 and flags 2. Three counted provenance strings precede units 10, tolerance 1e-6 and angular tolerance 1e-10. Four roots mean one ASM header and three bodies, not four bodies. All three snapshot bodies have key -1 and no body attribute chain.

The three bodies have different roles: solved solid, double-sided planar profile and single-sided sketch sheet. Neither planar region is a second solid or a historical revision. Snapshot files have no insertion journal. Complete historical operations and solved-body identities remain in `.smbh` and Design.

## Cuboid topology and allocation

The serializer allocates canonical entity IDs independently of the native breadth-first allocation. Reference fields are remapped through their typed entity roles; no original allocation table or payload is replayed.

| Canonical IDs | Semantic role | Count |
| --- | --- | ---: |
| 0 | ASM header | 1 |
| 1–3 | Solid, profile and sketch body roots | 3 |
| 4–87 | Solid-owned topology and carriers | 84 |
| 88–112 | Profile-owned topology and carriers | 25 |
| 113–137 | Sketch-owned topology and carriers | 25 |
| 138–143 | Solid face generic tags | 6 |
| 144–151 | Paired bottom-edge coedge sketch links | 8 |
| 152–159 | Profile coedge and edge sketch links | 8 |
| 160–167 | Sketch coedge and edge sketch links | 8 |

The 84 solid-owned records comprise one lump, one shell, six faces, six loops, 24 coedges, 12 edges, six planes, eight vertices, 12 straight curves and eight points. The complete snapshot has three bodies, three lumps, three shells, eight faces, eight loops, 32 coedges, 20 edges, eight planes, 16 vertices, 20 straight curves, 16 points, 30 custom attributes and one ASM header.

A history profile has two additional body attributes: timestamp and generic body identity. Those are absent from the snapshot. The snapshot still has all six face identity tags and eight source-coedge sketch attributes. Generic tag byte length is derived from the primary ASCII identity; secondary, operation and approach identities retain their signed integer semantics. Sketch attributes retain the six unsigned decimal fields and qualified zero topology flags.

## Typed solid and planar regions

`PrismSnapshot` contains a dimensional `CuboidBody`, complete `PrismFrame`, `PrismTags`, provenance and header plus separate `RegionFrame` values for the profile and sketch.

The solid frame retains eight actual centimeter corner coordinates, face chain order, face loop starts, face sense flags, 12 edge orientations and parameter intervals, vertex-owner edges, plane origins/normals/bases, and line origins/directions/bounds. Dimensions are derived from opposite corners and validated against every corner. Stored carrier fields are not normalized: direction scale and parameter range are coupled.

Each region has four corners in loop order, four forward edge/coedge pairs, four explicit vertex owner-edge indices, one planar frame, four coedge sketch links and four separate edge sketch links. Each edge retains both topological parameter limits and its straight-curve bounds. Corner order may differ from the solid's canonical bit-coordinate order. Region vertices must form the same rectangular bottom footprint; diagonals, duplicate corners, nonincident owners, unbounded scalar values and mismatched carrier endpoints are rejected.

The region plane has +Z normal, forward parameterization, a nonzero perpendicular basis and origin on the bottom plane. The profile face is double-sided with its explicit trailing false sense flag. The sketch face is single-sided and has no extra flag. Both use a single loop and four forward coedges with null partners. The observed curve and coedge direction tags are preserved explicitly; no inversion is guessed from arbitrary attribute values.

For each region, the 25 owned records are lump, shell, face, loop, plane, four coedges, four edges, four vertices, four curves and four points. Native vertex owner index 0 identifies an edge's start and 1 its end; regenerated values are derived from the explicit incident owner and loop order.

## Reader completeness

The reader bounds the payload at 2 MiB, reads exactly 168 entities, requires the exact qualified header and final marker, and requires EOF. It traverses solid and region ownership, constructs a bijection between all canonical and actual records, and validates every regenerated token, token discriminator, field count and entity reference against the input. This covers reserved fields, empty attribute links, fixed flags, text payloads and all topology references. Unsupported layouts fail instead of entering a generic retained-record fallback.

The emitted snapshot preserves typed semantics and header data. Its entity allocation and bytes can differ from the native input. Archive member order and compression are container responsibilities, not snapshot semantics.

## Empty configuration profile

The inspected archives each contain exactly two configuration members under `DesignConfigurationTable.BlobParts`: `DesignConfigurationTable.<UUID>.dsgcfg` and `DesignConfigurationRule.<UUID>.dsgcfgrule`. Both contain the JSON object `{}`. The model stores the validated canonical UUID-bearing part name and table/rule role; the only qualified content is the empty object.

Document validation resolves both configuration serializer triggers in Design to their exact sidecar names. Duplicate/missing parts, role mismatches, malformed JSON and nonempty configuration objects are rejected. This does not implement populated configuration tables or rules.

## Native acceptance preparation

`re/Fusion/LocalOracle/PreparePrismSnapshots.py` generated two source-specific archives using production `ReadSnapPart` and `EmitSnapPart`. `re/Fusion/LocalOracle/PrismSnapshot/Preparation.json` records hashes, dimensions, complete typed frames and expected parameter edits. Only `.smb` is replaced; every other member remains that same source's own member, including graphics. This is snapshot qualification, not independent full-document authoring or full-archive decoding.

The ordinary rectangle target is 40 × 30 × 25 mm with `d1` changing to 37 mm. Expected volume is 30 → 44.4 cm³. The saved cuboid target is 17 × 23 × 37 mm with `authoredLength` changing to 43 mm. Expected volume is 14.467 → 16.813 cm³. Native acceptance completed successfully in Fusion 2706.1.17: both candidates opened with the correct body/profile and healthy timeline, rolled back to zero bodies, restored/rebuilt, accepted the stated height edits, saved and reopened with six faces, 12 edges and eight vertices. The final document count was zero. Evidence: `re/Fusion/LocalOracle/PrismSnapshot/NativeAcceptance.json`, SHA-256 `2b1407635e513c354356e2497086a5ae3d93b7e9faf495705f35c2cf268ba993`. This proves complete snapshot replacement within each same-source archive, not interpretation or reserialization of its retained graphics.

## Remaining complete-archive gap

Nested `OGS.BlobFolder/OGS/DefaultScene/world` and mesh streams are not opaque snapshot fields. They have separate custom serializers being mapped under `re/Fusion/Reconstruction/OgsScene`. The document container continues to reject unsupported nested graphics. Removing them, retaining their raw bytes in a semantic model, or claiming complete native-source conversion would exceed the current qualification.
