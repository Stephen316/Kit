# Fusion drawing documents

This is a draft section for the [Fusion data model](../../../../Documentation/Reference/Research/FusionDataModel.md).
It describes modern F2D drawings, the historical drawing example and drawing-root F3Z bundles.
The evidence is the Kit drawing controls, the installed historical example and native runs in Fusion 2706.1.17.

## Package layer

An F2D file is a ZIP package with contiguous entries, no extra fields and no archive comment.
Kit reproduces every observed entry with these layouts.

| Entry kind                         | Method          | Flags  | Creator | Extract | External attributes |
| ---------------------------------- | --------------- | ------ | ------- | ------- | ------------------- |
| Directory                          | 0               | 0x0800 | 814     | 10      | 0x41ED0010          |
| Modern file                        | 93 (Zstandard)  | 0x0800 | 814     | 20      | 0x81A40000          |
| Modern `ComponentReferenceData.json` | 0             | 0x0800 | 814     | 20      | 0x81A40000          |
| Historical directory               | 0               | 0x0000 | 814     | 10      | 0x41FD0010          |
| Historical file                    | 8 (Deflate)     | 0x0000 | 814     | 20      | 0x81B40000          |

Deflate members use level 6 with a raw window of 15 bits and memory level 8.
Zstandard members use level 3, a checksum and no content size.
The [frame gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Drawing/FusionDrawingZstdFrames.md) explains the dependency on the encoder build.

## Members

The active asset folder of a modern drawing is `Documentation[Active]/`.

| Member                                               | Content                                         |
| ---------------------------------------------------- | ----------------------------------------------- |
| `Manifest.dat`                                       | Root manifest, version 20                       |
| `Properties.dat`                                     | Document properties                             |
| `ComponentReferenceData.json`                        | Component references, `{}` in the controls      |
| `Documentation[Active]/Manifest.dat`                 | Asset manifest, version 20                      |
| `Documentation[Active]/DrawingManifest.json`         | Active sheet, sheet size, standard, units, zones |
| `Documentation[Active]/AutomationSettings/*.json`    | Nine drawing automation settings                |
| `FusionDrawingDesignSegmentType1/`                   | Drawing entity segment, metadata and bulk       |
| `FusionDrawingACTSegmentType1/`                      | Drawing ACT segment, metadata and bulk          |
| `Dwg.BlobParts/ExtFile.<guid>.dwg`                   | Embedded AutoCAD database                       |
| `SheetThumbnails/*.png`, `Previews/small.png`        | Sheet and document images                       |

The historical example uses `Design1/` for its single entity segment.
It also has a root `RedirectionsStream.dat` and no sheet or settings members.

## Manifests

The modern root manifest has magic 1234 and version 20.
It stores a 64-bit software word and an optional save label after the document name.
The legacy root manifest has version 10 and a 32-bit software word.
Each legacy reference row has an extra unresolved string.

| Value in the Kit controls | Root manifest                     | Asset manifest                                  |
| ------------------------- | --------------------------------- | ----------------------------------------------- |
| Modules                   | `("Application", 2)`              | `("Application", 4)`, `("Server", 36)`          |
| Software word             | 3046685422794047505               | Not present                                     |
| Kind                      | Not present                       | `Neutron3DAssetType`                            |
| Link word, allocation     | Not present                       | 1, 3                                            |
| Change word               | Not present                       | 8                                               |
| Segments                  | Not present                       | Design segment 0, ACT segment 1                 |

The root reference row joins the drawing to its design.
Its properties include the design display name, version URL and lineage URN.
Its three paths are workstation cache paths, so they are private values.

## Entity segments

Both modern segments use the ordinary metadata and bulk grammar.
A drawing-specific vocabulary adds 14 class schemas to the design catalog.
`BuildVocabulary.py` generates it from the native reflection dump with SHA-256 `947d0a61e2e68b00b6fb57579cc8b4e8318de44080b2ab275526c132688f2187`.

| Class                         | Version | Typed content in the controls                              |
| ----------------------------- | ------- | ---------------------------------------------------------- |
| `FusionDocExternalFileRefs`   | 12      | References to model sources, sheets and tracked entities   |
| `ExtFileSerializer`           | 0       | `persistedFileName`, the DWG member name                   |
| `FusionDocSheets`             | 2       | `activeSheetId` `2E50`                                     |
| `FusionDocSheet`              | 4       | Sheet identity, order, thumbnails and title-block path     |
| `FusionDocModelSources`       | 3       | Next identifiers and the last model source                 |
| `FusionDocModelSource`        | 12      | Design link name, source identifier, sheet list, filters   |
| `TrackedEntity`               | 0       | One record for each tracked model element                  |
| `TrackedBrep`                 | 1       | Body persistent identifier and version                     |
| `TrackedOccurrence`           | 2       | Occurrence scope                                           |

`FusionDocModelSource.animationMarker` is a native `std::pair<std::wstring,double>`.
Kit reads it as a pair of a UTF-16 string and a double.
All three controls store an empty string and 0.0.

`FusionDocComponentFilterValue.comps` maps `BaseOccurrencePathValue` keys to `FusionDocComponentState` values.
The value type has no reflected members, so Kit cannot decode a non-empty map.
The controls store an empty map.
The drawing profile selects `BaseOccurrencePathValue` version 5, which is the reflected current version.

Classes of the other segment are selected at the version that its own metadata declares.
A drawing has the same class at two versions in the catalog, so a version-free choice is ambiguous.

| Control      | Design primaries | ACT primaries | Tracked entities | Native dimensions          |
| ------------ | ---------------- | ------------- | ---------------- | -------------------------- |
| A0 views     | 39               | 5             | 1                | 0                          |
| A1 dimension | 51               | 5             | 3                | 1                          |
| A2 automatic | 69               | 5             | 6                | 3                          |

No segment class stores a view, a view curve or a dimension.
The segments store the model link and tracked model elements.
Adding one dimension to the A0 drawing raised the tracked-entity count from 1 to 3.

## Embedded database

The DWG holds the sheet layout, the views and the annotations.
The modern controls declare `AC1032`, and the historical example declares `AC1027`.
`ReadDwgFile` decodes the whole file into a typed `DwgFile`, with the [Open Design Alliance DWG specification](https://www.opendesign.com/files/guestdownloads/OpenDesign_Specification_for_.dwg_files.pdf) as the format reference.
`EmitDwgFile` writes it back from those typed values.

| DWG                | Bytes   | Classes | Objects | Fully typed objects | Typed common data only | Re-emission  |
| ------------------ | ------- | ------- | ------- | ------------------- | ---------------------- | ------------ |
| A0 views control   | 126,690 | 93      | 1,958   | 1,891               | 67                     | Byte for byte |
| A1 dimension control | 129,413 | 97    | 1,993   | 1,920               | 73                     | Byte for byte |
| A2 automatic control | 146,068 | 96    | 2,133   | 2,066               | 67                     | Byte for byte |
| Historical example | 110,873 | 46      | 900     | 865                 | 35                     | Byte for byte |

The objects with typed common data only are AutoCAD Mechanical standard objects in the controls.
In the historical example, they are the `ACDBIDWSTREAM`, `ACDBIDWVERSION` and `ACDBSYNERGYMAPPINGS` objects.
Their class data stays as the exact bit tail that follows the typed common data.

The typed model covers these parts.

| Part                | Typed content                                                                  |
| ------------------- | ------------------------------------------------------------------------------ |
| File and page layer | File header, encrypted header, page map, section map and every page            |
| Header section      | 310 header variables and the four BS values after the handle stream            |
| Class section       | Class rows with names, proxy flags and instance counts                         |
| Handle section      | Rebuilt from the object handles and offsets when the file is written           |
| Objects             | Common data, extended data and class data for 75 object kinds in the A1 control |
| Other sections      | Summary, AppInfo, AppInfoHistory, Preview, RevHistory, template, free space, auxiliary header and the `AcDsPrototype_1b` data store |

The view objects are typed as well.

| Class                                      | Role in a view                                                  |
| ------------------------------------------ | --------------------------------------------------------------- |
| `ACDBVIEWREP`                              | View definition, body key, orientation matrix and view centre   |
| `ACDBVIEWREPBLOCKREFERENCE`                | Reference to an anonymous `*S` view block, two for each view    |
| `ACDBASSOCVIEWREPACTIONBODY`               | Associative action that owns the view                           |
| `ACDBASSOCEXTERNALPERSSUBENTIDHOLDER`      | Persistent reference to the referenced body                     |
| `ACDBASSOCPROJECTEDENTITYPERSSUBENTIDHOLDER` | Persistent reference to a projected edge                      |
| `ACDBVIEWREPSOURCEMGR`                     | View source manager with the `ACAD_ROUNDTRIP_2014_VIEWREP_FUSIONSRC` xrecord |
| `DRAWINGVIEW`                              | View border, scale, centre and viewport on the sheet            |

The `*S` blocks hold the view curves as plain lines, circles and arcs.
The `*D` blocks hold dimension graphics.
Extended data of the view reps stores `AUTO_VIEW_XDATA`, `AUTO_SCALE`, `AUTO_NEST`, `CENTERMARK` and `CENTERLINE`.

The DWG is not a cache that Fusion regenerates from the segments.
A drawing without its DWG member fails to open with the message `Cannot find the specified drawing file`.
A drawing with the A0 segments and the A1 DWG opened with the A1 dimension and views.
On open, Fusion writes the embedded DWG and a SAB export of the referenced body to a temporary folder.
It then starts the drawing engine, which runs one `VIEWEDIT` command for each view.
The views show the curves stored in the DWG, as the [stored curves gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Drawing/FusionDrawingStoredViewCurves.md) records.
Fusion recomputes them only when `updateAllReferences()` updates an out-of-date reference.

## Minimal drawing state

Native removal variants of the A1 control show which DWG content Fusion needs.
Each row names the variant whose result decides it.

| Content                                         | Needed | Evidence                                              |
| ----------------------------------------------- | ------ | ----------------------------------------------------- |
| DWG member of the F2D                           | Yes    | `P2NoDwg` showed `Cannot find the specified drawing file` |
| `ACDBVIEWREP` object of each view               | Yes    | `F1NoViewReps` gave views whose items were `None`     |
| Contiguous section ids                          | Yes    | `Q5NoRevHistory` and `Q3NoOptional` were not valid     |
| Handles that name present objects               | Yes    | `G1FreshHandles` crashed the drawing engine            |
| View curves in the `*S` blocks                  | No     | `D2NoViewCurves` opened with empty views               |
| Associative action of the dimension             | No     | `F3bPlainDimension` kept its dimension                 |
| Title block and border inserts                  | No     | `F4NoTitleBlock` and `F5NoBorder` kept 3 views         |
| Centre mark                                     | No     | `F6NoCenterMark` kept 3 views                          |
| Fusion and history entries of the named-object dictionary | No | `E2NoNodHistory` and `E3NoFusionNod` kept 3 views |
| `DICTIONARYVAR`, `FIELD` and `FIELDLIST` objects | No    | `E4NoVariables` and `E5NoFields` kept 3 views          |
| AutoCAD Mechanical objects                      | No     | `H1NoAcm` kept 3 views and the dimension               |
| `AcDb:AcDsPrototype_1b` with every data-store flag cleared | No | `Q1NoDataStore` kept 3 views and the dimension |

No variant had its view curves regenerated on open.
Fusion shows the stored view curves, and `updateAllReferences()` recomputes them from the referenced body.
The authoritative state of a drawing is therefore its sheet, its view reps with their view source, and its annotations.
Kit's author writes that state and leaves the view blocks empty.

## Authoring

`AuthorDwg` writes that state from a `DwgDraft`, and `BuildDrawing` and `BuildBundle` add the F2D members and the bundle.
No byte of a captured DWG or drawing goes into an authored file.
The ISO standard rows come from typed values that the research builders took from the template part of a Fusion-saved drawing.

| Authored part        | Content                                                                 |
| -------------------- | ----------------------------------------------------------------------- |
| Sheet                | Layout, paper-space block, viewports, border and ISO title block        |
| Title block          | Attribute texts from the draft                                          |
| Views                | `ACDBVIEWREP`, `DRAWINGVIEW`, view actions, source manager and empty `*S` blocks |
| Projected views      | The same objects with the parent view named                             |
| Dimension            | `DIMENSION_LINEAR` with its `*D` block and measured text                |
| Model reference      | View source with body id, component, geometry GUID and bounds           |
| Shell                | Ten sections with ids 1 to 10, Kit AppInfo and four header values from the version GUID |

Fusion did not finish opening an authored DWG.
Two checks of a Fusion save stop it.

| Check                                    | What it depends on                                  | Why Kit cannot meet it                           |
| ---------------------------------------- | --------------------------------------------------- | ------------------------------------------------ |
| Four BS values after the header handles  | The header variables, data and strings alike        | No unkeyed checksum reproduces the values        |
| Autodesk trusted-file text               | AppInfo or `AcDb:AppInfoHistory` carrying the text  | The text states an Autodesk save, so Kit does not write it |

The [header tail gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Drawing/FusionDrawingHeaderTail.md) and the [authored shell gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Drawing/FusionDrawingAuthoredShell.md) record the bisection.

## Drawing-root bundles

A drawing-root F3Z holds `Manifest.json`, `DesignDescription.json`, the F2D and the referenced F3D files.
The drawing object has a `DERIVED` relationship to its design.
`RouteBundle` returns a `DrawingBundle` when the root object is an F2D.
The historical bundle uses an older description grammar, as the [grammar gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Drawing/FusionHistoricalBundleGrammar.md) records.

## Native acceptance

The [acceptance report](NativeAcceptance.json) records the native runs in Fusion 2706.1.17.
It replaces cache paths and cloud identities with file names and placeholders.
Each variant was uploaded as a drawing-root F3Z into the `Kit Fusion Acceptance` project.

| Variant          | Content                                     | Result                                          |
| ---------------- | ------------------------------------------- | ----------------------------------------------- |
| `P0Control`      | A1 control as Fusion saved it               | Opened with 3 views and 1 dimension             |
| `H0Historical`   | Historical example bundle                   | Opened with 1 view and 0 dimensions             |
| `M1Reemitted`    | A1 control read and emitted by Kit          | Opened with the same measurements as `P0Control` |
| `P4ViewsControl` | A0 control as Fusion saved it               | Opened with 3 views and 0 dimensions            |
| `P2NoDwg`        | A1 control without its DWG member           | Engine error dialog, and the open never returned |
| `P3SwappedDwg`   | A1 segments with the A0 DWG                 | No engine session within 207 seconds            |
| `P5ReverseSwap`  | A0 segments with the A1 DWG                 | Opened with 3 views and 1 dimension, as in the A1 DWG |
| `M2Reemitted`    | A1 control emitted by Kit, uploaded twice   | Files were read-only, so the edit and save did not run |

The A1 control and its Kit re-emission gave these measurements.

| Item                 | Value                                                      |
| -------------------- | ---------------------------------------------------------- |
| Sheet                | 420 mm by 297 mm with `ISO_TITLEBLOCK`                     |
| Base view            | Type 0, orientation 3, scale 4.0 and 5 curves              |
| Base view outline    | x from 100.47 mm to 260.47 mm, y from 80.61 mm to 160.61 mm |
| Hole circle          | Center (220.47 mm, 120.61 mm) and radius 16 mm             |
| Projected views      | 4 curves each                                              |
| Document reference   | Source design version 1, not out of date                   |

The orientation and scale getters fail on the projected views, as the [getter gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Drawing/FusionProjectedViewGetters.md) records.

The edit run changed `kitWidth` from 40 mm to 60 mm in the referenced design.

| Stage                         | Reference version | Out of date | Base view x range      |
| ----------------------------- | ----------------- | ----------- | ---------------------- |
| Before the edit               | 1                 | No          | 100.47 mm to 260.47 mm |
| After open, before the update | 1                 | Yes         | 100.47 mm to 260.47 mm |
| After `updateAllReferences()` | 2                 | No          | 60.47 mm to 300.47 mm  |

The body volume changed from 7.4973 cm³ to 11.4973 cm³.
The [reference update gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Drawing/FusionDrawingReferenceUpdate.md) explains why the update call is needed.

Fusion did not save the drawing after the reference update.
The Personal-use license kept the new uploads read-only, as the [read-only gotcha](../../../../Documentation/Gotchas/Conversion/Fusion/Drawing/FusionPersonalReadOnlySave.md) records.
Save and reopen after a model edit are therefore not verified.
The upload and reopen of `M1Reemitted` show that a Kit-emitted drawing survives a cloud upload.
It reopened with the same measurements as the Fusion-saved control.

The second pass opened DWG variants that Kit's typed writer emitted.
The report keeps each plan, inspection, round, dialog, quarantine entry and recycle count.

| Variant              | Content                                               | Result                                         |
| -------------------- | ----------------------------------------------------- | ---------------------------------------------- |
| `H1NoAcm`            | A1 control without unused blocks and AutoCAD Mechanical objects | Opened with 3 views and 1 dimension  |
| `N2AuthoredF2d`      | Kit-built F2D members around the `H1NoAcm` DWG        | Opened in 4.3 s with 3 views and 1 dimension   |
| `Q1NoDataStore`      | `H1NoAcm` without the data-store section and flags    | Opened in 4.7 s with 3 views and 1 dimension   |
| `Q8AuthoredSections` | `Q1NoDataStore` with Kit's section set                | Opened in 5.2 s with 3 views and 1 dimension   |
| `Q5NoRevHistory`     | `Q1NoDataStore` with a gap in the section ids         | `Drawing file is not valid.`                   |
| `W1KitAppInfo` to `W6KitClassCounts` | One part of Kit's shell each           | Opened in 3.4 s to 6.1 s, except `W2KitShorts` |
| `W2KitShorts`        | Kit's four header values                              | Open had not finished after 185 s              |
| `U2ForeignTail`      | The four header values of the A2 control              | Open had not finished after 181 s              |
| `U4AuthoredShellTail` | Kit's shell with the A1 header values                | Open had not finished after 185 s              |
| `S5SheetDimension`   | Kit-authored sheet with one dimension                 | Open had not finished after 602 s              |

A guard restarted Fusion after each stall, so each stalled variant ended its run.

The third pass bisected the content of those stalls.
`BuildBisect.py` builds the variants, and `BisectRound.py` opens each one in its own run of `RunGuarded.mjs`.
That runner holds the oracle lock while it restarts Fusion after a stall of 60 s, so a stall no longer ends the round.
A restart took about 70 s.

| Variant           | Change                                                         | Result               |
| ----------------- | -------------------------------------------------------------- | -------------------- |
| `B0Base`          | `Q1NoDataStore` again, with the A1 header values               | Opened in 4.4 s      |
| `B10FifthLong`    | The BL after the four header values set to 1                   | Opened in 3.5 s      |
| `B8UserReal`      | `USERR4` from 0.0 to 1.0                                       | Not open after 61 s  |
| `B1VersionGuid`   | `VERSIONGUID`                                                  | Not open after 61 s  |
| `B9AllVaried`     | Every header variable that differs between saves               | Not open after 61 s  |
| `C7AppOnly`       | `Q8AuthoredSections` with Kit AppInfo                          | Not open after 61 s  |
| `C1AppNoTrust`    | `Q8AuthoredSections` with the Fusion product entry only        | Not open after 61 s  |
| `C2AppKitProduct` | `Q8AuthoredSections` with Kit's product and the trusted-file entry | Opened in 3.5 s  |

The four header values cover the header variables, but not the objects, the sections or the F2D members.
The second stall needs the Autodesk trusted-file text to be absent from both AppInfo and `AcDb:AppInfoHistory`.
`U4AuthoredShellTail` stalled because Kit's AppInfo and Kit's section set together removed both copies.
The acceptance report keeps these rounds under `bisection`, with the earlier pair rounds on `Q8AuthoredSections`.
