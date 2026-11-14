# Older saves write billboard attributes without flip visibility

## Expectation

Every saved scene declares `BillBoardAttribute` serializer version 2. Each billboard attribute holds `Style`, `Anchor`, `Axis`, `Compensation` and `FlipVisibility`.

## Actual behavior

`re/Fusion/examples/.f3d/example2.f3d` and the documents in `re/Fusion/examples/.f3z/example1.f3z` declare version 1. `BillBoardAttributeSerializer::DeSerialize` reads `FlipVisibility` only for version 2.

Kit accepted only version 2. It raised `ValueError("Unsupported graphics serializer versions or environment")` for these scenes.

## Workaround

Accept versions 1 and 2 in the scene globals. Select the attribute fields from the declared version. Do not write `FlipVisibility` for version 1.

## Evidence

- [Scene stream evidence](../../../../../re/Fusion/Reconstruction/ReaderCoverage/SceneStreams/SceneStreams.json)
- [Global version script](../../../../../re/Fusion/Reconstruction/ReaderCoverage/SceneStreams/Globals.py)
