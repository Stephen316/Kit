# Native BRep vertex edge indices are persisted values

## Expectation

Two cylinder histories with equivalent geometry and topology can use the same vertex edge-index values after record ordinals are mapped.

## Actual behavior

The independently authored cylinder uses vertex edge indices `(0, 0)`. The native 7 mm extrusion history stores `(2, 0)`. These integers are fields of the vertex records, distinct from record ordinals and edge references. A topology bijection alone does not account for the difference.

The first remote compatibility run rejected the native history because it compared this field against the authoring default. The rejection was valid evidence of an incomplete semantic model; ignoring the field would lose source state.

## Workaround

`HistoryModel` and `SnapshotModel` retain immutable `VertexIndices` values. Readers extract them before complete record validation, and writers apply them to their derived topology. Fresh authoring defaults remain `(0, 0)`. The qualified reader admits the observed integers `0` and `2`; other values are rejected rather than normalized.

## Verification

Production `ReadHistory` and `EmitHistory` reconstructed the complete history of `extrude_07mm.f3d`, preserving `(2, 0)`, while retaining that document's own other members. Fusion 2706.1.17 opened the result with the correct 7 mm cylinder before recomputation, rolled back to the sketch, and restored and rebuilt the solid. Fusion also accepted a 23 mm parameter edit and saved/reopened with healthy features.

The [native report](../../../../re/Fusion/LocalOracle/Authored/NativeHistoryAcceptance.json) records accepted output SHA-256 `29f70738c26cab17f8abab536b08fa9ece6381c53608e6530295209f7e206797` and zero documents left open. The [preparation manifest](../../../../re/Fusion/LocalOracle/Authored/NativeHistoryReemitted.json) records source and history digests. This establishes the observed index variant, not arbitrary vertex adjacency encodings.

See [the production document codec](../../../Changes/Fusion/FusionNativeDocumentCodec.md).
