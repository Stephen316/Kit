# Sketch and profile tag field semantics

This note covers two saved callback values: the profile edge tag and the sketch tag.
An earlier version also cited static inspection of installed Fusion libraries.
That material was removed.
Claims that rested only on it are marked below as not confirmed by a black-box experiment.

## Profile edge tag layout

The saved profile edge tag callback writes a version, a counted sketch-tag vector, and two counted sets of uint64 primary sketch tag IDs.
Kit names them start-adjacent and end-adjacent primary tag IDs.
That naming, the `SA` and `EA` labels, and the claim that each set holds only primary curve tags, came from the removed static evidence.
They are not confirmed by a black-box experiment.

## Topology role flags

The sketch tag holds a uint64 after the split sequence and total in the binary callback.
Kit calls it topology role flags.
The [read-only corpus sampler](SketchTagSamples.py) examined all 712 archives.
It found [5,077 decoded callback values](SketchTagSamples.json), all with zero role flags, with no unresolved records or archive failures.
This shows that zero is the common value in these files.
It does not show that nonzero flags are invalid.

The removed static evidence listed sheet-metal operations that set nonzero masks in this field.
That list, the field's version gate and its role in tag matching are not confirmed by a black-box experiment.
The complete bit meanings and the original member name remain unknown.

## Field order

The binary callback writes the role flags after the split sequence and total.
The ASCII kernel attribute places its fourth field before the split fields; see [SketchAsciiSemantics.md](SketchAsciiSemantics.md).
Reusing one order for the other corrupts semantic values.

## Direction wildcard

The saved corpus holds direction values 0, 1 and `4294967295`.
Treating `4294967295` as a wildcard came from the removed static evidence.
It is not confirmed by a black-box experiment.
