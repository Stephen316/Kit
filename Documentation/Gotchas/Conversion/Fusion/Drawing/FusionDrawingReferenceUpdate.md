# A drawing keeps old views until its references update

Fusion 2706.1.17 does not update drawing views when it opens a drawing after a model edit.
The views keep the geometry of the referenced model version that the drawing last used.

The Kit acceptance changed `kitWidth` from 40 mm to 60 mm and saved the design as version 2.
It then opened the typed re-emitted drawing.

| Stage                         | Reference version | `isOutOfDate` | Base view width on the sheet |
| ----------------------------- | ----------------- | ------------- | ---------------------------- |
| After open                    | 1                 | `True`        | 160 mm                       |
| After `updateAllReferences()` | 2                 | `False`       | 240 mm                       |

The base view scale is 4.0, so 240 mm is the 60 mm model width.
The drawing engine logged a `VIEWUPDATE` command for the update.

Call `DrawingDocument.updateAllReferences()` before you measure a drawing after a model edit.
Check `DocumentReference.isOutOfDate` before and after the call.

The projected views kept their sheet positions.
The side view stayed at x = 278 mm to 318 mm, while the wider base view extended to x = 300.47 mm.
A model edit can therefore make views overlap on the sheet.

The [edit acceptance script](../../../../../re/Fusion/Reconstruction/Drawings/Native/EditAcceptance.py) records these values.
