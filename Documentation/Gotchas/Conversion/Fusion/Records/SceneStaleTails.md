# Some saved mesh streams keep bytes that the world does not reference

## Expectation

The `world` member references every byte of each `stream_mesh_NNN` and `Fusion_mesh_NNN` member.

## Actual behavior

Two documents in `re/Fusion/examples/.f3z/example1.f3z` hold mesh data after the last referenced span. The copy in `re/Fusion/LocalOracle/Bundles` is the same. Member numbers follow `ReadBundle` order, as in the read gap sweep.

| Document | Stream | Spans | Referenced bytes | Member bytes |
| --- | --- | --- | --- | --- |
| Member 6 | `Fusion_mesh_000` | 293 | 64,048 | 128,096 |
| Member 8 | `stream_mesh_000` | 267 | 35,460 | 91,620 |
| Member 8 | `Fusion_mesh_000` | 121 | 57,680 | 706,104 |

In each stream the spans start at offset 0 and leave no gap. Only the tail after the last span is unreferenced. The tails decode as vertex data, but no `world` item points to them. An earlier, longer save left them when a later save rewrote the stream from offset 0. The Browser bulk stream keeps stale records in the same way.

Kit raised `ValueError("Trailing graphics mesh bytes")` for these scenes.

## Workaround

Keep the tail of each stream as scene slack: `GraphicScene.MeshSlack` for `stream_mesh_NNN` and `GraphicScene.FusionSlack` for `Fusion_mesh_NNN`. Each entry is a `GraphicsStream` with the stream index and the tail bytes. The writer appends each tail after the referenced spans of its stream.

A gap between spans still fails with `Unaccounted graphics mesh bytes`. A stream with no span still fails with `Unreferenced graphics mesh streams`. Slack for a stream that no item references fails with `Graphics mesh slack names an unreferenced stream`.

Both members now read, and their written `world` and stream members equal the saved bytes.

## Evidence

- [Cache and package notes](../../../../../re/Fusion/Reconstruction/ReadGaps/CachePackageNotes.md#mesh-streams-with-stale-tails-members-6-and-8)
- [Tail spy](../../../../../re/Fusion/Reconstruction/ReadGaps/TailSpy.py) and [cache check](../../../../../re/Fusion/Reconstruction/ReadGaps/TryCache.py)
- [Scene stream evidence](../../../../../re/Fusion/Reconstruction/ReaderCoverage/SceneStreams/SceneStreams.json)
- [Cache gap tests](../../../../../tests/convert/formats/FusionCodec/SavedCorpus/CacheGapTests.py), case `TestMeshSlack`
- [ACT bulk slack](FusionActBulkSlack.md)
