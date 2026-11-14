# Saved bool members can hold bytes above 1

## Expectation

A saved `bool` member is one byte, 0 or 1.

## Actual behavior

`DiameterDimensionInfo.needExtendArcForDim` holds the bytes `0x02`, `0x0a` and `0x20` in the older example files. The value class and its base have metadata rows at versions 2 and 3, which equal the catalog. Every other member of the 417-byte `FusionSketchDiameterDim` records decodes, and the next member starts right after the byte. The byte probably holds an uninitialized C++ `bool`.

The reader raised `Invalid Fusion feature scalar`.

## Workaround

Read a `bool` member as one byte. 0 is false, 1 is true, and any other byte is also true. Keep a byte above 1 as an integer, and write it back unchanged. `FlagByte.py` holds the rule.

The structural presence flags of frames, references and matrices still accept only 0 or 1.

## Evidence

- [Read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#example-record-rules)
- [Atom spy](../../../../../re/Fusion/Reconstruction/ReadGaps/AtomSpy.py)
