# Spline program text uses two string widths

## Expectation

SAB string tokens in Fusion BRep members look like one form: tag 7, a one-byte length and the text. Earlier Kit readers accepted only that form.

## Actual behavior

The `t_spl_subtrans_object` scope stores two line-oriented texts. The first text is the complete TSM program. The second text is the patch program. Each text uses tag 7 with a one-byte length or tag 8 with a little-endian two-byte length.

| Text | Members with tag 7 | Members with tag 8 | Largest tag 7 text (bytes) | Smallest tag 8 text (bytes) |
| --- | --- | --- | --- | --- |
| TSM program | 0 | 64 | None | 1226 |
| Patch program | 28 | 36 | 118 | 444 |

No member stores a text of 255 bytes or less with tag 8. Kit writes tag 7 up to 255 bytes and tag 8 above. The observations do not include a text between 119 and 443 bytes. The 255-byte limit comes from the one-byte length field.

The patch program starts with the line `0 N`, where `N` is the number of BRep faces. Each face has one line. The line holds the cell count and eight integers for each cell, and each number ends with a space. The eight integers are the TSM face, a four-integer window and a three-integer offset.

## Workaround

Read both widths in `ReadAsmToken`. Choose the width from the text length when you write. Reject a text that uses a non-canonical width, because Kit cannot then reproduce the source bytes. Keep the patch program as typed `PatchCell` rows and derive the text with `WritePatches`.

## Evidence

- [Spline census](../../../../../re/Fusion/Reconstruction/FormDocuments/SplineCensus.json)
- [Form round trip](../../../../../re/Fusion/Reconstruction/FormDocuments/RoundTrip.json)
- [Form document change entry](../../../../Changes/Fusion/TSpline/FusionFormDocuments.md)
