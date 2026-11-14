# Projected drawing view getters fail

Fusion 2706.1.17 returns errors for three properties of a projected drawing view.
The base view returns all three values.
Both projected views in the Kit controls returned the same errors.

| `DrawingView` property | Base view | Projected view                              |
| ---------------------- | --------- | ------------------------------------------- |
| `type`                 | 0         | 1                                           |
| `orientation`          | 3         | `3 : failed to read view orientation`       |
| `scaleValue`           | 4.0       | `3 : failed to read view scale`             |
| `style`                | 0         | `3 : failed to read view style`             |
| `viewCurves.count`     | 5         | 4                                           |

Read projected-view geometry through `viewCurves`.
Do not use the failed getters as acceptance values.
Wrap each getter separately, so that one failure does not hide the other values.

The values come from the [automatic capture](../../../../../re/Fusion/Reconstruction/Drawings/Native/CaptureAuto.py) of the A0 and A1 controls.
