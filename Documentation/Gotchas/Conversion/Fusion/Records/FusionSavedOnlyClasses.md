# Classes that only Fusion saves must stay out of authored documents

## Expectation

The reader and the author can share one class vocabulary. A class that you add for reading then also becomes available to the author.

## Actual behavior

`AuthorSchemas` writes every schema in `DesignClasses.json` into the class table of an authored Design segment. Fusion 2706.1.17 saves two classes that Kit does not author:

| Class | Version | Corpus files | Records |
| --- | --- | --- | --- |
| `TransientEntityHolder` `D87EC2D8-35C1-4AA2-A308-09AF07C490FF` | 0 | 21 | 21 |
| `DcDraftFeature` `F4163A07-9E71-4C46-BD92-ACE5B5B40BED` | 6 | 7 | 7 |

If these classes go into `DesignClasses.json`, every authored document gets two more class rows. The accepted authored bytes then change.

The native registration of `TransientEntityHolderMetaType` has no initialized own member set. Its base is `98542EB9-A4F2-4137-A808-DBB5B3CD6159`. All 21 saved records decode with zero own fields, and the strict reader finds no unread bytes.

## Workaround

Put a class that only Fusion-saved documents use in `SavedClasses.json`. `ReadDocSchemas` reads that file. `AuthorSchemas` does not read it. Keep a class in `DesignClasses.json` only when Kit authors that class. `TestAuthorScope` checks that the two classes stay out of the cuboid, rectangle and default author vocabularies.

## Evidence

- [Saved class vocabulary](../../../../../src/convert/formats/Fusion/DocumentCodec/Vocabulary/SavedClasses.json)
- [Native registration versions](../../../../../re/Fusion/LocalOracle/Reflection/Versions.json)
- [Native version differences](../../../../../re/Fusion/LocalOracle/Reflection/VersionDifferences.json)
- [Native acceptance of re-emitted saves](../../../../../re/Fusion/LocalOracle/ReaderCoverage/NativeAcceptance.json)
- [Change entry](../../../../Changes/Fusion/Records/FusionSavedDocumentCoverage.md)
