# A DWG that Kit authors does not finish opening in Fusion

Fusion 2706.1.17 did not finish opening any drawing whose DWG Kit authored.
`Documents.open` did not return, and Fusion showed no dialog.
Only a restart released it.

| Variant             | DWG                                                      | Waited before restart |
| ------------------- | -------------------------------------------------------- | --------------------- |
| `K1SheetOnly`       | Authored sheet without views                             | Stopped by hand       |
| `S5SheetDimension`  | Authored sheet with one dimension                        | 602 s                 |
| `T5SheetDimension`  | `S5SheetDimension` with the AppInfo of a Fusion save     | 307 s                 |
| `U12AuthoredShellShorts` | `H1NoAcm` objects in Kit's shell                    | 460 s                 |

The Kit-built F2D members are not the cause.
`N2AuthoredF2d` wraps the Fusion-saved `H1NoAcm` DWG in Kit-built members, and it opened in 4.3 s with 3 views and 1 dimension.

Two parts of the authored DWG stop the open.
The first is the four header values that the [header tail gotcha](FusionDrawingHeaderTail.md) records.

The second is the missing Autodesk trusted-file text.
A Fusion save carries the text `Autodesk DWG.  This file is a Trusted DWG last saved by an Autodesk application or Autodesk licensed application.` in two places.
One is an AppInfo entry, and the other is an `AcDb:AppInfoHistory` entry.
The open stalls when neither section carries the text.

## Pairwise bisection

Each variant below is `Q1NoDataStore` with one part of Kit's shell, and each kept the A1 header values.

| Variant            | Part taken from Kit's shell                         | Result                           |
| ------------------ | --------------------------------------------------- | -------------------------------- |
| `Q8AuthoredSections` | Section set without `AcDb:Preview` and `AcDb:AppInfoHistory` | Opened in 5.2 s      |
| `W1KitAppInfo`     | One Kit product entry, without the trusted-file entry | Opened in 4.7 s                |
| `W3KitAuxHeader`   | Auxiliary header with a save count of 1             | Opened in 3.5 s                  |
| `W4KitSummary`     | Summary with empty texts                            | Opened in 3.4 s                  |
| `W5KitFreeSpace`   | Object free-space record                            | Opened in 6.1 s                  |
| `W6KitClassCounts` | Class instance counts recounted from the objects    | Opened in 3.6 s                  |
| `U4AuthoredShellTail` | All of the above together                        | Not open after 185 s, no dialog  |

The pairs start from `Q8AuthoredSections` and add Kit's parts to it.

| Variant           | Parts added to `Q8AuthoredSections`                                  | Result               |
| ----------------- | -------------------------------------------------------------------- | -------------------- |
| `Y0`              | None                                                                 | Opened in 4.9 s      |
| `YX`              | Kit auxiliary header                                                 | Opened in 3.6 s      |
| `YS`              | Kit summary                                                          | Opened in 3.2 s      |
| `YAX`             | Kit AppInfo and Kit auxiliary header                                 | Not open after 184 s |
| `C7AppOnly`       | Kit AppInfo                                                          | Not open after 61 s  |
| `C1AppNoTrust`    | The Fusion product entry without the trusted-file entry, Kit auxiliary header | Not open after 61 s |
| `C2AppKitProduct` | Kit's product entry and the trusted-file entry, Kit auxiliary header | Opened in 3.5 s      |

The interacting pair is Kit's AppInfo and Kit's section set.
`W1KitAppInfo` opened because its `AcDb:AppInfoHistory` still carried the trusted-file text.
`Q8AuthoredSections` opened because its AppInfo still carried it.
Together they remove both copies.

The product entry does not matter.
`C2AppKitProduct` names Kit as the product and opened.
`C1AppNoTrust` names Fusion Drawings as the product and stalled.
The auxiliary header, summary, free space and class counts do not matter either.

## What Kit does

The trusted-file text states that an Autodesk application saved the file.
Kit does not write it, in AppInfo, in `AcDb:AppInfoHistory` or anywhere else.
Kit writes one AppInfo entry that names Kit as the product.
Fusion 2706.1.17 therefore does not open a DWG that Kit authors, even with valid header values.
