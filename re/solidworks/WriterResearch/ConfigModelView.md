# Configuration model presentation

`WriteModelView` resumes the generation-19000 [configuration units table](ConfigUnits.md) at archive counter 43. It files the local model component, two empty face visualization collections, the unexploded state, an optional curvature object, and the reference-plane presentation. The writer derives the model owner slot from the prior root definition and standalone allocation. The reader checks that the alias resolves to that enclosing `moPart_c`, and rejects external components, nonempty face appearance lists, or an exploded model in this scope.

## Native field authority

Preferred addresses below refer to the [pinned sldmodu](ConfigRoot.md#native-field-authority) and [sldmfcu](CmgrVisual.md#version-and-ownership) images from the installed 34.4.1.1011 release.

| Filed record | Source and interpretation |
| --- | --- |
| Local unit component | `moModel_c` allocates its `+0x990` member at `0x4c00ce70` through the public `moUnitComponent_c` constructor `0x4b827650` and saves it at `0x4c22c650`. The same store calls `moFeatureRefMgr_c::Serialize` first at `0x4c22c642`. The manager constructor `0x4bb35990` assigns the `moFeatureRefMgr_c` RTTI-confirmed virtual table `0x4cf57f08`, whose storing route at `0x4bb35c40` consumes no bytes on the measured branch. |
| Component ownership | The component virtual table `0x4ce994b0` selects `0x4c229990`. Its base serializer stores the local owning concept at `0x4c21a401` after selecting it at `0x4c21a41a`. The derived serializer's local branch writes the zero byte at `0x4c229cd0`. The 14 archived aliases resolve to the already registered model object at slot 2. |
| Face appearance and exploded state | The model store's `0x4c22c672` calls `moFaceVizProps_c::save` with member `+0xdd0`. That routine writes separate signed collection counts at `0x4c23f2de` and `0x4c23f410`, both zero in this scope. `0x4c22c683` writes the byte from the model's `+0xd30` member, also read by `moModel_c::isExploded` at `0x4b28d830`. |
| Curvature appearance | The model stores `+0xa70` through the typed `gcCurvatureObject_c` pointer at `0x4c22c694`. The object's serializer at `0x3c7d8dc0` writes five doubles from `+0x08` through `+0x28`, followed by low and high unsigned FILETIME words from `+0x58` and `+0x5c`. The object constructor at `0x3c7d7ed0` takes the five values as an array and calls `setCurvatureObjectTime`. This calls `GetSystemTime` and `SystemTimeToFileTime` at `0x3c7d892d` and `0x3c7d893c`. |
| Reference-plane presentation | `0x4c22c6a5` stores the model's `+0xdb0` object as `moTransRefPlaneData_c`. Virtual slot 5 is `0x4c6f1990`. Its stores file `i32` show edges, `i32` show intersections, `u32` front face color, `u32` back face color, `i32` transparency, and `u32` intersection line color. The six exported getters read `+0x8, +0xc, +0x10, +0x14, +0x18, +0x1c`, respectively. `0x4c033290`, `moModel_c::setDefaultPlaneColors`, writes both face colors using the typed setters. |

The 34.4.1.1011 `slduiu.dll` image SHA-256 is `88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6`. Its call at `0x490b3c2c` takes the settings from `uiEnvironment_c::getCurvatures` and passes them to the curvature constructor at `0x490b3c57`. It attaches the object to the model at `0x490b3c5e`. The `sldappu.dll` SHA-256 is `de39fa156eb9e92c030ec23c5d4a3a742aef941ec6246c7689c99ffb0abcd0b2`. The named getter at `0x45a4a810` copies five values from the environment settings object's `+0xb8` through `+0xd8`. The codec takes these settings and its creation FILETIME explicitly. It does not calculate appearance settings or cache presence from the boss dimensions. Reference-plane display properties are also explicit inputs, independent of the authored datum frames.

## Replay

```sh
python re/solidworks/WriterResearch/VerifyConfigView.py --read-only
```

All 14 receipt-pinned P01/P03 saves allocate local unit component class 43 and object 44. The six P01 saves have a null curvature pointer, an 88-byte span, and end at next index 47. The eight P03 saves have curvature class 45 and object 46, a 159-byte span, and end at next index 49. They share five settings `(1000, 31.6, 4, 1.2, 1)` and include three observed FILETIMEs. Six P03 captures retain one time across repeated saves and edits. Both lanes carry plane appearance `(1, 1, 0xf78453, 0x672305, 95, 0)`. The replay SHA-256 is `55dc06d858890565b1422363d76a22c12fde4e88c2bd573edf7ff559c6702569`. Its rows contain the archive SHA-256, boundaries, counters, parsed cache and display state, and the span SHA-256.

Hosted `CheckConfigView` reconstructs and compares the span using the inherited allocator. The current evidence is read-only. The following model bounding-box selector and later material fields remain outside this codec.
