# Complete typed Fusion mesh document routing

`DocumentCodec.ReadDocument` and `EmitParsed` now include `DocumentModel.Meshes`, a final tuple defaulting to empty. Each immutable `DocumentMesh` contains an asset-relative `Name` and a typed `MeshCodec.Model.ParaMesh`. Existing positional model construction and authored document profiles retain their previous behavior through the empty default.

```python
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

model = ReadDocument(source_archive)
for part in model.Meshes:
    positions = part.Mesh.Positions
    triangle_corners = part.Mesh.Corners
rebuilt_archive = EmitParsed(model)
```

The container recognizes the `ParaMeshGeometry.BlobParts` folder. The document layer admits only `ParaMeshGeometry.<UUID>.paramesh` names there and reads/emits each part using the independent semantic mesh codec. No mesh payload or compressed block survives in `DocumentModel`. Design, ACT and Browser records retain their named entity values and exact feature/history fields. Materials, configurations and graphics use their existing typed codecs; preview images remain explicitly modeled image artifacts.

Every mesh geometry must own a local serializer trigger of the exact registered class. That trigger must point back to the same geometry and provide the exact component filename through its inherited blob field. The component's `fusion_uuid` must match `ParaMeshGeometry.pMeshUuid`. The container-local mesh UUID and filename UUID are separate identities. Geometry UUIDs, component names and trigger ownership must be unique, and every component and trigger must be accounted for. These checks run on both document input and emission. ParaMeshBody geometry references must resolve to a compatible primary Design entity.

All current and historical geometry records participate. A component retained by a preceding mesh feature is required even when the current body references a later geometry; this preserves rollback and recomputation. Body placement and baked-transform matrices remain exact fields in the typed entity graph. The component reader does not apply or conflate those two transforms. Nonempty mesh texture mappings and geometry marked as requiring an update reject explicitly until their full contracts are qualified.

[Independent graph inspection](../../../../re/Fusion/Reconstruction/ParaMesh/MeshJoins.json) resolved 103 reciprocal geometry/trigger/component joins across 52 archives and 63 bodies without errors. Every original OGS world in that set is fully consumed under the already qualified ordinary-world profile. A raw metadata comparison found no additional ACT/Browser class or version differences across all 104 auxiliary segments. [DocumentIntegration.md](../../../../re/Fusion/Reconstruction/ParaMesh/DocumentIntegration.md) records the exact class GUIDs, identity domains and source-linked examples.

Remote archive integration coverage reconstructs all 52 complete documents, compares their full typed models and checks exact re-emission of entity and graphics streams. Six additional file-boundary cases exercise a missing historical component, an incorrect component UUID and an orphan component. The cases also exercise broken trigger reciprocity, a null body geometry link and stale geometry. The fixture builders keep ZIP framing, metadata and bulk offsets consistent so rejection reaches the intended semantic boundary. No tests run locally. Black, Ruff, MyPy, Pyright and repository steering checks passed for all 22 changed production/test Python modules.

The [component codec](FusionParaMeshCodec.md) and the complete document route now have distinct native acceptance. [Complete preparation](../../../../re/Fusion/LocalOracle/MeshDocuments/Preparation.json) records archives `d0acf4a696b7349153ddeffed90d10ddb574d8a949eded38459320aea11c6b73` and `1a74e49c91ae393247e61b4f8af9ef00f2c0fb19eaea16c92b5d8f5bcc6012e7`. They contain 337 and 311 entity records, three and two historical mesh parts, one material package, two configuration sidecars and 39 graphics objects each. Every semantic member passes through its production codec; preview images remain explicit assets.

[Native whole-document acceptance](../../../../re/Fusion/LocalOracle/MeshDocuments/NativeAcceptance.json), report SHA-256 `9bd545054849e9b72a80e0edd9cbae386b1942fcdac146432fb72876aa2c9113`, passed both controls and reconstructions through load, rollback, restoration/rebuild, meaningful feature edit and save/reopen. The combine feature changes from seven groups to eight on rollback and one after editing its selection. The shell changes thickness from 1 to 1.5 mm, producing 2,307 vertices, 4,606 triangles and volume 2.4168816259885424 cm³. Every observed geometry, normal, corner and group digest, physical measure, parameter and feature/timeline state matches its control. Complete numerical observations are retained in the adjacent compressed report. Zero documents remained open.

The ordinary graphics branch is supported. Four native-saved mesh controls also contain this complete ordinary world; [the inspection](../../../../re/Fusion/Reconstruction/ParaMesh/SavedWorlds.json) does not establish the separately identified custom mesh-world callback. The strict public neutral adapter still rejects meshes even though this lower-level document API supports them.

See [historical mesh ownership](../../../Gotchas/Conversion/Fusion/Mesh/HistoricalMeshParts.md).
