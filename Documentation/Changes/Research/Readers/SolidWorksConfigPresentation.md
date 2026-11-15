# SOLIDWORKS configuration presentation records

The [configuration map replay](../../../../re/solidworks/archive/ConfigMap.py) replaces at least 21,330 bytes of fixed advances per discovery capture with field reads. The build and capture receipt still scope the whole presentation walk.

| Record | Layout in build 34.4.1.1011 |
| --- | --- |
| Nine nested length units | The load branch of `sldmfcu!moUserUnits_c::Serialize` at RVA `0x1ecde5` reads 62 bytes. The subtype at `0x1ecb30` reads an unsigned 16-bit length code, then invokes the typed pointer reader at `0x1e91c0` for its child. The witnessed child is null in each body. |
| Ten model views | The load branch of `sldmodu!moView_c::Serialize` at `0x10ea3a9` reads its name, two transforms, and scalar fields separated by three collection counts. All three collections are empty in the witnessed views. The two auxiliary lists are inline when present. |
| Model and annotation transforms | The `sldmgu!mgXform_c::restore` path at `0x331d0` reads the matrix-present flag, an optional nine-double matrix, four translation and scale doubles, and an extension mode byte. Mode zero is required. |

The ten views consume 1,980 bytes in the observed captures. The model loader selects the ten-object loop at `sldmodu+0x10f2914` and reads each typed view at `0x10f2963`. The final view returns before a byte and two integers read by the model at `0x10f2c2f`, `0x10f2c51` and `0x10f2c61`.

## Detail settings before the first length pointer

The [detail settings reader](../../../../re/solidworks/archive/ConfigDetail.py) replaces the initial 1,183-byte presentation advance. Two leading zero bytes remain a checked boundary word with unassigned ownership. The modern `moDetailDefs_c` load branch at `sldmfcu+0x137c50` reads scalar settings and framed text. The continuation at `0x139eb8` reads the signed exclusion-name count, and `0x13a1a0` and `0x13a280` read three eight-integer rows each. The call at `0x13a3d9` reads the priority labels, which use the short count form in these archives.

At `0x13a401`, the reader enters the inline character format. The call at `0x13a414` enters the dimension settings at `0x13b8d0`. It reads the scalar settings before the first style at `0x13be26`. The linear style at `0x13e9a0` delegates to `moBaseDimDef_c::Serialize` at `0x1366a0`. The supported branch guards the unused layer ID, then uses the inline length-unit reader called at `0x136a5d`. Its typed child is the first presentation pointer.

## Dimension styles through the annotation settings boundary

The calls from `sldmfcu+0x13be26` through `0x13bf47` follow the inline members identified by the `moDimDefs_c` constructor at `0xbeb10`. The order is linear, angle, arc length, radial, hole callout, ordinate, chamfer, diameter, angular ordinate and base. Each call reads the shared style fields before the subclass tail. The in-stream dual-length pointer may be a typed class reference or null. The observed angle style is null, and the other nine allocate length records with no further child.

After the length pointer, the shared base serializer reads the inline angle unit at `0x136a6d`, the character format at `0x136a7d`, two line font records at `0x136a8d` and `0x136aae`, and three final integers. The line font serializer at `0x87650` reads a framed name, an inline short and float width via `0x12a6e0`, and another short. The subclass load paths supply the remaining primitive fields. The ten style continuations replace 4,222 bytes of fixed advances, including the last 240 bytes of the base style that were previously part of the following 9,053-byte span.

## Inline annotation settings

The [annotation settings reader](../../../../re/solidworks/archive/ConfigAnnot.py) consumes 1,956 bytes from the inline call at `sldmfcu+0x13a424` to the next member call at `0x13a434`. The `moAnnotationDefs_c` load branch at `0x135cf4` reads the scalar settings and invokes the members identified by the constructor at `0x82ff0`. The sequence is balloon, note, datum, geometric tolerance, surface finish, weld, bend note, plain base, revision cloud and view location label.

Each member uses `moBaseAnnotationDefs_c` at `0x136430`, including a guarded absent layer, two inline line widths and a framed character format. The subclass load paths add scalar settings, three framed strings for balloons and a second character format for welds. The revision cloud and view location label layouts close the annotation section without archive allocations.

## Inline table and label settings

In baseline A, the [table settings](../../../../re/solidworks/archive/ConfigTable.py) run from decompressed offsets 28,368 to 29,834. The `moTableDefs_c` serializer at `sldmfcu+0x1402e0` invokes nine inline table members identified by the constructor at `0x1b33f0`. Each shares `moGeneralTableDefs_c` at `0x13d640`, which reads the layer-free settings, two widths and a font. The revision and bill-of-materials variants add framed strings. A separate inline font follows the hole table, and the parent ends with two doubles.

The [label settings](../../../../re/solidworks/archive/ConfigLabel.py) follow from offsets 29,834 to 33,404. The `moLabelDefs_c` serializer at `0x13e7d0` visits five label members identified by the constructor at `0x127480`, with a separate inline font after the auxiliary member. The shared loader at `0x14d8c0` reads the guarded absent layer, two framed strings, six character formats and two line widths. The orthographic and miscellaneous vtables both select the serializer at `0x14dd50`.

## Annotation helpers and geometric tolerance frames

The [annotation helpers](../../../../re/solidworks/archive/ConfigAnnoData.py) continue from baseline A offset 33,404 to 35,177. The current surface finish, note and weld loaders begin at `sldmfcu+0x13fd00`, `0x13eb50` and `0x140670`. Their shared annotation helper at `0x1359e0` reads a font and two leader groups. The note loader has a separately counted 64-bit map which must be empty. The weld loader reads two additional character formats and calls the surface finish loader twice at `0x140cec` and `0x140cfc`.

The [tolerance helper](../../../../re/solidworks/archive/ConfigTol.py) reads the inline frame count at `sldmfcu+0x13ccf3`. Each `moGTolDlgDataFrame_c` load path at `0x13d259` reads five strings, two byte fields, six counted string arrays, and scalar fields. The two calls at `0x13d480` and `0x13d48c` read typed tolerance pointers which are null in this discovery scope. Datum and indicator collections must be empty. Baseline A reaches the recorded pointer pairs at offsets 35,225 and 35,227, then 35,277 and 35,279. The helper closes at 35,565.

## Remaining detail settings

The [detail settings tail](../../../../re/solidworks/archive/ConfigDetailEnd.py) reaches the serializer return at baseline A offset 37,959. Each center mark and datum record contains the existing inline annotation helper. All exercised Swift option fields are primitive integers and doubles. The eight printer widths are floats, and the final detail fields include two character formats and framed templates.

| Record | Load branch in `sldmfcu` | Baseline A bytes |
| --- | --- | ---: |
| Center mark | `0x136e7f` | 179 |
| Datum feature | `0x137341` | 170 |
| Datum target | `0x137580` | 235 |
| Swift options | `0x11ce81` | 812 |
| Printer widths and detail tail | `0x12ad10` and `0x13ae54` | 998 |

Two checked zero bytes at the boundary have unassigned ownership. The next typed declaration is `moEnvFolder_c` at offset 37,961.

## Environment lights and model view suffix

The [environment reader](../../../../re/solidworks/archive/ConfigScene.py) follows the folder serializer at `sldmodu+0xd70af0` into its concept and feature fields. The saved four-entry list carries one ambient light and three directional lights. Each child reads its node name, nullable feature fields and the light body at `0xaca160`. The user name is framed text, the user property count is zero, and directional lights add a vector and a double at `0xac97b2` and `0xac97e9`. The folder resumes its inherited feature fields after the fourth light and ends with its own two integers.

The model's fields after the view loop reach the schema-zero `moFeatColorTab_c` at baseline A offset 41,476. Its serializer at `sldmfcu+0xd21c0` reads the empty color table count. The model reads the following null pointer and three integers, including the zero count for an optional inline node list at `sldmodu+0x10f2d12`. Its next typed object is `moSketchBlockMgr_c` at offset 41,516.

## Saved managers and annotation views

The sketch block manager serializer at `sldmodu+0x17c8d90` reads an inherited feature, a 16-byte GUID, and its inline block settings. The settings load path at `0x17c6991` reads an integer and a reference to the same manager object already allocated at the start of the record. The following block and name tables must be empty.

The annotation view serializer at `0x10d4900` reads the existing inline model view body before its own fields. It reads four nullable references at `0x10d4b8a`, `0x10d4c78`, `0x10d4d43` and `0x10d4de8`, followed by the type's integer tail. The replay preserves the one-view and two-view list paths.

The partition marker at `0x9d9b30` reads one integer. The cosmetic thread manager at `0x1a57d0` reads an empty reference-list count and its trailing integer. The exploded-view manager at `0x52d0b0` uses the inherited feature and two nullable child references before its double and two integers. Parent fields around the marker, between the managers and in the final 38-byte trailer still use bounded advances.

## Verification

Run `python re/solidworks/archive/ConfigMap.py` from the repository root. The report for eleven P04 captures retains SHA-256 `d54ce30559d5905d56c290f4dabb3e961861673afeccc3071dc7cac40202853a`. The P04 resolved-list modes and the P01/P03 rectangular modes retain their exact prior report bytes. The revised reader matches every presentation pointer offset, allocation counter and token in the seven licensed controls. That covers 87 events per P01 baseline A and YZ archive, 92 per P03 baseline A and YZ archive, and 92 per P04 baseline A, YZ and width edit archive. [Native map evidence](../../../../re/solidworks/records/P04SketchResidence.md#offline-map-replay), [rectangular report commands](SolidWorksRectangularPlaneEvidence.md)

In a memory-only baseline A control, increasing the first line font name and its enclosing split length by 16 bytes shifted all subsequent pointer offsets by 16 while preserving the exact token and allocation sequence through stream end. A second control replaced the dual unit's null child with a length class reference and was rejected at that boundary.

An additional memory-only control added a 30-byte balloon property name and reached stream end with the same map and the expected pointer offsets. An altered annotation layer ID was rejected at the layer field.
