# Fusion parameter allocation watermark

## Expectation

In captures without parameter removal, the unsigned word at body offset 11 of the parameter collection equals the following member count.
Treating those equal values as two copies of the same count appears to reproduce those captures.

## Actual behavior

The runtime reflection capture lists the collection as `ParameterTableMetaType`.
Its own member set registers `highWaterMark` as a separate unsigned 32-bit member.
The word is therefore not a second copy of the list length.

## Workaround

Preserve allocation state separately from the current member sequence.
`ParamScope.HighWaterMark` is an explicit writer input; only the list count is derived from `MemberIds`.
Do not infer a general deletion or reallocation policy until controlled captures establish it.
The existing dense-ordinal source-proof profile remains deliberately narrower than the archive reader.

See the [reflection capture](../../../../re/Fusion/LocalOracle/Reflection/Versions.json) and the [data model](../../../Reference/Research/FusionDataModel.md#parameter-collection).
