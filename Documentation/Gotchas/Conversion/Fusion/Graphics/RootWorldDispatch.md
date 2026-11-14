# The root world does not use its displayed class serializer

A world whose stored interface name is `ARenderList` appears to require the derived serializer's trailing `Accelerate` boolean. Reading that byte at the document root overruns the valid stream.

In both complete controls, the root ends immediately after `WorldSerializerEndMark`, while nested `ARenderList` values add `Accelerate`.

Select framing from the root's dispatch context as well as its stored class name. The [wire model](../../../../../re/Fusion/Reconstruction/OgsScene/WireModel.md) describes both complete controls.
