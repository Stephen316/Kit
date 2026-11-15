# SOLIDWORKS configuration presentation records

The [configuration map replay](../../../../re/solidworks/archive/ConfigMap.py) replaces 9,917 bytes of fixed advances per discovery capture with field reads. The build and capture receipt still scope the whole presentation walk.

| Record | Layout in build 34.4.1.1011 |
| --- | --- |
| Nine nested length units | The load branch of `sldmfcu!moUserUnits_c::Serialize` at RVA `0x1ecde5` reads 62 bytes. The subtype at `0x1ecb30` reads an unsigned 16-bit length code, then invokes the typed pointer reader at `0x1e91c0` for its child. The witnessed child is null in each body. |
| Ten model views | The load branch of `sldmodu!moView_c::Serialize` at `0x10ea3a9` reads its name, two transforms, and scalar fields separated by three collection counts. All three collections are empty in the witnessed views. The two auxiliary lists are inline when present. |
| Model and annotation transforms | The `sldmgu!mgXform_c::restore` path at `0x331d0` reads the matrix-present flag, an optional nine-double matrix, four translation and scale doubles, and an extension mode byte. Mode zero is required. |

The ten views consume 1,980 bytes in the observed captures. Each parsed body reaches its next type token, except the last view, which ends nine bytes before the feature-color table. That intervening data remains an opaque advance. The ten-view sequence remains bounded by the witnessed ordinary model shape.

## Detail settings before the first length pointer

The [detail settings reader](../../../../re/solidworks/archive/ConfigDetail.py) replaces the initial 1,183-byte presentation advance. Two leading zero bytes remain a checked boundary word with unassigned ownership. The modern `moDetailDefs_c` load branch at `sldmfcu+0x137c50` reads scalar settings and framed text. The continuation at `0x139eb8` reads the signed exclusion-name count, and `0x13a1a0` and `0x13a280` read three eight-integer rows each. The call at `0x13a3d9` reads the priority labels, which use the short count form in these archives.

At `0x13a401`, the reader enters the inline character format. The call at `0x13a414` enters the dimension settings at `0x13b8d0`. It reads the scalar settings before the first style at `0x13be26`. The linear style at `0x13e9a0` delegates to `moBaseDimDef_c::Serialize` at `0x1366a0`. The supported branch guards the unused layer ID, then uses the inline length-unit reader called at `0x136a5d`. Its typed child is the first presentation pointer.

## Dimension styles through the annotation settings boundary

The calls from `sldmfcu+0x13be26` through `0x13bf47` follow the inline members identified by the `moDimDefs_c` constructor at `0xbeb10`. The order is linear, angle, arc length, radial, hole callout, ordinate, chamfer, diameter, angular ordinate and base. Each call reads the shared style fields before the subclass tail. The in-stream dual-length pointer may be a typed class reference or null. The observed angle style is null, and the other nine allocate length records with no further child.

After the length pointer, the shared base serializer reads the inline angle unit at `0x136a6d`, the character format at `0x136a7d`, two line font records at `0x136a8d` and `0x136aae`, and three final integers. The line font serializer at `0x87650` reads a framed name, an inline short and float width via `0x12a6e0`, and another short. The subclass load paths supply the remaining primitive fields. The ten style continuations replace 4,222 bytes of fixed advances, including the last 240 bytes of the base style that were previously part of the following 9,053-byte span.

## Inline annotation settings

The [annotation settings reader](../../../../re/solidworks/archive/ConfigAnnot.py) consumes 1,956 bytes from the inline call at `sldmfcu+0x13a424` to the next member call at `0x13a434`. The `moAnnotationDefs_c` load branch at `0x135cf4` reads the scalar settings and invokes the members identified by the constructor at `0x82ff0`. The sequence is balloon, note, datum, geometric tolerance, surface finish, weld, bend note, plain base, revision cloud and view location label.

Each member uses `moBaseAnnotationDefs_c` at `0x136430`, including a guarded absent layer, two inline line widths and a framed character format. The subclass load paths add scalar settings, three framed strings for balloons and a second character format for welds. The revision cloud and view location label layouts close the annotation section without archive allocations.

Baseline A reaches `moTableDefs_c` at decompressed offset 28,368. The next open interval begins with that serializer and covers 6,857 bytes to the next traced null pointer in these archives.

## Verification

Run `python re/solidworks/archive/ConfigMap.py` from the repository root. The report for eleven P04 captures retains SHA-256 `d54ce30559d5905d56c290f4dabb3e961861673afeccc3071dc7cac40202853a`. The P04 resolved-list modes and the P01/P03 rectangular modes retain their exact prior report bytes. The revised reader matches every presentation pointer offset, allocation counter and token in the seven licensed controls. That covers 87 events per P01 baseline A and YZ archive, 92 per P03 baseline A and YZ archive, and 92 per P04 baseline A, YZ and width edit archive. [Native map evidence](../../../../re/solidworks/records/P04SketchResidence.md#offline-map-replay), [rectangular report commands](SolidWorksRectangularPlaneEvidence.md)

In a memory-only baseline A control, increasing the first line font name and its enclosing split length by 16 bytes shifted all subsequent pointer offsets by 16 while preserving the exact token and allocation sequence through stream end. A second control replaced the dual unit's null child with a length class reference and was rejected at that boundary.

An additional memory-only control added a 30-byte balloon property name and reached stream end with the same map and the expected pointer offsets. An altered annotation layer ID was rejected at the layer field.
