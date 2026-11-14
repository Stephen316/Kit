# F3Z uses asynchronous upload

## Expectation

`createFusionArchiveImportOptions` appears suitable for both Fusion archive extensions, F3D and F3Z.

## Actual behavior

The public API explicitly supports F3D only.
Its documentation directs F3Z callers to `DataFolder.uploadFile`.
The upload method returns a `DataFileFuture` before the upload completes.
It cannot run inside a command event because that event has an open transaction.

This restriction comes from the official API contract.
The later production bundle acceptance followed this upload route successfully. Its [native report](../../../../re/Fusion/LocalOracle/Bundles/NativeBundleAcceptance.json) records root opening, rebuild, parameter edit, cloud save, and reopen.

## Workaround

Use `DataFolder.uploadFile` with an explicitly selected destination folder.
Run the operation outside command transactions.
Observe its future until the upload completes or fails, then inspect the resulting design.
Do not treat a successfully created local ZIP as native acceptance evidence.

## Evidence

- [Official Fusion archive import method](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_ImportManager_createFusionArchiveImportOptions.htm).
- [Official asynchronous upload method](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataFolder_uploadFile.htm).
- [Bundle envelope codec](../../../Changes/Fusion/FusionBundleCodec.md).
