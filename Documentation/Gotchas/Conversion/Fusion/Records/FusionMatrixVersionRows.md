# DRMatrix version 16 stores translations in saved documents

## Expectation

The authored corpus contains only identity `matrix3d` values in `DRMatrix` version 16. A profile that rejects other matrices then seems safe.

## Actual behavior

`DesignClasses.json` declared `matrix3d` of `DRMatrix` version 16 with `HasMatrixRows` set to false. `BindProfile` then rejected each matrix that is not identity. Fusion-saved documents with offset or fillet features store translations in that field. `vendor_RoundFilletsControl.f3d` holds three matrices that are not identity. Each matrix has a translation of 1 cm along Z in entry 11. The read failed with `ValueError("Fusion entity profile does not qualify nonidentity matrices")`.

Version 16 changed only `arcLengthForPeriodicFace`, from a double to a strong reference to `DcDoubleParameter`. The `matrix3d` layout is the same as in version 15, and version 15 already qualifies matrix rows. The corpus holds 166 version 16 records in 161 files.

## Workaround

Set `HasMatrixRows` to true for `matrix3d` in `DRMatrix` version 16. The codec then reads and writes 16 row-major `f64` values, or the identity flag. `TestMatrixRows` checks the schema flag and the three translations.

## Evidence

- [Native version differences](../../../../../re/Fusion/LocalOracle/Reflection/VersionDifferences.json)
- [Design vocabulary](../../../../../src/convert/formats/Fusion/DocumentCodec/Vocabulary/DesignClasses.json)
- [Native acceptance case `RoundFillets`](../../../../../re/Fusion/LocalOracle/ReaderCoverage/NativeAcceptance.json)
- [Change entry](../../../../Changes/Fusion/Records/FusionSavedDocumentCoverage.md)
