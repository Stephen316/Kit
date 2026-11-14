# A save returns before the new version exists

## Expectation

`Document.save` returns after Fusion makes the new cloud version.
`Document.dataFile` then shows the new version number.

## Actual behavior

`Document.save` returned `True` before the new version existed.
The `DataFile` object of the open document kept version 1 in each observed run.

| Run | Wait after save | Version check | Result |
| --- | --- | --- | --- |
| `Accept2` | 300 s, then close | `Document.dataFile.versionNumber` | Version 1 in both files. Later folder listings still showed version 1. |
| `SaveProbe` | Up to 420 s, document open | New folder lookup | Version 2 of `KitLinkMovedR1` |
| `Accept2_saves` | Up to 600 s, document open | New folder lookup | Version 2 of `KitLinkReplayR5` |

`DataFile.isReadOnly` was `True` for both uploaded files at the start of a run.
This flag did not prevent the new versions in `SaveProbe` and `Accept2_saves`.

## Workaround

Keep the document open after `Document.save`.
Look up the `DataFile` again in its folder and wait until its version number increases.
Then close the document and open the latest `DataFile` from the folder.
Do not use the return value of `Document.save` as proof of a new version.

## Evidence

- [Save probe script](../../../../../re/Fusion/LocalOracle/LinksConfigs/ProbeLinkSave.py)
- [Save acceptance script](../../../../../re/Fusion/LocalOracle/LinksConfigs/AcceptLinkSaves.py)
- [Native acceptance report](../../../../../re/Fusion/LocalOracle/LinksConfigs/LinkAcceptance.json), runs `Accept2`, `SaveProbe` and `Accept2_saves`
