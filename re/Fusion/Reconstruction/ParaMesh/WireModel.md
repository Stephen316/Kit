# Fusion mesh container field model

## Evidence and qualification

The [inventory](CorpusInventory.json) finds 103 `.paramesh` members in the indexed 712-archive corpus and no `.tsm` members. The independently written [research inspector](InspectContainers.py) consumes all 141,403 encoded member bytes, decompresses all 618 streams, and resolves 7,691 vertices and 14,935 triangles. [ContainerFields.json](ContainerFields.json) records source/member digests and counts and binds the [compressed complete field report](ContainerFields.json.xz) by SHA-256. The complete report preserves every registry, stream descriptor, decoded-stream digest and offset. It also resolves normal overrides, feature-edge topology and face-group memberships with zero inspection failures.

These are read-only corpus findings. This report itself establishes neither production execution nor native acceptance. A separately implemented typed component codec is described in the production change entry below. Coordinates are in each container's local frame; the owning Design entity's placement remains necessary to obtain model geometry. All samples use the same three descriptor shapes. Split components, textures and arbitrary attribute channels are not qualified by this corpus.

The initial comparison source is [cadmpeg revision de2726870ff728352163f601ab4e60bbd54fbade](https://github.com/cadmpeg/cadmpeg/tree/de2726870ff728352163f601ab4e60bbd54fbade), specifically `docs/formats/f3d.md` section 1.1.2 and `crates/cadmpeg-codec-f3d/src/paramesh.rs`. Attribution: cadmpeg; the specification is CC-BY-4.0 and the Rust source is Apache-2.0. The Python inspection code is independently written. Its complete corpus results, rather than upstream support claims, establish the local observations below.

## Container envelope

All multibyte envelope integers use little endian.

| Offset         | Type            | Meaning                                                   |
| -------------- | --------------- | --------------------------------------------------------- |
| 0              | 12 bytes        | `89 55 44 50 4d 45 53 48 0d 0a 1a 0a`, the mesh signature |
| 12             | uint32          | Container version 2                                       |
| 16             | 32 bytes        | Reserved, zero in every inspected sample                  |
| 48             | uint64          | Protobuf registry byte length                             |
| 56             | uint32          | Registry chunk kind 1                                     |
| 60             | Registry bytes  | Named roles, properties, identities and channels          |
| After registry | Repeated chunks | uint64 body length, uint32 kind, then the body            |

The first subsequent chunk has kind 3. Its MessagePack map binds stream names to integer stream identities. Remaining chunks have kind 4 and follow increasing stream identity. Literal names such as `v`, `t` and `r0` are not the source of semantic roles: the registry assigns those roles.

## Registry graph

The observed protobuf fields use wire type 0 for integers and wire type 2 for text and nested messages.

| Registry field | Meaning                                                                              |
| -------------- | ------------------------------------------------------------------------------------ |
| 4, repeated    | Vertex-domain attribute channel; an index stream makes it a corner-override channel  |
| 5, repeated    | Triangle-domain attribute channel                                                    |
| 7              | Feature-edge declaration; nested field 4 is its stream name                          |
| 8, repeated    | Named property: field 1 key, field 3 text value or field 4 stream reference          |
| 9              | Face-group-associated count; retain independently from the number of mapping entries |
| 12             | Container-local mesh UUID                                                            |
| 21             | Vertex-position stream name                                                          |
| 22             | Triangle-corner stream name                                                          |

Each channel has optional field 2 role, optional field 3 resource UUID, field 5 stream declaration, and repeated field 6 group mappings. A stream declaration contains field 1 element code, field 2 value-stream name and optional field 3 index-stream name. Each group mapping contains field 1 uint32 key and field 2 UUID. The observed optional role defaults to zero.

The `fusion_uuid` text property identifies the Design join. It differs from the entry-name UUID, container-local mesh UUID, channel resource UUID and face-group UUID. Those identities must remain separate even when one sample happens to share a value. The file is not joined to its Design body by ZIP order.

## Stream framing and compression

A nonsplit kind-4 body contains a uint16 descriptor length, a MessagePack descriptor map, uint32 decoded byte count, two encoding-selector bytes and encoded data. The three descriptor shapes observed are:

| Descriptor         | Logical interpretation                                                         | Observed count |
| ------------------ | ------------------------------------------------------------------------------ | -------------: |
| `{D:3,T:3}`        | Three float32 position components                                              |            103 |
| `{T:1,d:1}`        | uint32 words with terminal-delta semantics selected by the registry role       |            412 |
| `{D:3,T:3,U:true}` | Three-dimensional unit directions stored as two float32 octahedral coordinates |            103 |

`5d 14` selects LZMA1 with `lc=3`, `lp=0`, `pb=2`; `14` is the base-two dictionary exponent, giving a nominal 1 MiB dictionary. The stream has a declared output size. Reconstructing a standard LZMA-alone header as properties byte `5d`, a uint32 dictionary size and the uint64 declared output size permits exact termination. Every observed stream then reports end-of-stream and zero unused bytes.

The first research hypothesis treated these as unknown-length raw LZMA and requested one byte beyond the declared count to detect overflow. Eight valid members then appeared to expand by an extra byte. That hypothesis is refuted: known-length LZMA termination is part of the framing contract. The declared count is not merely a post-decompression assertion. The successful inspector uses the reconstructed known-length header and still rejects truncated or trailing input.

The upstream source additionally describes selector `5d fe` for literal bytes and split-component descriptors. They are explicit research branches but have no local sample coverage in the 103-member set.

## Geometry and topology

Positions are finite float32 triples. They are container-local coordinates and cannot be interpreted as millimetres or centimetres without the Design placement. Geometry bounds in the report are deliberately labelled `container_bounds`.

The corner stream contains one 32-bit word per triangle corner. All words except the last are signed two's-complement differences to the next corner. The final word does not continue that sequence. Accumulate the differences from a relative initial value zero; let the minimum and maximum be `m` and `M`. With `V` vertices, the implicit initial index must satisfy both `start=-m` and `start=V-1-M`. A mismatch means the stream does not identify a unique in-domain starting vertex. Group the reconstructed sequence into consecutive triples without sorting or reversing them. The final stored word is retained independently; it is not discarded as padding.

The other observed delta streams use a different rule: the final word is the absolute terminal uint32 value, and preceding words are signed differences. Therefore `first=terminal-sum(deltas)`. The reconstruction must remain inside uint32. A decoder must select this rule by semantic role, not merely by the shared descriptor.

## Normals and corner overrides

Element code 5 is an octahedral direction table. Each stored pair `(x,y)` lies in `[-1,1]²`. Compute `z=1-|x|-|y|`; if `z<0`, unfold the lower hemisphere by replacing the two planar components with their reflected signed values, then normalize the three-dimensional vector. Retaining the original float32 pair is necessary for exact representation; normalization is a derived semantic view.

The table starts with one default direction per vertex. A terminal-delta index stream identifies strictly increasing triangle-corner positions for all remaining table entries. Thus `table_count=vertex_count+override_count`. A triangle corner uses its vertex's default unless that exact corner position has an override. All 103 members satisfy those counts and reference bounds. Vertex index and triangle-corner ordinal are distinct domains.

## Feature edges and face groups

The feature-edge stream is a terminal-delta sequence of vertex endpoints. Pair adjacent values. Each pair is strictly ascending, unique, and an edge of at least one decoded triangle. These are source classifications, not all triangle edges, and cannot be regenerated by marking every triangulation edge sharp.

Element code 7 in a triangle channel provides one terminal-delta group key per triangle. Every key resolves through the same channel's uint32-to-UUID table. The table order, keys, UUIDs and membership remain distinct semantic fields. Registry field 9 must not be substituted for table length: the first inspected sample stores field 9 value 1 while mapping eight group keys. The inspection report records both rather than enforcing the incorrect equality.

## Typed production profile and remaining document work

A production writer must construct the envelope, typed registry, name table and every scalar stream from semantic fields, with bounded decompression and strict reference checks. It must preserve corner order, terminal words, normal-table representation, override addressing, feature-edge classifications and group identities. Complete native document conversion also requires the Design-to-container identity and placement joins, feature ownership and the associated graphics state. This report does not implement those obligations or claim native loadability.

The qualified component implementation is now `src/convert/formats/Fusion/MeshCodec`, documented in [FusionParaMeshCodec](../../../../Documentation/Changes/Fusion/Mesh/FusionParaMeshCodec.md). It models the three observed descriptors and all six roles without retaining encoded payloads. `PromoteMeshCases.py` reproducibly derives 103 complete semantic hashes and source digests from this independent inspector for remote archive compatibility. `PrepareMeshes.py` is a parent-executed native artifact generator; it replaces only the mesh components in their own controls. Neither script establishes full mesh-document authoring, and no tests or native calls are executed as part of this research promotion.


## Component-native acceptance

Fusion 2706.1.17 accepted five independently serialized components across the grouped-octahedron and hollow-tetrahedron controls. [The native report](../../LocalOracle/ParaMesh/NativeAcceptance.json), SHA-256 `2a4257fd81b657ca33456754dc6cee62da2e56ca178206edf70c6768d529626a`, records exact geometry-array/group digest comparisons, healthy history rollback and restoration, meaningful combine-group and shell-thickness edits, save and reopen. The complete observation archive is bound by SHA-256 `820a8f055753146857692183162f96dd237ac98b2f582c0b0a12a2a2091454a8`. Only the `.paramesh` members were independently emitted in these experiments; unchanged native control members supplied the enclosing document context.

The independent [join inventory](MeshJoins.json) now covers 103 geometry/trigger/component joins across 52 archives and 63 mesh bodies, with zero reciprocal-reference, member-inventory or `fusion_uuid` mismatches. Every original OGS world in these 52 controls is consumed by the ordinary-world research reader. See [DocumentIntegration](DocumentIntegration.md) for exact class GUIDs and the distinction between original ordinary worlds and saved native mesh-world callbacks.
