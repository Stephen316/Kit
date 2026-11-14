# Fusion segment kinds include drawing segments

`SegmentKind` might appear to list only the segments of a design archive.
It also has `KDrawingDesign` and `KDrawingAct`, because the drawing reader and writer use the same metadata grammar.
A design archive such as `offset.f3d` has no `FusionDrawingDesignSegmentType1` or `FusionDrawingACTSegmentType1` folder.
A loop over every `SegmentKind` member that reads `BulkStream.dat` from a design archive raises `KeyError`.

Iterate `KCoreSegments` from `ContainerCodec/ContainerLayout.py` when you read the segments of a design archive.
Iterate `SegmentKind` only for synthetic metadata that you build in the test.
See [merge queue run 43530545010](https://github.com/TryUniCAD/Kit/actions/runs/43530545010), which failed in `FusionBulkWireTests`, `FusionSegmentTests` and the isolated wheel runtime.
