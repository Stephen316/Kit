# A saved Kit root ends its Design stream with padding

## Expectation

Each record of a Design `BulkStream.dat` ends where the next record starts.
The last record ends at the end of the stream.

## Actual behavior

Fusion saved the uploaded Kit root `KitAsmRoot` as version 2.
Each Fusion export of that version ends the Design stream with 10 bytes after the last record.
The last record is the continuation of a new `VisualAnalyses` record, which Fusion added on save.
That continuation has 5 bytes of fields, as in native designs.

| Export | Design stream bytes | Trailing bytes | Same trailing bytes as the first export |
| --- | --- | --- | --- |
| `AcceptedKitAsmRoot.f3d` | 17,946 | 10 | Yes |
| `ReexportFirstKitAsmRoot.f3d` | 17,946 | 10 | No |
| `ReexportSecondKitAsmRoot.f3d` | 17,946 | 10 | No |

The last two exports came from one opened document.
Their trailing bytes differ from the first export, so they are not record data.
The trailing bytes of the first export are 8 zero bytes and then `c7cb`.
In the native controls, the `VisualAnalyses` continuation is not the last record and has no extra bytes.

Before the fix, `ReadDocument` raised `Unexplained trailing Fusion entity payload bytes` for these exports.
Fusion itself opened, updated, saved and opened the root again without errors.

## Workaround

Kit keeps at most 16 trailing Design bytes as `ParsedSegment.BulkSlack`.
`EmitDocSegment` writes them back after the last record, so the stream stays byte-equal.
A longer Design tail still raises `ValueError`.
The Browser stream keeps the strict check.

| Stream | Trailing bytes kept |
| --- | --- |
| ACT | Any number |
| Design | 0 to 16 |
| Browser | 0 |

`KMaxDesignSlack` in `SlackLimit.py` holds the Design limit.
Kit does not interpret these bytes.

## Evidence

- [Assembly authoring acceptance](../../../../../re/Fusion/LocalOracle/LinksConfigs/AsmAcceptance.json), key `fusion_exports`
- [Export script](../../../../../re/Fusion/LocalOracle/LinksConfigs/ReexportAsmRoot.py)
- [Saved root fixture](../../../../../re/Fusion/LocalOracle/LinksConfigs/Fixtures/KitAsmRootSaved.f3d), a sanitized copy of `AcceptedKitAsmRoot.f3d`
- [Saved root tests](../../../../../tests/convert/formats/FusionCodec/Links/SavedRootTests.py)
- [Slack tests](../../../../../tests/convert/formats/FusionCodec/Documents/Act/ActSlackTests.py)
- [Assembly authoring change](../../../../Changes/Fusion/Assembly/FusionAssemblyAuthoring.md)
