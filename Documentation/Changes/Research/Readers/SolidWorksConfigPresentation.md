# SOLIDWORKS configuration presentation records

The [configuration map replay](../../../../re/solidworks/archive/ConfigMap.py) reads 2,556 previously skipped bytes per discovery capture as typed fields. The build and capture receipt still scope the whole presentation walk.

| Record | Layout in build 34.4.1.1011 |
| --- | --- |
| Nine nested length units | The load branch of `sldmfcu!moUserUnits_c::Serialize` at RVA `0x1ecde5` reads 62 bytes. The subtype at `0x1ecb30` reads an unsigned 16-bit length code, then invokes the typed pointer reader at `0x1e91c0` for its child. The witnessed child is null in each body. |
| Ten model views | The load branch of `sldmodu!moView_c::Serialize` at `0x10ea3a9` reads its name, two transforms, and scalar fields separated by three collection counts. All three collections are empty in the witnessed views. The two auxiliary lists are inline when present. |
| Model and annotation transforms | The `sldmgu!mgXform_c::restore` path at `0x331d0` reads the matrix-present flag, an optional nine-double matrix, four translation and scale doubles, and an extension mode byte. Mode zero is required. |

The ten views consume 1,980 bytes in the observed captures. Each parsed body reaches its next type token, except the last view, which ends nine bytes before the feature-color table. That intervening data remains an opaque advance. The dimension-style intervals between length pointers and the subsequent 9,053-byte advance are still open. The ten-view sequence remains bounded by the witnessed ordinary model shape.

Run `python re/solidworks/archive/ConfigMap.py` from the repository root. The report for eleven P04 captures retains SHA-256 `d54ce30559d5905d56c290f4dabb3e961861673afeccc3071dc7cac40202853a`. The P04 resolved-list modes and the P01/P03 rectangular modes retain their exact prior report bytes. The revised reader matches every presentation pointer offset, allocation counter and token in the seven licensed controls. That covers 87 events per P01 baseline A and YZ archive, 92 per P03 baseline A and YZ archive, and 92 per P04 baseline A, YZ and width edit archive. [Native map evidence](../../../../re/solidworks/records/P04SketchResidence.md#offline-map-replay), [rectangular report commands](SolidWorksRectangularPlaneEvidence.md)
