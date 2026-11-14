# The Fusion root count includes free faces and free edges

## Expectation

The `RootCount` field of an `.smb` or `.smbh` header is one more than the number of `body` records. Each live face has a shell, each live edge has a coedge, and each body has a lump.

## Actual behavior

Some saves keep a construction face or a selected edge as a top-level entity. Kit raised a root-count error for 13 files. Kit raised `ValueError("Missing required Fusion topology reference")` for an unstitch save.

A top-level entity is one of these records.

| Record | Null reference |
| --- | --- |
| `body` | None, or lump and wire for an empty body |
| `face` | Shell, token 5 |
| `edge` | Coedge, token 7 |

In every readable `.smb` and `.smbh`, `RootCount - 1` is the number of top-level entities. Free faces and free edges always occupy root slots 1 to `RootCount - 1`. This is also true in every older journal state. A free edge has no coedge use. The unstitch journal keeps the original body empty, without a lump or a wire.

## Workaround

Use `CountRoots` to count bodies, faces without a shell, and edges without a coedge. Compare this count with `RootCount - 1`. Accept a null body lump, face shell, or edge coedge only in a root slot. Skip the use-pair check for a free edge that no coedge uses.

## Evidence

- [Root lists](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/RootLists.json)
- [Null references](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/NullRefs.json)
- [Census delta](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/CensusDelta.json)
