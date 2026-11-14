# Manual drawing creation needs a template

Fusion 2706.1.17 rejects a manual drawing request that has no template.
`DrawingManager.createDrawing` raised this error for `ManualDrawingCreationMode`:

```text
RuntimeError: 3 : Manual drawing creation requires a template with view placeholder information.
```

The automatic mode succeeded with the same source design.
It created one A3 sheet with one base view, two projected views and an ISO title block.
The Kit drawing controls therefore use `AutomaticDrawingCreationMode` with automatic dimensions turned off.
A script can then add a dimension through `drawingDimensions.addLinearDimension`.

| Creation mode                      | Observed result                                |
| ---------------------------------- | ---------------------------------------------- |
| `ManualDrawingCreationMode`        | Rejected, no drawing file                      |
| `AutomaticDrawingCreationMode`     | Drawing file with one sheet and three views    |
| Automatic mode with auto dimension | Drawing file, but the script did not return    |

The automatic-dimension run created its drawing file, but the oracle runner timed out after 1,500 seconds.
Do not use automatic dimensions in an unattended capture until the cause is known.

The [capture scripts](../../../../../re/Fusion/Reconstruction/Drawings/Native/CaptureAuto.py) record the request values.
