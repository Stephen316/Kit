# Fusion saves body edges and faces in a second mesh stream family

## Expectation

The OGS default scene holds one `world` member and some `stream_mesh_NNN` members. The `world` member references the vertex and index buffers in `stream_mesh_NNN`.

## Actual behavior

Fusion can also write `Fusion_mesh_NNN` members in `OGS.BlobFolder/OGS/DefaultScene`. The native `MeshSerializer` names them with the format `Fusion_mesh_%03d`.

`ReadContainer` did not accept these members. It raised `ValueError("Missing directories or unaccounted Fusion container members")` for eight timeline study documents and `RolledHistoryReemitted.f3d`.

The members hold the vertex data of body display items. A body LOD node with display item type 6 or 7 holds `Props` words instead of a `RenderGeom` link. The words give a stream index and a byte offset in `Fusion_mesh_NNN`.

Both stream families start at index 000. The same index in the two families names two different members.

## Workaround

Read `Fusion_mesh_NNN` as a separate stream family. Do not merge it with `stream_mesh_NNN`. Write each family again from the typed display items. Reject a stream byte that no display item references.

## Evidence

- [Scene stream evidence](../../../../../re/Fusion/Reconstruction/ReaderCoverage/SceneStreams/SceneStreams.json)
- [Display item layout](SceneDisplayItems.md)
