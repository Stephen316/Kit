# Config-0 weld and geometric tolerance helpers

`WriteSavedWeld` and `WriteSavedTolerance` follow the [surface finish and note helpers](ConfigFinishNote.md) in the generation-19000 detail owner. Their callers supply the native typefaces for separately owned unset fonts. Both archived intervals serialize inline.

## Native field owners

Addresses are virtual addresses in the installed 34.4.1.1011 [pinned DLL](../records/P04ArchiveWalk.md#inputs).

| Owner | Native source |
| --- | --- |
| Weld defaults | `moWeldDataHelper_c` constructor `0x3c7e25b0` initializes two sides and the additional text and scalar fields. Stores at `0x3c7e2797`–`0x3c7e27ee` clear the guarded empty fields. The enabled fields at +0xe8, +0x150 and +0x154 are set at `0x3c7e2844`–`0x3c7e2858`. Serializer `0x3c870670` writes the text and settings and calls its main and two side fonts. The side font byte and format loop is `0x3c870900`–`0x3c870925`. |
| Weld finish members | The weld constructor creates its two `moSFDataHelper_c` members at `0x3c7e280c` and `0x3c7e2835`. The modern branch serializes their bodies inline through virtual calls at `0x3c870cec` and `0x3c870cfc`. Their exact settings use the existing surface finish constructor. |
| Tolerance defaults | `moGTolDataHelper_c` constructor `0x3c7e18b0` initializes frames 0 and 1 through `getGtolDlgFrame` at `0x3c7e1951` and `0x3c7e1963`. `Serialize` at `0x3c86cb40` writes the frame count at `0x3c86cb97`, iterates inline frames at `0x3c86cba9`–`0x3c86cbb7`, then writes its scalar and text fields. The embedded font and annotation helper serialize at `0x3c86cef5` and `0x3c86cf1f`. Six versioned byte options follow. |
| Tolerance frames | `moGTolDlgDataFrame_c` constructor `0x3c7e1a20` constructs the empty strings and six short-form arrays and clears the two tolerance child pointers. Serializer `0x3c86d080` files both typed pointers at `0x3c86d1aa` and `0x3c86d1b6`. A zero datum count skips inline datum records. The indicator count comes from the frame's collection at `0x3c86d217`. |

## Pinned comparison

The six P01 and eight P03 saves at capture revision `466dcb172dfa3803463e07ccde963ba01671d200` share a 1,044-byte weld record at +13740 to +14784 and a 388-byte tolerance record at +14784 to +15172 relative to the relation return. Their SHA-256 digests are `0e9aa4204bc596b29dec18625360aaa6a4e729cc346bf4fe7f658c59462b5aba` and `4b743aea3cc89b8e303edf284b54ef1d17e1956c94571ba11dedc6d31768eb9b`. The two weld finish intervals start at +400 and +722 within the weld helper. The four null pointers in the tolerance frames start at +48, +50, +100 and +102 within the tolerance helper. The archive next slot stays 66 or 70.

[Hosted verification](VerifyConfigWeldTolerance.py) will compare both generated intervals and the archive map. Expected read-only replay digests are `2115ff0916fd90b17900e6bba2c67ce9964183de9c3e446197bf8b93d3791a0b` for weld and `7e2e03da49c28147edfe34010635b41553073c2ceaf74c859a450f9de11c6360` for tolerance, with rows recording source receipt hashes, native boundaries, inherited next slot and span hashes. The independent detail return reaches +17566 before the shared parameter array.
