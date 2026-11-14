# Independent Three-Body Fusion Snapshot

## Scope

This experiment regenerates the entire snapshot BRep member `BREP.6b7f67e0-2eb6-4db1-9a3c-b5d54f9a9fe5.smb` for the controlled circular extrusion. It derives all topology, geometry, source-link attributes and framing from semantic cylinder/circle inputs. It does not read the original snapshot or any recorded payload while generating the output.

The native snapshot has three bodies, not just a stale copy of the physical result. The first is the solid extrusion tool body. The second is a double-sided planar sketch region. The third is a single-sided planar sketch/profile body. All three are regenerated and retained in their original top-level order so that the enclosing Design passive-ID machinery can still select them.

The accepted native experiment replaces both embedded geometry members: this complete new snapshot `.smb` and the previously accepted independently generated 19 mm solved/history `.smbh`. All Design records are reconstructed from typed fields, and OGS graphics caches are omitted. The surrounding editable same-source Design identities and remaining source envelope remain necessary. This is a complete rewrite of the controlled document's embedded BRep members, not independent full-document F3D generation.

## Source and attribution

The grammar work adapts the [cadmpeg ASM specification](https://github.com/cadmpeg/cadmpeg/blob/de2726870ff728352163f601ab4e60bbd54fbade/docs/formats/asm.md) and [Fusion carrier specification](https://github.com/cadmpeg/cadmpeg/blob/de2726870ff728352163f601ab4e60bbd54fbade/docs/formats/f3d.md), pinned at commit `de2726870ff728352163f601ab4e60bbd54fbade`. These specifications are CC-BY-4.0, attributed to the cadmpeg project. The independent code here uses locally reconstructed semantic record builders and typed token serialization; it contains no copied upstream serializer or vendor payload.

Native observations come from `LocalOracle/Features/extrude_07mm.f3d`, its reflected `extrude_07mm.entities.json`, and the earlier complete token framing in `LocalOracle/Brep/extrude_07mm.tokens.json`. `DesignBindings.json` records the relevant reflected Design entities as analysis evidence. Those analysis files are not generation inputs.

## Snapshot ownership differs from the solved body map

The native Design snapshot serializer is record 24, type `Ns::BREP::BRepSerializer`. It stores:

| Field | Native value |
|---|---|
| `partName` | `BREP.6b7f67e0-2eb6-4db1-9a3c-b5d54f9a9fe5.smb` |
| `mapBodyId` | Empty |
| `rBodies` | Design body collection 22 |
| `rTopEntityPIDGenerator` | Design record 25 |

Collection 22 has no visible child bodies and links back to serializer 24. This snapshot should not add three physical model bodies to the document's current output. The separate modern history serializer 8 maps ASM body key 0 to the one physical Design body 261 in the `.smbh` stream.

The snapshot's body records all have integer body key `-1`. Their identity therefore cannot be reconstructed by pretending they use the modern solved-body key map. Record 25 is a top-entity passive-ID generator with three saved top-entity addresses, `scanOrderIndex = [5, 4, 3]` and `nextId = 6`.

The reflected cache users provide two independently visible joins:

| Cache record | Passive identity | Owning Design object | Role |
|---:|---:|---|---|
| 280 | 5 | `DcExtrudeToolBody` record 249 through `toolbodyCaches` | Extrusion tool solid |
| 278 | 4 | `SketchRegionRef` record 239 through `caches` | Selected sketch region |

Both caches carry the same scope entity identifier `77dc8960-634d-4445-a9d9-c411a1579607`. The ordered snapshot roots are kept as cylinder, double-sided planar region, single-sided planar body, corresponding to the saved scan sequence 5, 4, 3. This ordering was inferred from the reflected generator, native body roles and cache owners. Native replacement now confirms that this independent reallocation supports healthy feature load, rollback to sketch-only state, restoration, later edit/rebuild and save/reopen. No reflected cache consumer of passive ID 3 was identified in the selected control, so its higher-level purpose remains bounded to the observed single-sided sketch/profile body.

## Complete snapshot wire model

The header is `ASM BinaryFile8` followed by signed little-endian 64-bit words `23200, 0, 4, 2`. The root count 4 includes `asmheader` and the three body roots. The zero record-count word is the native unwritten-count convention. Flags 2 declare revision 1 with the observed no-history profile.

Three counted header strings carry explicit `Kit` provenance. Binary scale metadata is 10, absolute tolerance is `1e-6` and normal tolerance is `1e-10`. All model-space lengths encode in centimetres. Direction/reference vectors, ratios, angles and topology references do not take the length conversion.

The generated stream has the same full class inventory as the native snapshot:

| Class | Count |
|---|---:|
| asmheader | 1 |
| body, lump, shell | 3 each |
| face | 5 |
| loop, coedge | 6 each |
| edge, vertex, ellipse-curve, point, plane-surface | 4 each |
| cone-surface | 1 |
| ATTRIB_CUSTOM-attrib | 11 |

There are 59 active records. The final `End-of-ASM-data` name chain ends at EOF without a terminator. There is no history preamble, delta state or archived revision section in this snapshot member.

## Fresh allocation

The serializer deliberately uses a different allocation below the preserved top-level roots:

| Records | Responsibility |
|---|---|
| 0 | ASM schema header |
| 1 | Cylinder body root |
| 2 | Double-sided region body root |
| 3 | Single-sided planar body root |
| 4–27 | Independently authored cylinder topology and carriers |
| 28–37 | Double-sided region lump, shell, face, loop, coedge, edge, vertex, circle, plane and point |
| 38–47 | Single-sided planar body with the same ten-record structure |
| 48–58 | Explicit operation and sketch source-link attributes |

The cylinder's previously accepted semantic topology is remapped by reserving two additional body roots before its owned records. Every nonnegative topology reference at or above its original owned-record boundary is recomputed from that allocation. This remapping operates on semantic `Reference` values, not byte offsets or recorded blocks.

## Planar profile geometry

Each planar body has one lump, one shell, one face and one loop. The loop contains one coedge whose next and previous links point to itself. Its partner is null because it bounds one planar sheet region rather than joining two faces of a closed solid.

The coedge uses a full-circle edge. Start and end references name the same vertex, with parameters `-pi` and `pi`. The edge references an `ellipse-curve` with ratio 1, the semantic circle center, positive Z normal and positive X radius vector. The vertex references a point obtained by evaluating that circle at `-pi`.

The face references a plane at the circle center with normal `(0, 0, 1)` and a dimensionless unit X parameter reference. Its face sense and coedge sense are forward. Both circle and plane carriers have absent optional bounds, encoded as false tokens.

The two planar faces differ structurally in sidedness. The double-sided face has a true sidedness token and an additional false containment token. The single-sided face has a false sidedness token and no containment field. Treating both as fixed ten-field faces would lose one byte from the double-sided record and desynchronize the stream.

The semantic profile requires the sketch circle to coincide with the cylinder's base circle: same center and radius, positive Z cylinder axis. The generator rejects noncoincident input rather than fabricating a source-feature relationship.

## Attribute identities

The snapshot contains no timestamp or generic body identity attributes. Its body keys remain `-1`, as in the native snapshot. The cylinder retains five operation-tag attributes and two sketch-source links:

| New attribute record | New owner | Explicit semantic identity |
|---:|---:|---|
| 48 | Side face 6 | Selector 1, label `3`, operation 301 |
| 49 | Top face 7 | Selector 1, label `2`, operation 301 |
| 50 | Bottom face 8 | Selector 1, label `1`, operation 301 |
| 51 | Top edge 17 | Selector 2, label `-1`, operation 301 |
| 52 | Bottom edge 18 | Selector 4, label `-102`, operation 301 |
| 53 | Cylinder bottom-side coedge 14 | Sketch identity `(102, 0)`, sense 0 |
| 54 | Cylinder bottom-cap coedge 16 | Sketch identity `(102, 0)`, sense 0 |
| 55 | Double-region coedge 32 | Sketch identity `(102, 0)`, sense 0 |
| 56 | Double-region edge 33 | Sketch identity `(102, 0)`, sense 1 |
| 57 | Single-region coedge 42 | Sketch identity `(102, 0)`, sense 0 |
| 58 | Single-region edge 43 | Sketch identity `(102, 0)`, sense 1 |

Each operation group and sketch tuple is emitted from typed inputs using the previously derived attribute grammar. The edge's sketch-source sense is opposite its region coedge's source sense in this bounded profile. All enum pairs are explicitly `(1, 1)`. Negative operation labels are counted strings, not kernel null pointers.

## Generated artifact and framing evidence

`IndependentNineteen.smb` is 6,025 bytes with SHA-256 `a8318f6f44b5f5a1282f5d2ac1e5b92896c21565a2f0cc52b34d2e42f58eec4b`. Its cylinder radius is 10 mm and height is 19 mm; both planar bodies remain at Z=0 with radius 10 mm.

The companion derivation report names every field's origin. The token report accounts for all emitted bytes and reencodes them identically from typed tokens. The semantic report recovers all 59 records, all 11 attributes and only in-range initial references. These full reports are packaged in [SnapshotEvidence.tar.xz](SnapshotEvidence.tar.xz), with archive/member byte sizes and SHA-256 digests in [SnapshotEvidence.json](SnapshotEvidence.json). Their raw JSON forms remain locally regenerable and ignored by Git to avoid large pretty-printed evidence diffs. The explicit wire analysis and native acceptance are separate evidence layers.

`GenerateSnapshot.py` reads only `SnapshotNineteen.json` as semantic input. Shared imports are pure record builders and token encoders under reconstruction tooling. There are no source-file lookups, compressed templates, copied entity blocks or opaque suffixes in generation.

## Reproduction

```sh
uv run --python 3.14 --no-project python re/Fusion/Reconstruction/SnapshotAuthoring/GenerateSnapshot.py re/Fusion/Reconstruction/SnapshotAuthoring/SnapshotNineteen.json re/Fusion/Reconstruction/SnapshotAuthoring/IndependentNineteen.smb
uv run --python 3.14 --no-project python re/Fusion/Reconstruction/BrepTokens.py re/Fusion/Reconstruction/SnapshotAuthoring/IndependentNineteen.smb re/Fusion/Reconstruction/SnapshotAuthoring/IndependentNineteen.tokens.json
uv run --python 3.14 --no-project python re/Fusion/Reconstruction/BrepModel.py re/Fusion/Reconstruction/SnapshotAuthoring/IndependentNineteen.tokens.json re/Fusion/Reconstruction/SnapshotAuthoring/IndependentNineteen.semantic.json
```

No local test suite or CAD runtime is invoked by these generation and analysis commands. The parent owns native import/rebuild/save/reopen acceptance and surrounding archive assembly.

## Native acceptance chain

The [rewrite report](../../LocalOracle/Features/FullBrepRewrite.json) binds snapshot SHA-256 `a8318f6f44b5f5a1282f5d2ac1e5b92896c21565a2f0cc52b34d2e42f58eec4b` to archive SHA-256 `7a67ce6bd8592af0a14966d7f8bf877663dd0d35e1971afc5b9335575620563a`. This archive contains the independently generated solved/history stream as well. Its source envelope was `kit_cacheless_19mm.f3d`, SHA-256 `23b01576ce5eaf635eeabb76bcce520d5c57777bfdd00e7dec496578e9c66bfa`.

The [native acceptance report](../../LocalOracle/Features/FullBrepAcceptance.json), from Fusion 2706.1.17, records:

| Stage | Bodies | Height, cm | Volume, cm³ | Timeline health |
|---|---:|---:|---:|---|
| Initial open | 1 | 1.9 | 5.969026041820864 | Both nodes healthy, no messages |
| Rollback to sketch-only state | 0 | — | — | Both nodes healthy |
| Timeline restoration | 1 | 1.9 | 5.969026041820864 | Both nodes healthy |
| Explicit rebuild | 1 | 1.9000000000000001 | 5.969026041820864 | Both nodes healthy |
| Edit depth to 23 mm and rebuild | 1 | 2.3000000000000003 | 7.225663103256217 | Both nodes healthy |
| Save and reopen | 1 | 2.3000000000000003 | 7.225663103256217 | Both nodes healthy |

Every observed solid has three faces, two edges and two vertices. The timeline preserves sketch `Radius10mm` and extrusion `Kit ControlledExtrusion`. Parameter `depthLength` drives dependent `d2`; `d3` remains a zero-degree taper. The native saved archive hash is `16ec3ba2d6e7f012be41a9fa1c21f714d6af3acc21eae64443aca7fc4597e53b`, and the report records zero remaining documents after cleanup.

The rollback/restoration sequence is the evidence that replacing the entire snapshot did not merely preserve the final visible solid while breaking the selected sketch-region or extrusion-tool cache path. It does not resolve arbitrary snapshot families or establish fully source-independent document assembly. [AcceptanceBinding.json](AcceptanceBinding.json) records the exact geometry/archive/native-report chain.
