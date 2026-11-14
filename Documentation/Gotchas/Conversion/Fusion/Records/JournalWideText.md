# Long T-spline program text uses ASM tag 9

## Expectation

Every journal string uses ASM tag 8 with a 4-byte length. T-spline program text in a Form journal is then always a tag 8 string.

## Actual behavior

Fusion 2706.1.17 writes program text longer than 32767 characters with tag 9 and an 8-byte length. The cap prism saves for valences 6, 7 and 8 carry 37658 to 50541 characters this way. A 31161-character text in the same run still uses tag 8.

Kit's ASM table had no entry for tag 9. The reader stopped on these saves, and the writer could not emit long program text.

## Workaround

Read tag 9 as a string with an 8-byte length. Accept it as program text only above 32767 characters. Emit tag 9 from the wide text writer when the text is longer than 32767 characters, and tag 8 otherwise.

## Evidence

- [Cap prism probe](../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapPrismsProbe.json)
- [General conversion notes](../../../../../re/Fusion/Reconstruction/FormDocuments/General/GeneralNotes.md)
- [Spline text tests](../../../../../tests/convert/formats/FusionCodec/Brep/Spline/SplineTextTests.py)
