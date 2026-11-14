# Segment metadata omits versions of classes that have no instance

## Expectation

Each class in the type closure of a segment profile has a version in the segment metadata. The reader can then select one exact schema for each class.

## Actual behavior

Segment metadata lists only the classes that have records in that segment. A class can appear in the type closure only through a reference type, a value type or a base chain. That class then has no metadata row. If the catalog holds two versions of that class, the reader cannot select one of them.

After `TransientEntityHolder` entered the catalog, `CloseCatalog` reached `BaseOccurrencePathValue` through `ComponentPostOffice` and `PostOfficeDataValue`. The catalog holds versions 4 and 5 of that class, and the read failed with `ValueError("Unqualified Fusion native class or schema version")`.

Six classes have two catalog versions. In each pair, the newer version is the current registration in Fusion 2706.1.17:

| Class | Catalog versions | Current registration |
| --- | --- | --- |
| `DcDraftFeature` | 5, 6 | 6 |
| `DRMatrix` | 15, 16 | 16 |
| `Parameter` | 9, 10 | 10 |
| `ComponentBaseInstance` | 10, 11 | 11 |
| `BaseOccurrencePathValue` | 4, 5 | 5 |
| `PMISettings` | 2, 4 | 4 |

## Workaround

When the metadata has no row for a class, `PickSchema` selects the newest catalog version. That class has no record in the segment, so the selection cannot change decoded bytes. When the metadata gives a version, `PickSchema` requires that exact version and raises `ValueError` for an unknown version. `TestNewestPick` and `TestUnknownPick` cover both rules.

## Evidence

- [Native version differences](../../../../../re/Fusion/LocalOracle/Reflection/VersionDifferences.json)
- [Version selection](../../../../../src/convert/formats/Fusion/EntityCodec/Vocabulary/PickSchema.py)
- [Class gap census script](../../../../../re/Fusion/Reconstruction/ReaderCoverage/ClassGaps.py)
- [Change entry](../../../../Changes/Fusion/Records/FusionSavedDocumentCoverage.md)
