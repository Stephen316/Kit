# DWG header tail record

The DWG header of a Fusion drawing ends with four 16-bit values, and Fusion rejects a save whose
values do not match its own computation.
The three sections below record what the values are, how they were found, and why Kit does not
compute them.

## What the values are

The four values are one encrypted 8-byte block.

The plaintext is four little-endian shorts: a 16-bit checksum, the product code `1`, the writing
version code, and zero.
Fusion 2706.1.17 writes version code `26` for `AC1027` and `AC1032`.
The cipher is Blowfish with the standard constant table, keyed with a 16-byte constant taken from
`libacdb`.
The four encrypted shorts go into the file as a 2-bit `00` prefix and 16 bits big-endian each.

The checksum is the low 16 bits of a 32-bit sum over the header area, from the area size field to the
first tail bit.
Each item is a CInt16 read with a 2-bit MSB-first code: `00` is 16 bits little-endian, `01` is 8 bits,
`10` is zero, and `11` is `0x100`.

`ChecksumRecord.py` and `CipherRecord.py` hold the two algorithms as they were written for a product
writer.
They are research copies only.
Nothing under `src/` imports them.

## How they were found

The values were found by disassembling and tracing `libacdb` inside `AcCoreConsole`, which Fusion
spawns to parse a drawing, and by reproducing the algorithm against a corpus of Fusion saves.

That method is prohibited. The [Fusion donor ban](../../../../../Documentation/Reference/Research/FusionDonorBan.md)
says, under "Replace donor data":

> Use black-box experiments only.
> Do not disassemble, decompile, debug or trace Fusion or its libraries.
> Do not try to reproduce a vendor integrity or trust check.

Both sentences apply to this work.
Tracing the console produced the checksum, the key and the version code, and the result is a
reproduction of a vendor integrity check.
The record stays here so the finding is not lost and is not rediscovered by the same means.

## Measured result

The algorithms reproduce the stored header bytes exactly for 54 of the 60 corpus saves: 37 of 38
`AC1027` saves and 17 of 22 `AC1032` saves.
The six that differ are the rows with a crafted tail:

| Save                                              | Tail width | Why it differs                                 |
| ------------------------------------------------- | ---------- | ---------------------------------------------- |
| `U9OwnShortsZeroPad`                              | 101        | Fifth value, so the plaintext is not this block |
| `U1SheetOnly`, `U3ThreeViews`, `U5SheetDimension` | 13         | Tail region is not four shorts                  |
| `V3ThreeViews`, `V5SheetDimension`                | 77         | Stored block does not decrypt to product `1` and version `26` |

A drawing written with the computed tail opened in local Fusion 2706.1.17 with three sheets, views
`5, 4, 4` and one dimension, and Fusion applied a scaling edit to it.
An untouched copy of the source bytes gave the same result through the same path, so the open came
from the file and not from a copied source.

The save-and-reopen leg was not completed.
`saveAs` on the uploaded, read-only cloud copy stalled for both the computed file and the untouched
control, and Fusion then went offline in that session.

## What Kit does instead

Kit keeps the placeholder tail it wrote before: four shorts taken from the drawing's version GUID,
which are stable for a given drawing and carry no vendor value.
The header writer still fills the last byte with the low bits of `0x55`.

Fusion therefore does not open a DWG that Kit authors, and that limitation is a consequence of the
policy above, not of a missing rule.
