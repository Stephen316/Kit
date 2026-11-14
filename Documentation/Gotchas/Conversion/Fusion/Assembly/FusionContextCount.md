# The MetaStream reserved word counts version contexts

## Expectation

The 32-bit word after `NextId` in `MetaStream.dat` is a reserved value that is always 0.

## Actual behavior

The word is 0 only in a design without external references.
In a design with external references, the word is the number of version contexts.
The contexts follow the word, before the property list.

| Context field | Wire type | Content |
| --- | --- | --- |
| `Token` | 64-bit integer | Key that `CrossRef` values use |
| `LinkId` | UTF-16 text | Root manifest link GUID |
| `RevisionId` | UTF-16 text | Revision GUID of the referenced design |
| `VersionUrn` | UTF-16 text | Version URN of the referenced design |
| `AssetId` | UTF-16 text | Asset GUID of the referenced design |
| `SegmentId` | 32-bit word | 0 for Design and Browser, 1 for ACT |

The previous reader kept the word as an opaque value.
It then read the first context bytes as the property list.

## Workaround

Read the word as a count and read that number of contexts.
`CheckWireBody` raises `Fusion version context count disagrees` when `MetaSegment.Reserved` differs from the context count.

## Evidence

- [Context reader](../../../../../src/convert/formats/Fusion/SegmentCodec/Metadata/ReadMetaCtx.py)
- [Fixture replay tests](../../../../../tests/convert/formats/FusionCodec/Links/LinkArchiveTests.py), cases `TestLinkTables` and `TestLinkTokens`
- [External references change](../../../../Changes/Fusion/Assembly/FusionExternalReferences.md)
