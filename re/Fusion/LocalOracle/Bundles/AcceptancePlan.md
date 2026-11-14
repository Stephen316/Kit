# F3Z native acceptance preparation

## Prepared artifact

The production call chain was `ReadBundle(source_bytes)` followed by `EmitBundle(typed_bundle)`.
Preparation ran once to produce the artifact for the authorized native acceptance step.
It did not execute integration tests, perform native calls, or upload files.

| Item | Value |
| --- | --- |
| Source | `re/Fusion/examples/.f3z/example1.f3z` |
| Source SHA-256 | `e14866ac96457805a93e63fa269beb4dc8c69caa80c819de4a195db45ccc23c6` |
| Output | `re/Fusion/LocalOracle/Bundles/kit_production_example1.f3z` |
| Output SHA-256 | `33a42876f25ecc72844cf37af3ab35cb17ed6bfe621ff4e21ce4b3a62c6afe54` |
| Output bytes | 9,295,119 |
| Documents | 9 |
| XREF relationships | 8 |
| Root object | `1545802` |
| Root member | `3cb733fc-f1dc-4b67-ae97-9c7b04d8aa2f.f3d` |

[Preparation.json](Preparation.json) records all document member digests.
[PrepareBundle.py](../PrepareBundle.py) reproduces the artifact from the production API.
The fresh ZIP and JSON envelope wraps explicit complete source document bytes.
This experiment verifies the bundle envelope, not independent generation of the nine nested F3D documents.

## Read-only native inventory

[InspectBundleProjects.py](../InspectBundleProjects.py) is prepared but has not been run by this agent.
The parent coordinates its execution through the existing native script channel.
Its first parent-run invocation failed when `Data.activeProject` raised `RuntimeError: 2 : InternalValidationError : id.size()`.
The corrected script records that optional-selection failure and continues enumeration.
The initial report was preserved locally as `ProjectInventory.InitialFailure.json`.
It records Fusion version, offline state, document count, accessible hubs, project identities, root folders, and upload API contracts.
It does not open documents, enumerate project contents, create projects, change the active hub, or upload anything.
It writes `ProjectInventory.json` locally.

The selected hub must be identified explicitly from that inventory.
An active hub is observable context, not proof of permission to change arbitrary existing projects.

## Minimal isolated cloud route

1. Verify the prepared artifact's SHA-256 before native work.
2. Select one accessible hub by its recorded ID without changing the active hub.
3. Create a uniquely named project through that hub's `dataProjects.add` method.
4. Use a name such as `Kit Fusion Codec Acceptance 33a42876f25e` with a fresh timestamp suffix.
5. Set the purpose to the bounded F3Z envelope acceptance experiment and leave contributors empty.
6. Record the returned project and root-folder IDs before upload.
7. Upload only the prepared F3Z through the new root folder's `uploadFile` method.
8. Run upload outside command transactions and retain the returned `DataFileFuture`.
9. Observe `uploadState` until `UploadFinished` or `UploadFailed`, with a finite timeout and periodic persisted status.
10. Obtain the resulting `dataFile` only after successful completion.
11. Wait for its cloud processing to complete before opening it.
12. Record the resulting document identity and all resolved child-reference identities.
13. Verify that the imported children belong to the newly created project.
14. Open the uploaded root and record assembly contents, reference resolution, component names, and feature health.
15. Close only the document opened by this experiment and restore the previous active document if needed.

The new project isolates experiment data from existing projects.
Its access control still follows the selected hub's settings; an empty contributor list does not establish private access.
No automatic invite, deletion, project reuse, or cleanup operation is included.
A failed upload must preserve the recorded job and destination evidence rather than retry into a different project.

Parent coordination is required before any cloud mutation.
No project or upload has been created during artifact preparation.

## Acceptance boundaries

A generated ZIP is only the input artifact.
Upload completion establishes server ingestion, while opening the root establishes document loadability.
Resolved child references establish that the embedded documents were rebound together.
Feature edits, rebuilds, save, and reopen remain additional acceptance observations where supported by this multi-document specimen.
Preservation of the supplied nested payloads does not establish a nested F3D conversion capability.

## Public API sources

- [F3D-only archive import and F3Z upload direction](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_ImportManager_createFusionArchiveImportOptions.htm).
- [Upload method and command-transaction restriction](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataFolder_uploadFile.htm).
- [Project creation in a specified parent hub](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataProjects_add.htm).
- [Hub project collection](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataHub.htm).
- [Asynchronous upload result](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataFileFuture.htm).
- [Cloud processing completion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataFile_isComplete.htm).
- [Resolved child document references](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataFile_childReferences.htm).
- [Opening the uploaded document](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Documents_open.htm).

The installed API definitions also expose `UploadProcessing=0`, `UploadFinished=1`, and `UploadFailed=2`.
They were read as source text without importing the native API.

## Static environment

The passing Pyright invocation used the repository root as its working directory:

```sh
uv run --python 3.14 --no-project --with 'pyright==1.1.414' --with 'pytest==9.1.1' python -m pyright src/convert/formats/Fusion/BundleCodec tests/convert/formats/FusionCodec/Bundles
```

Both Pyright and Pytest are installed in the same temporary `uv` Python environment.
The command performs static analysis only and does not collect or execute tests.
No custom `PYTHONPATH` was needed for that static command.
