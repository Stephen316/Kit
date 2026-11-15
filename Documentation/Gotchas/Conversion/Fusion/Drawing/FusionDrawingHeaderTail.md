# A DWG without its four header shorts stalls the drawing open

The DWG header section of a Fusion drawing ends with four BS values after its handle stream.
Each value uses the 2-bit `00` code and a full 16-bit short, unless it is below 256.
A BL value follows, then fill bits from the `0x55` pattern.
Every Fusion save writes that BL as zero, with the 2-bit `10` code.
The ODA specification lists four unknown BS values at the end of the header variables.

Kit reads these bits as `TailWidth` and `TailBits` and writes them back unchanged.

| DWG                                         | `TailWidth` | Four values                       | BL and fill |
| ------------------------------------------- | ----------- | --------------------------------- | ----------- |
| A1 control                                  | 77          | `0x8DA9`, `0xC9A5`, `0xF093`, `0xFED8` | `10` and `101` |
| A2 control                                  | 77          | `0x7B4C`, `0xCEEE`, `0x05E7`, `0x8C61` | `10` and `101` |
| 27 DWG exports of Fusion 2706.1.17          | 77          | Different in every export         | `10` and `101` |
| Export of `U9OwnShortsZeroPad`              | 101         | Different                         | Full BL and `101` |

`U9OwnShortsZeroPad` had zero fill bits, so Fusion read a BL with the `00` code there.
Its export wrote that BL back with a full 32-bit value.

The values do not follow from the DWG content alone.
`H1NoAcm` and `N2AuthoredF2d` carry the same DWG bytes.
Their Fusion exports still carry unrelated values, such as `0xBB79` and `0x1341` first.

Variants without the values stalled.

| Variant            | Header tail                                    | Result                                        |
| ------------------ | ---------------------------------------------- | --------------------------------------------- |
| `Q1NoDataStore`    | The A1 values and fill                         | Opened in 4.7 s with 3 views and 1 dimension  |
| `U1ZeroShorts`     | `Q1NoDataStore` with four zero values (`10` code) and zero fill | Not open after 453 s, no dialog |
| `F7ZeroHeaderTail` | The A1 control with no values and zero fill    | Not open after more than 10 minutes           |

Fusion checks the values themselves.
These variants change only the header tail of `Q1NoDataStore`.

| Variant              | Header tail                                         | Result                          |
| -------------------- | --------------------------------------------------- | ------------------------------- |
| `U9OwnShortsZeroPad` | The A1 values with zero fill bits                   | Opened in 3.3 s                 |
| `B10FifthLong`       | The A1 values with the BL set to 1                  | Opened in 3.5 s                 |
| `W2KitShorts`        | Four full values that Kit takes from the version GUID | Not open after 185 s, no dialog |
| `U2ForeignTail`      | The 77 tail bits of the A2 control                  | Not open after 181 s, no dialog |

## What the values depend on

Each variant below keeps the A1 values and changes one input.
A stall means that the values depend on that input.

| Variant              | Input changed                                       | Result                     |
| -------------------- | --------------------------------------------------- | -------------------------- |
| `H1NoAcm`            | Objects: AutoCAD Mechanical objects and unused blocks removed, handle map rebuilt | Opened |
| `Q1NoDataStore`      | Objects and sections: data-store flags and section removed | Opened in 4.7 s     |
| `B0Base`             | `Q1NoDataStore` emitted again in a new bundle       | Opened in 4.4 s            |
| `Q8AuthoredSections` | Section set and section ids                         | Opened in 5.2 s            |
| `W3KitAuxHeader`     | Auxiliary header                                    | Opened in 3.5 s            |
| `W4KitSummary`       | Summary                                             | Opened in 3.4 s            |
| `W5KitFreeSpace`     | Object free-space record                            | Opened in 6.1 s            |
| `W6KitClassCounts`   | Class instance counts                               | Opened in 3.6 s            |
| `N2AuthoredF2d`      | Every F2D member, with a new DWG member name        | Opened in 4.3 s            |
| `B8UserReal`         | `USERR4` from 0.0 to 1.0, the same in every save    | Not open after 61 s        |
| `B1VersionGuid`      | `VERSIONGUID`, a header string                      | Not open after 61 s        |
| `B9AllVaried`        | Every header variable that differs between saves    | Not open after 61 s        |

The values therefore cover the header variables, both the data and the strings.
They cover neither the objects nor the other sections.
A single changed header variable breaks them, so the variables that differ between saves were not tested one by one.

## Ruled-out rules

The values are not a plain checksum of the header.
These functions were tested on 31 Fusion saves: the A0, A1 and A2 controls, the historical example and 27 exports.

| Inputs                                                           | Functions                                    | Matches |
| ---------------------------------------------------------------- | -------------------------------------------- | ------- |
| Header bytes before the tail, with and without sentinel and size | CRC-16 ARC, Kermit, CCITT and Buypass        | None    |
| Same, with the tail bits set to zero                             | The same CRC-16 functions                    | None    |
| Header data and strings, and the handle stream, as packed bits   | The same CRC-16 functions                    | None    |
| Every input above                                                | Seeds 0, `0xFFFF`, `0xC0C1` and each of the four values | None |
| Every input above                                                | CRC-32, CRC-32C and CRC-32/MPEG-2, seeded with 0, all ones or two of the values | None |
| Every input above                                                | Adler-32, CRC-64 ECMA and ISO                | None    |
| Every input above                                                | Any four adjacent words of MD5, SHA-1, SHA-256, SHA-512 and BLAKE2b | None |
| Three of the four values                                         | CRC-16 of the other three, in any order      | None    |
| Save times, handle seed and GUID words as seeds                  | MSVC, Park-Miller, `lrand48` and MT19937 sequences | None |

Earlier runs also ruled out CRC-16, CRC-32, Adler-32 and digests over each section, the header area and the whole file.
The values match no word of the fingerprint GUID, the version GUID or the save timestamps.
They do not appear elsewhere in the DWG as aligned bytes or as typed object values.
Their bits are evenly spread, and the four values show no relation to each other.

The values therefore behave like a keyed check over the header variables.
Only Fusion's own code could show the key or the rule, and that code is out of scope.

## What the values are

The four values are one encrypted 8-byte block, not four independent values: a 16-bit checksum of the
header area, a product code `1`, the writing version code and a zero short, encrypted with Blowfish
under a 16-byte constant from `libacdb`.

That makes them a vendor integrity check over the header variables.
The [Fusion donor ban](../../../../../Documentation/Reference/Research/FusionDonorBan.md) forbids
reproducing a vendor integrity or trust check, and forbids disassembling, debugging or tracing Fusion
or its libraries, so Kit does not compute them.
The measured rule and the evidence are recorded in the
[research record](../../../../../re/Fusion/Reconstruction/Drawings/ThirdParty/HeaderTail/README.md).

The values were reproduced for 54 of the 60 corpus saves, and a drawing that carried them opened in
local Fusion 2706.1.17 and accepted a scaling edit.
That work is research only and no longer has a product path:

| Case                              | Result                                       |
| --------------------------------- | -------------------------------------------- |
| All 38 `AC1027` saves but one     | header bytes reproduced exactly              |
| 17 of 22 `AC1032` saves           | header bytes reproduced exactly              |
| The six remaining saves           | crafted or non-standard tail                 |
| A drawing with the computed tail  | opened in Fusion and accepted a scaling edit |
| A Kit-authored DWG                | still stalls, because Kit writes placeholders |

## What Kit does

Kit writes the placeholder tail it always wrote: four shorts taken from the drawing's version GUID,
with the last byte filled from the low bits of `0x55`.
Kit does not copy the values of a Fusion save into an authored file, and it does not compute them.
A parsed save keeps its stored values so that reading and re-emitting it stays lossless.

Fusion 2706.1.17 therefore does not open a DWG that Kit authors, as the
[authored shell gotcha](FusionDrawingAuthoredShell.md) records.
Closing that gap needs a document-level field that Fusion accepts in place of the check, or an
explicit decision to lift the prohibition.
