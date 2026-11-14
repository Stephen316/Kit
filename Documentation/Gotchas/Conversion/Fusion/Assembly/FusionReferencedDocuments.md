# Opening a root also opens referenced designs

## Expectation

`Documents.open` of one assembly adds one item to `Application.documents`.

## Actual behavior

The root `KitLinkRoot` references Part A and a subassembly, and the subassembly references Part B.
After `Documents.open` of the root, `Application.documents.count` was 4.
The script then closed only the root and one other part that it had made.
The final count was 0.

## Workaround

Record `Application.documents.count` after each open.
Close each document that the script opened.
Check `documents_after == 0` at the end of the script.
If the count is not 0, close the remaining documents that have the `KitLink` name prefix.

## Evidence

- [Configuration control script](../../../../../re/Fusion/LocalOracle/LinksConfigs/CreateConfigControls.py), field `link_documents_open`
- [Clean-up script](../../../../../re/Fusion/LocalOracle/LinksConfigs/CloseLinkDocs.py)
