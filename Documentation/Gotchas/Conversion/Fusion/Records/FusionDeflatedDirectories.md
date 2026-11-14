# Fusion opens archives with deflated empty directory entries

## Expectation

Fusion writes each directory entry as a stored entry with zero bytes. The reader can then reject any other directory entry.

## Actual behavior

All 1,955 directory entries in the Fusion-saved `vendor_*.f3d` archives use method 0 with zero compressed bytes. Python `zipfile` writes a directory entry in a deflated archive with method 8. That entry holds the 2-byte empty Deflate stream and zero uncompressed bytes.

Twelve Kit-prepared archives use that deflated layout for all 146 of their directory entries. These are the eight `JournalStates/*History.f3d` archives and the four `PlanarTopology` permuted and production archives. Fusion 2706.1.17 opened, rebuilt, edited, saved and reopened them. The reader rejected all twelve with `ValueError("Fusion container directories must be empty and stored")`.

## Workaround

`ReadContainer` accepts a directory entry with zero size and zero CRC when it is stored with zero compressed bytes. It also accepts a deflated directory entry with 2 compressed bytes. Any other directory entry still raises `ValueError`. `TestFolderRule` reads a deflated layout. `TestFoldReject` changes one directory to stored with 2 compressed bytes and checks the rejection.

## Evidence

- [Container reader](../../../../../src/convert/formats/Fusion/ContainerCodec/ReadContainer.py)
- [Journal state acceptance](../../../../../re/Fusion/LocalOracle/JournalStates/NativeProductionAcceptance.json)
- [Planar topology acceptance](../../../../../re/Fusion/LocalOracle/PlanarTopology/NativeAcceptance.json)
- [Native acceptance case `DeflatedFolders`](../../../../../re/Fusion/LocalOracle/ReaderCoverage/NativeAcceptance.json)
- [Directory entry gotcha](../FusionArchiveDirectories.md)
- [Change entry](../../../../Changes/Fusion/Records/FusionSavedDocumentCoverage.md)
