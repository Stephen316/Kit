# A reference update makes a new link

## Expectation

`Document.updateAllReferences` changes only the version of an existing link.

## Actual behavior

The update replaced the link of the updated design with a new link.
The controls `R6_out_of_date` and `R7_updated` show the change.

| Item | Part A link before update | Part A link after update | Subassembly link |
| --- | --- | --- | --- |
| Link GUID | Old GUID | New GUID | Unchanged |
| `URL` suffix | `?version=1` | `?version=2` | `?version=1` |
| `linkClassification` | `OriginalDesign` | Absent until the next save | `OriginalDesign` |
| Design and Browser context token | Old token | New token | Unchanged |
| ACT context token | Old token | New token | Unchanged |

Every `CrossRef` that points into the updated design uses the new tokens.
The update also wrote a new `ACTRefdTable` record for Part A, object 16 instead of object 10.
Its `referenceCount` was 1 in `R7_updated` and `R8_updated_saved`, and 2 in the later export `R9_archive`.

## Workaround

Do not use a link GUID or a context token as a stable key across versions.
Use the lineage URN from the link properties to identify the referenced design.
Write the link GUID, the asset row, the contexts and the `CrossRef` tokens as one consistent set.

## Evidence

- [Fixture replay tests](../../../../../tests/convert/formats/FusionCodec/Links/LinkArchiveTests.py), case `TestLinkUpdate`
- [Native controls](../../../../../re/Fusion/LocalOracle/LinksConfigs/LinkEvidence.json)
- [External references change](../../../../Changes/Fusion/Assembly/FusionExternalReferences.md)
