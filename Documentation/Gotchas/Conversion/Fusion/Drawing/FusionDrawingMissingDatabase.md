# Fusion cannot open a drawing without its DWG

Fusion 2706.1.17 does not rebuild a drawing from its entity segments.
It needs the embedded DWG member `Dwg.BlobParts/ExtFile.<guid>.dwg`.

The `P2NoDwg` variant kept the A1 control package and removed only that member.
Fusion accepted the upload and then failed to open the drawing.

| Observation                         | Value                                                                    |
| ----------------------------------- | ------------------------------------------------------------------------ |
| Engine input folder                 | Body SAB, `compmeta.json` and settings, with no `Document1.dwg`          |
| Dialog title                        | `Fusion Drawings Message`                                                |
| Dialog text                         | `Cannot find the specified drawing file. Please verify that the file exists.` |
| Fusion main thread with the dialog  | `Nu::MessageBox::show`, called back from the drawing engine              |
| Engine session header in its log    | Not written                                                              |
| After the dialog was dismissed      | Fusion logged the document as opened after 240 seconds                   |
| `Documents.open` after dismissal    | Still waiting in `DrawingDocument::waitForOpenToComplete`                |

The modal dialog blocks a script, because `Documents.open` does not return while it is shown.
After dismissal, the open still did not return, so only stopping Fusion released the oracle.

`ReadDrawing` and `EmitDrawing` accept a drawing without a DWG, because the test fixtures omit it.
Keep the DWG member in any drawing that Fusion must open.

The [native acceptance report](../../../../../re/Fusion/Reconstruction/Drawings/NativeAcceptance.json) records this run under `missing_database`.
