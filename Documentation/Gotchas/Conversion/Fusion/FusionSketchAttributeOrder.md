# Sketch attribute field order differs from the Design callback

## Expectation

The same native sketch-tag value uses one field order in every serialized form.

## Actual behavior

Kit reads the ASCII string inside `sketch_attrib_def` as primary identity, secondary identity, direction, topology role flags, split sequence and split total. It reads the binary Design callback as version, primary identity, secondary identity, direction, split sequence, split total and topology role flags.

The ASCII fourth word was previously described as an inserted zero, and the final pair as enumerations. The corpus supports the new reading. Across 20,636 attributes, the fourth word is always zero, and every final pair satisfies `1 <= sequence <= total`. 456 attributes have non-default split pairs. The field names and widths come from earlier binary inspection. The corpus agrees with them but does not prove them.

## Workaround

Map each wire form to named semantic fields rather than sharing an unqualified positional tuple. Use unsigned 64-bit domains for primary/secondary identities and role flags, unsigned 32-bit domains for direction and split fields, and validate the one-based fragment relationship. Keep unsupported nonzero role flags guarded until their complete meanings are qualified.

[The corpus evidence](../../../../re/Fusion/Reconstruction/EntityGraph/SketchAsciiSemantics.json) records the counts. [The production model change](../../../Changes/Fusion/FusionSketchAttributeSemantics.md) describes API migration and archive coverage.
