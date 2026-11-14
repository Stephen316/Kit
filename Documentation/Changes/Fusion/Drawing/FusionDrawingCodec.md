# Typed Fusion drawing documents

Kit adds a reader, a writer and an author for Fusion drawing documents under `convert.formats.Fusion.DrawingCodec`.

| API                                                     | Result                                                   |
| ------------------------------------------------------- | -------------------------------------------------------- |
| `ReadDrawing(DataValue, InflateZstd=None)`              | `FusionDrawing` from a modern or historical F2D          |
| `EmitDrawing(Value, CompressZstd=None)`                 | F2D bytes from a `FusionDrawing`                         |
| `ReadDrawBundle(DataValue, InflateZstd=None)`           | `DrawingBundle` from a drawing-root F3Z                  |
| `EmitDrawBundle(Value, CompressZstd=None)`              | F3Z bytes from a `DrawingBundle`                         |
| `RouteBundle(DataValue, InflateZstd=None)`              | `DrawingBundle` for an F2D root, else `FusionBundle`     |
| `ReadInventory(Content)`                                | `DwgInventory` with the DWG header, pages and classes    |
| `Dwg.ReadDwgFile(Content)`                              | Typed `DwgFile` with every section and object            |
| `Dwg.EmitDwgFile(DwgModel)`                             | DWG bytes from a `DwgFile`                               |
| `Dwg.Author.AuthorDwg(Draft)`                           | New DWG bytes from a `DwgDraft`                          |
| `Author.BuildDrawing(SpecValue, Database)`              | New `FusionDrawing` from a `DrawingSpec` and its DWG     |
| `Author.BuildBundle(SpecValue, Drawing, DesignData)`    | New drawing-root `DrawingBundle` with the referenced design |
| `Author.MakeIdentity()`                                 | Fresh document, version and lineage identities           |
| `Author.CheckSpec(SpecValue, Database)`                 | Raises `ValueError` for an inconsistent drawing spec     |

## Behavior

`FusionDrawing` holds typed root and asset manifests, both entity segments, the sheet layout and the nine automation settings.
It also holds images, properties, component references, the historical redirection table and the exact entry layout.
The modern segments decode to typed entity records through a native drawing vocabulary of 14 class schemas.
The historical segment keeps framed records, because its class profiles are older than the reflected schemas.

The embedded DWG is a `DrawingDatabase` with its member name and bytes.
The reader requires that name to equal `ExtFileSerializer.persistedFileName` in the drawing segment.
`ReadDwgFile` decodes those bytes into header variables, classes, objects and every other section.
`EmitDwgFile` writes them back from the typed values.
The [Open Design Alliance DWG specification](https://www.opendesign.com/files/guestdownloads/OpenDesign_Specification_for_.dwg_files.pdf) is the format reference.

| DWG                  | Bytes   | Objects | Fully typed | Typed common data only | Re-emission   |
| -------------------- | ------- | ------- | ----------- | ---------------------- | ------------- |
| A0 views control     | 126,690 | 1,958   | 1,891       | 67                     | Byte for byte |
| A1 dimension control | 129,413 | 1,993   | 1,920       | 73                     | Byte for byte |
| A2 automatic control | 146,068 | 2,133   | 2,066       | 67                     | Byte for byte |
| Historical example   | 110,873 | 900     | 865         | 35                     | Byte for byte |

The objects with typed common data only are AutoCAD Mechanical objects in the controls.
In the historical example, they are its `ACDBIDWSTREAM`, `ACDBIDWVERSION` and `ACDBSYNERGYMAPPINGS` objects.

The [data model section](../../../../re/Fusion/Reconstruction/Drawings/DataModelSection.md) describes the members, manifests, classes, DWG objects and joins.

## DWG authority

The DWG is the authoritative store of sheets, views, view curves and annotations.
Fusion does not regenerate it from the segments.
On open, Fusion gives the drawing engine the embedded DWG and a SAB export of the referenced body.
The engine shows the view curves that the DWG stores.
It recomputes them when `updateAllReferences()` updates an out-of-date reference.

Native removal variants define the minimal state of a drawing.
Fusion needs the DWG member, a view rep object for each view, contiguous section ids and handles that name present objects.
It does not need the stored view curves, the title block, the border, AutoCAD Mechanical objects or the data-store section.
A view without stored edges opens empty, though, so Kit writes them.
The [data model section](../../../../re/Fusion/Reconstruction/Drawings/DataModelSection.md) lists each variant.
The [section id gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingSectionIds.md) records the section rule.

## Authoring

`AuthorDwg` builds a new DWG from a `DwgDraft` without any source DWG bytes.
The draft names the sheet, the title block texts, the views, the view source and the dimensions.
Kit writes every object from typed values, declared vocabulary and rules.
No table, header block or row captured from a Fusion save ships in `src`.
The caller supplies the fingerprint and version GUIDs and the save moment.
Each view stores the edges it shows, computed from the view source solid, as the view edges section explains.

`BuildDrawing` builds the F2D members around that DWG from a `DrawingSpec`.
`BuildBundle` builds the drawing-root F3Z with the referenced design.

### Rules in place of captured data

| Part                     | Rule                                                                                   |
| ------------------------ | -------------------------------------------------------------------------------------- |
| Paper                    | ISO A0 to A4 by halving 841 × 1189 mm and rounding down; ASME A to E by halving 34 × 44 in, written in millimetres |
| Border block             | ISO 5457: filing margin 20 mm, other margins 10 mm, trim marks, centring marks, 2·round(side/100) zones per side, digits across, letters down |
| ASME border block        | ASME sheet family: 0.5 in margins, zones a quarter of an A sheet across the whole sheet, numbers from the right, letters from the bottom |
| Title block              | Kit ISO 7200 block, 180 mm wide, 5 rows of 8 mm, the 15 ISO 7200 field tags as attributes |
| Header variables         | 310 variables in specification order; paper limits from the paper; dimension sizes from ISO 3098 letter heights |
| Layers                   | ISO 128 line widths as AutoCAD lineweight indices; plot flag per layer                  |
| Line types               | `acad.lin` inch patterns times 25.4, computed in exact decimals                         |
| Text and dimension style | Arial styles; `Dim-ISO-25` from the same rules as the header                            |
| Text extents             | Arial advance widths and glyph boxes from the font, for printable ASCII and `°`, `±` and `Ø`; other glyphs raise |
| Named objects            | Only the dictionaries the header and sheet name; ByBlock and ByLayer materials; STANDARD multiline style; view standard |
| Classes and app ids      | Only the classes of the object kinds written and the app ids the extended data uses     |
| Sheet manifest           | Width, height and zones from the paper rule                                             |
| Images                   | One large and one small thumbnail for the sheet, and the preview; no template sheet thumbnails |
| Drawing component colour | Kit's neutral grey (0.8, 0.8, 0.8), the value Kit's design writer uses                  |
| Design record ids        | One counter after the empty design: 2 ids per model source, 1 per sheet, 6 per tracked edge |
| Sheet order              | The sheet record's order is its layout's tab order; the model tab is 0 and sheets count up from 2 |
| Model source             | `<index>_Component`, numbered from 1                                                    |
| Linear dimensions        | Sizes from the `Dim-ISO-25` rule: extension lines 2.1 mm off the feature and 2.1 mm past the line, 3.5 mm arrows, text 1.4 mm off the line |
| Short dimensions         | Arrows inside from two arrows and two text gaps (9.8 mm); text inside from its width and two gaps; else past the second arrow; no extension line through a point |
| Base view directions     | Along a model axis; Fusion writes slanted views in another record layout, so Kit refuses them |
| Projected views          | A view beside its parent looks back along the parent's right axis and one above or below looks back along its up axis; the shared axis stays; the view angle points from the parent to the view |
| View rep viewport        | The view's frame viewport, the one that looks straight at the paper, as in all 63 view reps of 5 Fusion saves |
| View style               | `ViewLongB` 2 for visible edges, 1 with hidden edges; a projected view takes 4 plus its base view's style |
| View edges               | Computed from the view source solid and the view direction, in Fusion's stored form; see below |
| Round dimensions         | Text placed by Kit, so flags 10 and the DIMUPT override; radius also DIMSE1; diameter sign U+2205 |
| Hole data                | Styled JSON with sorted keys and tab indents, built from the body id                    |
| View state body mark     | `21 84 DE 7B 09`, once after each body's bounds in every view state Kit has read        |

Kit writes no save history, document version record, variable dictionary, plot device name, visual style, table style or multileader style.
The authored A3 DWG shrank from 39.8 KB to 19.4 KB.

`SheetDefaults.json` holds the field values each object kind shares, such as ByLayer colour and line weight.
In the four readable Fusion saves, 75,669 object fields equal these values and 2,535 differ.
The differences are values Kit sets per object, and Kit's neutral choices: no plot device, zero plot margins and middle-centre dimension text.

One shared value is bytes: the entity graphics of `DRAWINGVIEW` and `ACDBVIEWREPBLOCKREFERENCE`, `08 00 00 00 00 00 00 00`.
It is only the 8-byte header of a proxy graphics stream.
Its first 32-bit word, 8, equals the stream length, and its second word is 0, so no primitive chunk follows.
The [DWG specification](https://opendesign.com/files/guestdownloads/OpenDesign_Specification_for_.dwg_files.pdf), section 29, gives the chunk layout: a 32-bit size, a 32-bit type, then the data.
[ezdxf](https://github.com/mozman/ezdxf/blob/master/src/ezdxf/proxygraphic.py) skips the same 8-byte header before it reads chunks.
So the stream holds no primitives.

[`SheetDefaultReasons.json`](../../../../re/Fusion/Reconstruction/Drawings/SheetDefaultReasons.json) gives each of the 666 default rows a basis and a note.
It also counts the instances that hold the value in three Fusion-made drawings.
Of the rows, 640 have a known meaning.
Of those, 355 are from public DWG and DXF references, 129 are empty values and 74 are identity values.
The remaining known rows are 31 versions, 31 names from Fusion's drawing schema, 7 template settings and 13 neutral Kit choices.
The other 26 rows have no known meaning.
They are words and bits of the hole reference data, the inventor subentity manager, the hatch manager and the geometry dependency.
They also include bit 3 of the dimension flags, the dimension bit after the measurement, one MTEXT bit and one drawing view real.
Each keeps one value in every instance Kit has read.

Each of these 26 rows was tested in Fusion 2706.1.17.
A test changes the field in the A3 control drawing and opens the drawing in Fusion.
[`GraftRoundUnknowns.json`](../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundUnknowns.json) records the 45 variants and their outcomes.
The reasons file gives these rows the `tested` basis and lists each value Fusion opened or rejected.

- In 10 rows, Fusion rejects some other values. It reports the drawing as damaged, or its open does not finish within 300 seconds.
  - The inventor subentity manager word opens with 64, 65, 66, 96 and 127. Fusion reports damage with 1, 2, 8, 16, 32, 48, 63, 128, 192, 256 and 1000. Its open with 0 does not finish. So the tested values that open are exactly those with bit 6 set and no higher bit.
  - The three hole reference data words reject 0. The second word also rejects 2.
  - The three hole reference data bits reject 1. So do the third and fifth hatch manager words and the MTEXT bit.
- In 16 rows, Fusion opened the drawing with another value. It showed the same views and dimension. Kit keeps the value of every Fusion save.
  - These rows are bit 3 of the dimension flags, the dimension bit, and the subentity manager bit and raw word.
  - They are also the geometry dependency word and bit, and the second and fourth hatch manager words. These rows are also the fifth reference data text and the drawing view real.

The dimension rows were tested on the linear dimension, because all four dimension kinds share this common data.
The hole reference data has only one instance in the three drawings, so its evidence is weakest.
The diameter and radius dimension rows have no instance in the three drawings.
The tests show which values Fusion accepts, but not what the fields mean.

Fusion-saved drawings differ in the component colour, so it is per document and not a format constant.

Every Fusion drawing keeps its template's ten border blocks, A0 to A4 in both orientations.
Kit's border rule was fitted on `ISO_A3_SHEET` and checked against the other nine.
It matches the landscape A0, A1 and A2 blocks to within 2 × 10⁻⁴ mm, the rounding of Fusion's template.
The portrait and A4 blocks differ by design, as the [border gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingTemplateBorders.md) explains.

Kit used to write ASME sheets with inch numbers in a millimetre drawing, so a B border was 17 × 11 mm.
Kit now writes every paper in millimetres and draws ASME borders from the ASME sheet family.
No Fusion save holds an ASME border, as the [ASME gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingAsmeSheets.md) explains.

Fusion 2706.1.17 did not finish opening any drawing with a Kit-authored DWG.
The open waits without a dialog until Fusion is stopped.
Two parts of the authored DWG cause the wait.

| Cause                                   | Evidence                                                    |
| --------------------------------------- | ----------------------------------------------------------- |
| Four header values after the handles    | Zero, Kit-chosen and foreign values each stalled an otherwise Fusion-saved DWG. With the saved values kept, a change to one header variable also stalled it |
| Missing Autodesk trusted-file text      | The open stalled when neither AppInfo nor `AcDb:AppInfoHistory` carried the text, and opened when AppInfo carried it next to Kit's product entry |

The four values depend on the header variables, both data and strings.
They do not cover the objects, the other sections or the F2D members.
No unkeyed CRC, Adler, digest or seeded generator reproduces them in 31 Fusion saves.
The trusted-file text states that an Autodesk application saved the file.

The [header tail gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingHeaderTail.md) and the [authored shell gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingAuthoredShell.md) record the bisection runs.
Kit does not copy Fusion-written header values into an authored file.
Kit never writes the trusted-file text.
Kit therefore has no rule that makes Fusion 2706.1.17 open an authored DWG.

The F2D author works on its own.
`N2AuthoredF2d` put Kit-built members around a Fusion-saved DWG, and it opened with 3 views and 1 dimension.

### View edges

Fusion 2706.1.17 draws a view on open only from the edges its view rep stores, as the [stored edge gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingStoredEdges.md) explains.
Kit therefore computes each view's edges and writes them as Fusion does.
`ViewSource.Solid` carries the body's B-rep, and a view without it raises.
`ViewDraft.ShowHidden` picks the style, and a projected view must share its parent's style.
The [data model](../../../Reference/Research/FusionDataModel.md#stored-view-edges) gives the stored form and its evidence.

| Step         | Rule                                                                                  |
| ------------ | ------------------------------------------------------------------------------------- |
| Edge ids     | Position among the distinct edges of the walk over shell faces, face loops and loop coedges |
| Candidates   | Every line and circle edge that does not project to a point, and the two silhouettes of each cylinder and cone |
| Silhouettes  | Id 0xFFFFFFFF − 2048 × face index − side; side 0 at offset sight × axis; the line spans the face's boundary circles |
| Covered      | A piece that projects onto a nearer candidate with a parallel tangent is not stored    |
| Hidden       | A piece is hidden when the ray toward the eye enters a face strictly inside it          |
| Rows         | Visible style stores visible pieces; hidden style stores both, flag 0 and layer Hidden for hidden ones; rows sorted by signed id |
| Cached curve | The whole edge: a line's start and span, or a circle's centre, normal, arbitrary axis, radius and full turn |
| Drawn entity | The stored piece in model millimetres: LINE, CIRCLE, or ARC for a circle seen edge on, centres in object coordinates |

These cases have no Fusion evidence, so Kit raises for them.

| Case                                           | Why                                                         |
| ---------------------------------------------- | ----------------------------------------------------------- |
| An edge split into more than one piece         | No saved view draws part of a line; ids never repeat in a body |
| An edge that is part of a circle               | All 255 saved cached circles are whole                     |
| A tangent edge, as fillets make                | Whether and how Fusion draws tangent edges is not recorded |
| Spheres, tori, splines and other surfaces      | Silhouettes of other surfaces are not decoded              |
| More than one body, or a moved body            | Every decoded view shows one untransformed body           |

## Verification

`ReadDrawing` and `EmitDrawing` reproduce these inputs byte for byte.

| Input                          | Bytes   | SHA-256 prefix |
| ------------------------------ | ------- | -------------- |
| A0 views control F2D           | 123,711 | `1914355f`     |
| A1 dimension control F2D       | 127,179 | `9a13d8b7`     |
| A2 automatic dimension F2D     | 140,651 | `f38fec3f`     |
| Historical example F2D         | 103,817 | `33589d0e`     |
| Historical example F3Z bundle  | 200,292 | `4e67c7a5`     |

The tests in `tests/convert/formats/FusionCodec/Drawings` use normalized fixtures without the captured DWG.
They cover the package, parts, manifests, bundles, the DWG inventory, the typed segment facts and the authored DWG.

Native runs in Fusion 2706.1.17 gave these results.

| Check                                   | Result                                                        |
| --------------------------------------- | ------------------------------------------------------------- |
| Kit-emitted A1 drawing opens            | Same sheet, views, curves and dimension as the saved control  |
| Model edit from 40 mm to 60 mm          | Base view width 160 mm before and 240 mm after the update     |
| Reference after `updateAllReferences()` | Version 2, not out of date                                    |
| Kit-built F2D around a Fusion-saved DWG | Opened in 4.3 s with views of 5, 4 and 4 curves and 1 dimension |
| Kit-modified DWG with Fusion header values | Opened in 3.3 s to 6.1 s with 3 views and 1 dimension      |
| Same, with one header variable changed  | Open had not finished after 61 s                              |
| Same, with no trusted-file text left    | Open had not finished after 61 s                              |
| Kit-authored DWG                        | Open had not finished when stopped after 121 s to 602 s       |
| Authored view recompute and model edit  | Not run, because no authored drawing opened                   |
| Fusion save and reopen after an edit    | Not run, because the Personal license kept every upload read-only |

The [acceptance report](../../../../re/Fusion/Reconstruction/Drawings/NativeAcceptance.json) records every run with normalized names.

Kit-authored DWGs do not open, so the rules are checked by graft.
A graft keeps a Fusion-saved control and its header, and swaps in what a rule generates.
All grafts below opened in Fusion 2706.1.17 with views of 5, 4 and 4 curves, 1 dimension and a 420 × 297 mm sheet.

| Graft                | What Kit replaced                                                                 |
| -------------------- | --------------------------------------------------------------------------------- |
| `L1Lean`             | Removed save history, Fusion dictionary items and the variable dictionary         |
| `L4Core`             | Kept only the standard objects Kit generates                                      |
| `T1Tables`           | 8 layers, 6 line types, 2 text styles, the dimension style and the active viewport |
| `T2Standard`         | Also materials, the multiline style, the view standard and the layout plot fields |
| `T3Sheet`            | Also Kit's border block, title block, their inserts and the 15 title attributes   |
| `C1NoTemplateThumbs` | Removed the template sheet thumbnails                                             |
| `C2NeutralCycle`     | Set the drawing component colour to Kit's neutral grey                            |
| `C3Renumbered`       | Renumbered the control's design records without gaps, next id 60 in place of 80   |
| `C4KitMembers`       | Replaced every F2D member except the DWG with Kit's, design ids up to 41          |
| `D0Plain`            | `T2Standard` with the control dimension's associative action removed              |
| `D1Vertical` to `D4Diameter` | `D0Plain` with Kit's vertical, aligned, radius or diameter dimension and its block |
| `D5Short`, `D6OnLine` | `D0Plain` with a short aligned dimension, with and without extension lines           |
| `D7Split`, `D8Flank` | `D0Plain` with a short aligned dimension whose text goes outside and a vertical one whose arrows go outside |
| `S1AsmeB` to `S3AsmeA` | `T3Sheet` on ASME B, D and A paper, the control's sheet block filled with Kit's ASME border |
| `V1LeftBelow` to `V3AboveBelow` | `D0Plain` with its projected views turned into left and below, right and back, or above and below views by Kit's leaves |
| `V4KitModel` to `V6RightBackKitModel` | `D0Plain`, `V3AboveBelow` and `V2RightBack` with Kit's model space places for the views |
| `V7NoEdges` to `V9AboveBelowNoCurves` | `D0Plain` and `V3AboveBelow` with no stored view edges, as Kit writes views, and then also no view curves |

19 of the 22 generated standard objects equal the Fusion-saved ones apart from handles.
Fusion writes line type dashes as exact millimetre decimals and sums them as floats, and Kit now does the same.
The other three differ by design.
The view border line type is Kit's own pattern, the active viewport shows the whole paper, and Kit writes 0.1 where Fusion writes 0.1000000001.
The [T3](../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT3.json), [T4](../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT4.json) and [T5](../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT5.json) reports record these runs.
`C3Renumbered` shows that Fusion does not need its own gaps in the record ids.
`C4KitMembers` shows that Kit's numbered records, sheet order and manifest open around a Fusion-saved DWG.
The [T6](../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT6.json) report records the dimension grafts.
The [T7](../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT7.json) report records the ASME sheet grafts, which opened at the ASME paper sizes.

A Fusion save with five sheets holds six vertical, six aligned, two radius and one diameter dimension.
Kit's vertical and aligned layout matches Fusion's, and Kit's text extents match all fifteen texts.
Fusion keeps both arrows inside when the line is at least two arrows and two text gaps long, 9.8 mm.
It keeps the text inside, above the line, when the line is at least the text width and two gaps long.
Text that does not fit goes past the second arrow, 1.4 mm beyond a 3.5 mm line.
That text sits over a line that ends 1.4 mm after it.
Arrows that do not fit point in from outside, with a 3.5 mm line past each arrow that has no text beside it.
An extension line whose point lies on the dimension line is left out.
The view scales of four Fusion saves put a 3.54 mm and a 10 mm dimension at 30 lengths from 2.12 mm to 50 mm.
The limits sit between 9.72 and 9.90 mm for the arrows, and between 11.77 and 11.99 mm for text 9.07 mm wide.
For text 4.67 mm wide, the limits sit between 6.0 and 7.5 mm.
Kit's lines, arrows and text points match all 68 saved linear and aligned dimensions to 6 × 10⁻⁶ mm.
Fusion orders each arrow's corners along the reading direction's normal, and so does Kit.
Fusion opened `D5Short` and `D6OnLine`, as the [T8](../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT8.json) report records.
Fusion opened `D7Split` and `D8Flank`, which cover the other two short layouts, as the [T9](../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT9.json) report records.

The projected view grafts take from a Kit build only the values that differ between two layouts.
On every such value the control equals Kit's build with the control's right and above views, which checks Kit's projected view rule against Fusion's.
Fusion opened all nine view grafts, as the [T10](../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT10.json) report records.
On open, Fusion projects only the edges a view stores, so a view that changes direction shows its old edges from the new side.
After a scale change, Fusion found the edges again and drew each view at Kit's planned place and size.
A view with no stored edges opens empty until such an update, as the [stored edge gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingStoredEdges.md) records.

Round T16 grafted the views Kit authors, with their edges, onto the control in four layouts and both styles.
Left, below and back views are held out: no rule came from them.
All 8 grafts opened with Kit's curves, and the counts and boxes on open equal those after a scale change.
The DWG Fusion exported after that update holds its own edges, and they equal Kit's in all 24 views.
Kit's views of BoxA, an unrelated Fusion-saved design, equal its stored edges.
The [T16 report](../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT16.json) records both checks.
The [round dimension gotcha](../../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingRoundDimensions.md) lists what differs for radius and diameter.
