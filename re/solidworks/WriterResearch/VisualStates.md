# Standalone part visualization state

The eight receipt-pinned P03 saves from revision `466dcb172dfa3803463e07ccde963ba01671d200` retain a 1,789-byte `ThirdPtyStore/VisualStates` member. Reconstructing the ordinary part's display state requires its populated representation map. [Capture receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)

## Native save and archive context

The installed SOLIDWORKS 34.4.1.1011 `sldvisualstateu.dll` has SHA-256 `bcbe477995e6631e8b339f8ed043f6ef0b9c2450c5cce5c67cabeff27cb85e2a`. The save routine at RVA `0x81330` opens the member at `0x813d8`, installs archive conditions `0x20004000` at `0x8148a` and writes the unsigned version, signed document flag and `visStateKeyData_c` pointer. The loader reads the same three items at RVAs `0x7ccc8`, `0x7cd6b` and `0x7cda9`.

The root object's serializer at `0x3ff50` writes its `+0x15c` field, then constructs temporary representation lookup maps at `0x3f450`. It writes an independent `+0x158` field, the count at `+0x120` and relationship rows at `0x40160–0x401bd`. From `0x401d7` to `0x40453` it writes selected representation entries using the actual names and three scalar members. The next stage gathers the configuration objects and their component owners at `0x40488–0x40584`. Later paths serialize typed object maps and call the model's `moDisplayedEntityTracker_c::Serialize` at `0x40f9b`. This context differs from the combined Config-0 and ResolvedFeatures archive. [Archive counter observation](../archive/Multistream.md#2-does-the-segmentation-model-transfer)

The eight saved prefixes contain version 19000, document flag 0 and a schema-1 `visStateKeyData_c` definition at byte 8. At byte 31 the consecutive words are `(5, 0, 1, 0, 1, 1, 1, 1)`. They lead to the wide string `<Default>_Display State 1` at byte 63. A schema-1 `moCompHolder_c` definition follows at 137 and owns the first `moUnitComponent_c` definition at 157. These positions identify the ordinary populated route. Equal prefixes alone do not prove default ownership for every flag.

## Typed appearance and feature evidence

The schema-1 `visStateVisualPropertiesAttribute_c` at byte 275 writes a base attribute selector and a typed visual-properties pointer. Its native serializer at `0x42800` passes the pointer to the `moVisualProperties_c` archive operator at `0x4283f`. The reached visual definition begins at 320. The existing `ReadVisualSpan` consumes its body from byte 346 to 1125 on all eight files. Its 300-byte DSPBR range begins at 825 and equals the independently typed CMgr DSPBR body in every save. The RealView prefix carries a native `<SystemTexture>` asset locator. The CMgr writer's absolute installation path and appearance ID policy cannot be assumed for this context. [Typed appearance reader](CmgrColorReadback.py) [Appearance constructor scope](CmgrVisual.md)

The next schema-1 object at 1125 is `visStateVisualStateAttribute_c`. Its serializer at `0x42880` writes the base attribute and four signed fields. The following first `moCompFeature_c` definition is at 1181. Five later version, tree ID and clock triples agree with independently decoded creation logs in every saved ModelHeader.

| Triple offset | Tree ID | Owned feature |
| ---: | ---: | --- |
| 1283 | 26 | RectangleSketch |
| 1400 | 5 | Origin |
| 1511 | 4 | Right Plane |
| 1642 | 3 | Top Plane |
| 1753 | 2 | Front Plane |

The edited width and height captures advance the sketch's modification times while retaining its creation clock in VisualStates. The YZ and reverse-direction reauthors change only the sketch creation clock at 1291 in this stream. The body appearance and reference roster are byte-identical. The native IDs and clocks can therefore come from authored feature logs. This read-only join does not establish the full allocation and map-entry grammar.

## Remaining decision

The follow-up owner trace establishes the first representation ID, its configuration relationship, the visual appearance allocator, and the component and attribute references. Construction still needs the original appearance-allocation sequence and attribution of the unit-component payloads, state flags and footer. The existing CMgr visual constructor accounts for the shared 300-byte DSPBR body. [Visual-state owners](VisualStateOwners.md)

A generation-19000 omission campaign can establish whether the ordinary display state regenerates after open, rebuild, driving-dimension edit, save and fresh reopen. Older generation-18000 evidence covered a narrower visual-state omission. The current P03 omission run retained this member. [Earlier omission](../archive/Multistream.md#4-which-streams-are-load-critical) [Current licensed campaign](../../../Documentation/Changes/Research/Writers/SolidWorks/SolidWorksArchiveOmissions.md)
