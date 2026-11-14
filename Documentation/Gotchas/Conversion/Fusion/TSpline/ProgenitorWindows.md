# Form progenitor windows are patch cell boxes

## Expectation

The Form feature stores one progenitor per cage face and per cage edge. The BRep tags of the converted body name these cage entities.

## Actual behavior

Fusion stores one `TSplineEntityProgenitor` per tagged BRep face or edge, not per cage entity. The tag text in the BRep is a decimal label. The label numbers are small integers that start at 1.

Each progenitor lists windows as `TsEntityProgInfoValue(faceIndex, uLow, uHigh, vLow, vHigh)`. `faceIndex` is a cage face index. The window is a box in the local parameter square of that cage face.

| Tagged entity | `entityType` | Windows |
| --- | --- | --- |
| BRep face | 0 | One window per patch cell of the face patch program, sorted by cage face index. The window is the cell box. |
| Grid side 0, first row | 1 | (0, 1, 0, 0) for each cell in row 0 |
| Grid side 1, last column | 1 | (1, 1, 0, 1) for each cell in the last column |
| Grid side 2, last row | 1 | (0, 1, 1, 1) for each cell in the last row |
| Grid side 3, first column | 1 | (0, 0, 0, 1) for each cell in column 0 |

A grid cell with offset (−row, −column, 0) is in that row and column. The edge windows are sorted by cage face index.

Not every BRep edge has a tag. The box, symmetric box and creased box bodies tag only their six faces. The creased plane body has no tag on its interior crease edge.

The labels connect four Design records.

| Record | Content |
| --- | --- |
| `DcTSplineFeature.subDInfoMap` | One entry from the SubD node to (301, node progenitor table) |
| Node progenitor table | `ProgenitorTagVec` of (progenitor, label number) in ascending label order, and `tagId` = largest label + 1 |
| Body progenitor | `featureTagOccMap` key `FeatureTagInfoValue` with the ASCII labels concatenated in ascending order, cumulative offsets, `operationId` 301 and `primary` false |
| Feature progenitor table | `ProgenitorTagVec` of (body progenitor, 1) and `tagId` 2 |

Fusion does not assign the labels in one fixed order. Plane primitives from the same API call sequence get different side labels.

| Archive | Face label | Side 0 | Side 1 | Side 2 | Side 3 |
| --- | --- | --- | --- | --- | --- |
| `Plane1x1` | 1 | 3 | 4 | 2 | 5 |
| `Plane3x2` | 1 | 4 | 5 | 2 | 3 |
| `Plane4x4` | 1 | 4 | 5 | 3 | 2 |
| `Plane2x5` | 1 | 3 | 2 | 4 | 5 |
| `TSpline/Plane` | 5 | 4 | 1 | 3 | 2 |

The local archives have labels below 10 only. The order of labels with two or more digits has no evidence.

## Workaround

Derive the face windows from the patch program with `FormLabels`. Give each tagged edge its windows in `FormEdge.Windows`. Choose any unique labels. `GridBody` uses face label 1 and side labels 2 to 5.

## Evidence

- [BRep rebuild comparison](../../../../../re/Fusion/Reconstruction/FormDocuments/Sourceless/BrepRebuild.json)
- [Native acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/Sourceless/NativeAcceptance.json)
- [Grid cage pole order](GridCagePoleOrder.md)
