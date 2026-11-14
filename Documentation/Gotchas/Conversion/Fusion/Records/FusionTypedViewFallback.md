# Typed body views do not rebuild every value that Fusion stores

## Expectation

A body history or snapshot that matches the shape rules of a typed view decodes into that view. The view then rebuilds each stored token.

## Actual behavior

The typed views calculate some values from a small set of parameters. Fusion stores values that it calculated in a different way. In `extents/offset_negative.f3d`, the cylinder history stores a top plane at Z `0.8000000000000002`. The typed view calculates `0.8`. The snapshot of the same document stores the offset start plane at Z `0.0`, and the typed view calculates `-0.9`. A prism history with entity ids also fails its typed view.

Before this change, such a mismatch rejected the whole document. In the corpus, 13 Fusion-saved documents have a body history that fails its typed view.

## Workaround

`ReadBodyPart` always decodes the exact `JournalModel` first. It then tries the typed view that `PickBodyView` selects. If the typed view raises `ValueError`, the document keeps the `JournalModel`. `ReadSnapPart` does the same with `GeometryState` and `ReadTypedSnap`. The journal and geometry codecs re-emit the stored bytes exactly.

The typed views put records in a canonical order. A typed view that succeeds can therefore write different bytes with an equal model. Across the corpus, only part of the typed members re-emit byte-exact:

| Model | Byte-exact members |
| --- | --- |
| `JournalModel` | 525 of 525 |
| `GeometryState` | 581 of 581 |
| `HistoryModel` | 20 of 59 |
| `PrismHistory` | 14 of 77 |
| `FrustumHistory` | 12 of 24 |
| `SnapshotModel` | 7 of 47 |
| `PrismSnapshot` | 6 of 105 |

`TestTypedFall` checks that `offset_negative.f3d` keeps its journal model.

## Evidence

- [Typed body selection](../../../../../src/convert/formats/Fusion/DocumentCodec/Reading/ReadTypedBody.py)
- [Typed mismatch script](../../../../../re/Fusion/Reconstruction/ReaderCoverage/TypedMismatch.py)
- [Byte exactness script](../../../../../re/Fusion/Reconstruction/ReaderCoverage/BrepExactness.py)
- [Native acceptance cases `JournalFallback`, `SnapshotFallback` and `PrismFallback`](../../../../../re/Fusion/LocalOracle/ReaderCoverage/NativeAcceptance.json)
- [Change entry](../../../../Changes/Fusion/Records/FusionSavedDocumentCoverage.md)
