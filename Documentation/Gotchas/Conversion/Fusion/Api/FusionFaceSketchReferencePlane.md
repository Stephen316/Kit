# Face sketches hide their reference plane at the timeline end

## Expectation

`Sketch.referencePlane` returns the support of any sketch.
A script can read it at any time to record what the sketch is on.

## Actual behavior

Fusion 2706.1.17 raises `RuntimeError` for a sketch on a body face when the timeline marker is after the sketch.
The message is `referencePlane is a BRefFace - need to roll timeline back before sketch`.
Sketches on construction planes do not raise this error.

The first P04 capture stopped at its first reading because of this error.

## Workaround

Read `referencePlane` in a `try` block.
For a face sketch, record the support as a body face and keep the sketch frame from `origin`, `xDirection` and `yDirection`.
Roll the timeline back only when the script owns the document and restores the marker afterwards.
The [shared capture code](../../../../../re/automation/PairedCaptures/FusionCapture.py) records the face without a rollback.
