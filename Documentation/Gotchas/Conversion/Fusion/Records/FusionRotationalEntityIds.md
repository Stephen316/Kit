# Saved rotational histories can hold face and vertex entity ids

## Expectation

Token 1 of each ASM face and vertex record in a body history is `-1`. The typed cylinder and frustum views write `-1` in that slot.

## Actual behavior

After some edits and saves, Fusion 2706.1.17 writes entity ids in that slot. `vendor_NativeCylinderControl.f3d` and `vendor_NativeFrustumControl.f3d` both hold these values:

| Records | Ordinals | Entity ids |
| --- | --- | --- |
| Faces | 4, 5, 6 | 14, 15, 16 |
| Vertices | 20, 21 | 12, 13 |

The typed views compared the stored tokens with the tokens they rebuilt. They then raised `ValueError("Unsupported Fusion BRep semantic field")`. 23 Fusion-saved documents failed with this error.

Prism histories can hold ids in the same way. `namedbodies.f3d` holds ids on six faces and eight vertices. The prism view does not model these ids.

## Workaround

`ReadIds` reads the five slots into `EntityIds`. `HistoryModel` and `FrustumHistory` keep the value in `Tracking`. `BuildHistory` and the frustum record builder apply the ids with `ApplyIds`. The default value keeps `-1` in each slot, so authored bodies do not change. `ApplyIds` raises `ValueError` when a slot already holds an id. A prism history with ids stays in the exact journal model. `TestTrackedIds`, `TestEntityIds`, `TestIdBounds` and `TestSlotReject` cover these rules.

## Evidence

- [Entity id model](../../../../../src/convert/formats/Fusion/BrepCodec/Models/EntityIds.py)
- [Typed mismatch script](../../../../../re/Fusion/Reconstruction/ReaderCoverage/TypedMismatch.py)
- [Native acceptance cases `CylinderIds` and `FrustumIds`](../../../../../re/Fusion/LocalOracle/ReaderCoverage/NativeAcceptance.json)
- [Change entry](../../../../Changes/Fusion/Records/FusionSavedDocumentCoverage.md)
