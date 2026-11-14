# Controlled Fusion sketch dimension captures

`re/Fusion/LocalOracle/CaptureRectangleDimensions.py` creates a temporary native rectangle sketch and exports four successive states for differential format research. The states are the undimensioned baseline, a horizontal driving dimension, horizontal and vertical driving dimensions, and a subsequent edit of both user parameters. This is a native source generator, not a production codec or evidence of Kit-authored sketch dimensions.

Run it through the serialized local oracle:

```sh
node re/Fusion/LocalOracle/RunNative.mjs re/Fusion/LocalOracle/CaptureRectangleDimensions.py
```

The installed Fusion Python API defines `SketchDimensions.addDistanceDimension(pointOne, pointTwo, orientation, textPoint, isDriving=True)`. Each dimension's model parameter is assigned an expression referring to a named user parameter. The tool records exact file digests, all parameter bindings and values, dimension types, line endpoints, geometric constraint types and profile count. It closes the created document and restores the previously active document.

## Actual capture evidence

Fusion `2706.1.17` captured all four states successfully and left zero open documents. [Capture.json](../../../re/Fusion/LocalOracle/RectangleDimensions/Capture.json) records these files:

| State                | SHA-256                                                            | Observed semantic change                                                                                    |
| -------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| Baseline             | `a27741a82f16c9ae5839588a33a7eafccd1b42be248874f4721b209b123b2f87` | Four shared-endpoint lines form a 17×23 mm rectangle; two user parameters exist without model dimensions.   |
| WidthDimension       | `1aaa7bb5862654a833f2932b3f936cdc2d42715c181cd8888b102bafb5e1220b` | One `SketchLinearDimension`; model parameter `d3` references `controlledWidth`.                             |
| WidthDepthDimensions | `376cdae975d87e683f140a273020e0e4ec58beb003bf320c4bb334efb8dc9be7` | A second `SketchLinearDimension`; `d4` references `controlledDepth`.                                        |
| EditedDimensions     | `2d35e30d9e7bdb315116d175890cc0eb60510112d55cf8acc27796375b32b367` | User inputs become 19 and 29 mm, both model dimensions follow, and the sketch still has one closed profile. |

The geometric-constraint collection is empty in all four states. The explicit dimension collection grows from zero to one to two entries. Those collections must not be conflated. The native rectangle constructor did not expose horizontal, vertical or origin-fixing constraints through this collection.

The dimension edits preserve the measured rectangular lengths but move its bottom boundary from `y=0` to `y=-6 mm`; the upper boundary remains at `y=23 mm`. These dimensions do not anchor the sketch to the origin. See [the unanchored dimension gotcha](../../Gotchas/Conversion/Fusion/Sketch/FusionUnanchoredDimensions.md).

These files provide controlled inputs for class, field, reference and observer-graph research. They do not qualify independent dimension writing, arbitrary sketch solving, or general parametric conversion. No local automated test suite was run.

The [dimension data model](../../../re/Fusion/Reconstruction/SketchDimensions/DimensionModel.md) decodes all 1,054 physical records and 101,241 payload bytes across these four captures. It identifies the four new logical entities per dimension, inherited continuations, exact class versions, annotation values, parameter/observer links and reciprocal dependency updates. The combined entity graphs are stored as typed compressed research evidence; they are not a runtime authoring template.

[The observer model](../../../re/Fusion/Reconstruction/SketchDimensions/ObserverModel.md) and the [observer slot inventory](../../../re/Fusion/Reconstruction/SketchDimensions/ObserverSlots.json) of the saved segments distinguish persisted Browser subscribers from runtime subscribers. Binary inspection suggested that native subscription appends to a shared observer list, and that post-load registration can repair index collisions. A black-box experiment does not confirm this. The exact identities of two unsaved subscribers remain unknown; a fixed dimension index base of four is not a general format rule. See [observer indices](../../Gotchas/Conversion/Fusion/Sketch/FusionObserverIndices.md).
