# A read-only cloud file accepts a save and never saves

Fusion 2706.1.17 with a Fusion for Personal Use license limits the number of editable documents.
`DataFile.isReadOnly` is `True` for a file beyond that limit.
A save of such a file does not raise an error.

| Observation                                           | Value                               |
| ----------------------------------------------------- | ----------------------------------- |
| Kit acceptance projects before any deletion           | 37 files, 10 editable, 27 read-only |
| `M1Reemitted` files, listed after the failed save    | Design editable, drawing read-only  |
| `Document.save()` on the read-only drawing            | Returned `True`                     |
| New drawing version within 300 seconds                | None                                |
| `Document.save()` on a read-only design               | Returned `True`, and no new version |
| Limit message returned to the script                  | None                                |
| Fusion log lines on read-only access for these files  | None                                |
| `saveAs` on a read-only authored design, 240 seconds  | Returned `True`, and no new file    |
| `saveAs` on a read-only authored drawing, 900 seconds | Returned `True`, and no new file    |
| `saveAs` on a freshly imported design, 300 seconds    | Returned `True`, and no new file    |

Deleting old Kit acceptance documents did not make new uploads editable.

| Attempt | Editable before | Deleted             | Editable after | New design and drawing |
| ------- | --------------- | ------------------- | -------------- | ---------------------- |
| 1       | 10              | 1, and 1 refused    | Not listed     | Both read-only         |
| 2       | 9               | 1                   | 8              | Both read-only         |

The counts cover only the Kit acceptance projects, because the runs did not read other projects.
The server refused one deletion with `GEN_RELATED_OBJECTS`, because the file had relationships.

The same stall holds for a file that Kit authored and uploaded, so it is a property of the read-only
upload and not of the file contents.

Importing the same F3D into a new document with `importManager.importToNewDocument` does not help.
The imported document reports the authored parameter and the exact body volume, and its `saveAs`
still returns `True` and produces no file in 300 seconds. The limit is on the account, not on how the
document arrived.
An authored design still opens and still accepts a parameter edit, so an unattended run can verify
open and edit on a read-only upload and cannot verify a save.

Check `DataFile.isReadOnly` before a save in an unattended run.
Otherwise the script waits for a version that never appears.

The [native acceptance report](../../../../../re/Fusion/Reconstruction/Drawings/NativeAcceptance.json) records both attempts under `capacity` and `saved_edit`.
