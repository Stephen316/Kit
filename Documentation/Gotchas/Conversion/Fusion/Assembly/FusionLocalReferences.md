# Local import refuses files with external references

## Expectation

`ImportManager.importToNewDocument` opens any F3D that Fusion exported, as for single-part acceptance.

## Actual behavior

Fusion 2706.1.17 refused the Kit replay of the saved root `R5_saved`.

```text
RuntimeError: 3 : New design cannot be created from a local file containing external references
```

The source control and the Kit output both contain two root manifest links.
Fusion did not open a document, and the script ended with 0 open documents.

## Workaround

Upload the F3D to a cloud folder with `DataFolder.uploadFile`.
Wait until the uploaded `DataFile` is complete, then open it with `Documents.open`.
Use a dedicated acceptance folder for these uploads.

## Evidence

- [Local import attempt](../../../../../re/Fusion/LocalOracle/LinksConfigs/AcceptLinkReplay.py)
- [Upload start script](../../../../../re/Fusion/LocalOracle/LinksConfigs/BeginLinkUpload.py)
- [Native acceptance report](../../../../../re/Fusion/LocalOracle/LinksConfigs/LinkAcceptance.json), run `Accept1`
