# Older Fusion BRep members use 4-byte ASM integers

## Expectation

Every Fusion BRep member starts with `ASM BinaryFile8`. Its header and integer tokens hold 8-byte integers. A history journal header holds the scale 50.

## Actual behavior

The older example files hold 78 BRep members that start with `ASM BinaryFile4`. All other corpus members start with `ASM BinaryFile8`. Both kinds hold ASM version 23200.

| Member | Header | First header number | Members |
| --- | --- | --- | --- |
| `.smbh` | `ASM BinaryFile8` | 50 | 1,456 |
| `.smb` | `ASM BinaryFile8` | 10 | 1,375 |
| `.smb` | `ASM BinaryFile4` | 10 | 41 |
| `.smbh` | `ASM BinaryFile4` | 40 | 35 |
| `.smbh` | `ASM BinaryFile4` | 30 | 2 |

The digit is the integer width. The four header integers have that width. Tags 4, 12, 21 and 23 hold integers of that width, and tag 18 has a length of that width. Every other token is the same at both widths. With this rule every narrow member tokenizes to its exact end.

The example journals also exceed the old quotas. The largest has 9,258,923 bytes, 5,139 entities and a `delta_state` record of 321,648 tokens.

## Workaround

Read the width from the signature, and keep it in `BrepHeader.IntWidth`. Pass it to the token reader, and write it back. Accept any positive first number in a history journal header, and write the stored value. Snapshots keep 10.

`JournalLimits.py` holds the journal quotas: 32 MiB per member, 2^18 entities, 4,096 states, 2^16 roots, 2^14 boards per state and 2^18 board changes. `AsmTable.py` allows 2^20 tokens per record.

## Evidence

- [Read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#asm-integer-width)
- [Header census](../../../../../re/Fusion/Reconstruction/ReadGaps/AsmHeads.py)
- [Narrow tokenizer](../../../../../re/Fusion/Reconstruction/ReadGaps/NarrowAsm.py)
- [Journal trial](../../../../../re/Fusion/Reconstruction/ReadGaps/TryWidth.py)
