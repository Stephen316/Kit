# Drawing views need their view rep objects

Fusion 2706.1.17 builds its drawing views from DWG objects, not from the drawing segments.
A view needs its `ACDBVIEWREP` object.
A drawing without those objects opens without usable views, and Fusion gives no error.

Each variant below removes objects from the A1 control without unused blocks.
The base opened with 3 views of 5, 4 and 4 curves and 1 dimension.

| Variant             | Removed objects                                                  | Views              | Dimensions |
| ------------------- | ---------------------------------------------------------------- | ------------------ | ---------- |
| `F1NoViewReps`      | `ACDBVIEWREP` and its two subentity holder classes               | Items were `None`  | 1          |
| `F2NoViewActions`   | The `F1NoViewReps` objects and the associative view actions      | 0                  | 1          |
| `F8bNoNetwork`      | The `F1NoViewReps` objects and every associative action and network | 0              | 1          |
| `F3bPlainDimension` | The associative action of the dimension                          | 3                  | 1          |
| `F4NoTitleBlock`    | The `ISO_TITLEBLOCK` insert                                       | 3                  | 1          |
| `F5NoBorder`        | The `ISO_A3_SHEET` border insert                                  | 3                  | 1          |
| `F6NoCenterMark`    | The centre mark                                                  | 3                  | 1          |

In `F1NoViewReps`, `Sheet.views.count` was not 0, but `Sheet.views.item()` returned `None`.
`F2NoViewActions` and `F8bNoNetwork` also lack the view reps.
They therefore do not show whether the actions or the network are needed on their own.
`F3bPlainDimension` shows that a plain dimension without its associative action is accepted.

These named-object dictionary entries are not required.

| Variant          | Removed entry                                  | Views | Dimensions |
| ---------------- | ---------------------------------------------- | ----- | ---------- |
| `E2NoNodHistory` | Save history, recompose data and mechanical entries | 3 | 1          |
| `E3NoFusionNod`  | The `ACAD_FUSDOC_*`, `FUSDOC_*` and `AcFusion*` entries | 3 | 1        |
| `E4NoVariables`  | Every `DICTIONARYVAR` object                   | 3     | 1          |
| `E5NoFields`     | Every `FIELD` and `FIELDLIST` object           | 3     | 1          |

A removal must not leave a handle to an absent object.
The [dangling handle gotcha](FusionDrawingDanglingHandles.md) records why.
