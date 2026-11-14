# A shell can hold a wire instead of faces

## Expectation

Every shell record points to its first face. The slot after the face slot looks like an unused reference that is always null.

## Actual behavior

Shell slot 6 is the first wire of the shell. A wire shell has a null face slot and a live wire slot. Five corpus journals contain one live wire each. They come from split-face and surface-trim features that use a sketch line.

The `wire` record has the common entity prefix and these fields.

| Token | Field | Corpus value |
| --- | --- | --- |
| 3 | Next wire | Null in all 5 records |
| 4 | First coedge | Live coedge |
| 5 | Owner shell | Live shell |
| 6 | Reserved reference | Null in all 5 records |
| 7 | Side logical | `F` in all 5 records |

A wire coedge stores the wire in its owner slot 8 instead of a loop. Its next and prior slots point to itself, and its partner slot is null.

## Workaround

Read shell slot 6 as `ShellNode.FirstWire`. Require a face or a wire on each live shell. Accept a wire as a coedge owner, and use `WireNode` for the record. Do not treat a null face slot as a missing reference when the wire slot is live.

## Evidence

Fusion 2706.1.17 opened the five wire archives after typed re-emission. Every stage equaled the native control within 1e-8, through rollback, rebuild, save and reopen. Fusion lists one body for each split-face archive, so the wire body does not appear in `bRepBodies`.

- [Corpus bounds summary](../../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyBounds.json)
- [Acceptance preparation](../../../../../re/Fusion/LocalOracle/ComplexGeometry/Bounds/Preparation.json)
- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/Bounds/NativeAcceptance.json)
- [Journal attribute evidence](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalAttributes/Evidence.json)
- [Reader coverage acceptance](../../../../../re/Fusion/LocalOracle/ReaderCoverage/NativeAcceptance.json)
