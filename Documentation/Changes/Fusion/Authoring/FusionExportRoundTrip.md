# A Kit-authored design survives a Fusion export and reads back identically

## Problem

The save-and-reopen leg was unproven. `DataFile.isReadOnly` is true on this Personal Use license, and
`saveAs` returns `True` and produces no file for a design (240 s), a drawing (900 s), or a design
imported into a new document (300 s). The limit is on the account, so a cloud save cannot be used to
show that a Kit-authored file survives a write by Fusion.

## Change

Fusion can export a design to a local F3D without a cloud save, through
`Design.exportManager.createFusionArchiveExportOptions` and `execute`. That is Fusion's own writer
producing a file from the model it built when it opened Kit's file, so it exercises the same
serialization path a save would.

`ExportDesign.py` runs the loop:

1. import Kit's authored F3D with `importManager.importToNewDocument`
2. export the imported design to a local F3D with `Design.exportManager`
3. read Fusion's export back with Kit

## Behavior

Source: `KitAuthoredCylinder.f3d`, written by Kit from a `DocumentSpec`.

| Step | Result |
| ---- | ------ |
| Kit writes the design | 84187 bytes |
| Fusion imports it | `kitLength` `40.0 mm`, 1 body, 19.634954084935366 cm³ |
| Fusion exports it | 54756 bytes, `export_started` `True` |
| Kit reads Fusion's export | `kitLength` `40.0 mm`, `d2` `kitLength`, `d3` `0 deg`, 1 body |
| Fusion reopens its own export | 1 body `Kit Body`, 3 faces, 2 edges, 2 vertices, 19.634954084935366 cm³ |

The parameters survive exactly, including the formula reference `d2 = kitLength`, which is a
parameter that points at another parameter rather than a number.

The geometry survives too. Both files read back as the same model:

```
kit authored   CylinderBody(Radius=12.5, Height=40.0, BasePoint=(0.0, 0.0, 0.0))
fusion export  CylinderBody(Radius=12.5, Height=40.0, BasePoint=(0.0, 0.0, 0.0))
```

`pi * 12.5^2 * 40` is 19634.95 mm³, which is the 19.634954084935366 cm³ Fusion reported on import.

Fusion's export also reopens in Fusion with the same volume to the last digit, and with the body name
Kit wrote:

```
Kit Body   faces 3   edges 2   vertices 2   volume 19.634954084935366 cm3
parameters kitLength 40.0 mm, d2 kitLength, d3 0 deg
```

So the loop closes in both directions: Kit writes, Fusion reads and writes, Fusion reads again, and
Kit reads Fusion's output. The volume is identical at every step.

## Verification

The run is recorded in `Out/Designs/ExportKitAuthoredCylinder.json` with `status` `accepted`. Fusion
2706.1.17 imported the file, exported 54714 bytes, reopened that export, and reported the same
parameter and the same volume.

`ExportDesign.py` gates on the reopen rather than recording success from the import alone. It
compares the reopened expression, body count and volume against the imported ones and raises if any
differs, so a lost parameter or a lost body fails the run instead of passing it.

## Limits

This is a local export, not a cloud save. It shows that Fusion can serialize a design it built from
Kit's file and that Kit reads the result, which is what the save leg was for. It does not show that a
cloud save succeeds, because the account cannot perform one.

The export is Fusion's own output, so it is not a byte comparison against Kit's file. The two files
differ in size because Fusion rewrites the document in its own layout.
