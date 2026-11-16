# Standalone P03 visual-state owners

Eight generation-19000 P03 saves at `466dcb172dfa3803463e07ccde963ba01671d200` establish the saved default display-state graph. The sources below use RVAs in the pinned SOLIDWORKS 34.4.1.1011 modules. The observations extend the stream framing and independent feature-log joins already recorded. [P03 receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json) [Visual-state framing](VisualStates.md)

## Default configuration representation

The loader continuation in `sldvisualstateu.dll` can construct `visStateKeyData_c` at `0x7cf8a` using the in-memory configuration manager. The constructor is `0x72cb0`, identified by RTTI and its serializer slot pointing to `0x3ff50`. It initializes the representation-number source `+0xb4` to zero at `0x72dba`. For the standalone part branch, the continuation calls the state builder at `0x7d3a1` with the current configuration object and mode 1. The builder at `0x7e0b0` reads `+0xb4` through `0x8fb50`, adds one and retains that result at `0x7e131–0x7e138`. The first such representation is therefore ID 1. The full counter lifecycle for several representations remains open.

The ordinary part name at `0x7e5b7–0x7e62d` comes from `moBaseConfiguration_c::getName`, localized string resource `0x4951` and format `<%s>_%s %d` with ordinal 1. The builder takes the configuration's native ID by virtual call at `0x7e7a8`, installs its relationship to the new representation at `0x7e7c7`, and inserts or finds the named representation by its new ID at `0x7e7fa`. That ID also reaches the object's field through `0xa4c50`. The observed relationship and representation own the same archive ID.

| Saved offset | Typed observation in all eight archives | Source |
| ---: | --- | --- |
| 31 | Root word 5 | Root `+0x15c` from constructor at `0x72e42`, constant-return helper `0x43c20`, stored at `0x400c3`. |
| 35 | Root word 0 | Root `+0x158` initialized to zero at `0x72e37` and stored at `0x4012f`. The post-load continuation can set it to 1 at `0x7d16f`. |
| 39–55 | One relation, configuration ID 0, representation ID 1, marker 1 | Count and row from `0x4014d–0x401bd`. |
| 55–117 | One representation, ID 1, name `<Default>_Display State 1` | Filtered count, row key and wide name from `0x401f6–0x403fd`. |
| 117–129 | Three zero scalars | Representation-row members `+0x384`, `+0x394` and `+0x38c` stored through `0x4042a`. Their full semantics are unresolved. |

## Appearance identity and locator

The root holder's appearance has unsigned 64-bit ID 3 at byte 460 in every VisualStates member. The same document's CMgr appearance has ID 4 or 5 at byte 392 and the saved Definition manager counter is 5 or 6, respectively. Baseline A, YZ and reverse direction carry `(3, 4, 5)`; baseline B, its three edits and the inch save carry `(3, 5, 6)`. The common DSPBR body still compares byte for byte. This distinguishes a separately bound sidecar appearance from the CMgr appearance even when they use the same material. [Definition counter](DefinitionJournal.md#appearance-id-counter) [CMgr appearance](CmgrVisual.md#material-and-realview-research-constructor)

The visual-state appearance rekeying path at `sldvisualstateu` RVA `0x48fc0` finds the document through `ModelContext_c::Document` and calls its virtual `+0x1640` method at `0x490dc`. The primary `uiPartDoc_c` table in `sldprtu.dll` selects the import thunk at `0x195f73` for that slot. It calls `slduiu!uiModelDoc_c::getPWMaterialManager`, whose implementation at `0x474e0` returns the very same `+0x1110` manager saved by Definition. The visual-state path calls `PWMaterialManager_c::getNewApperanceID` at `0x49324`, `0x49348` and `0x49398`. It installs IDs on visual material objects through `uoMaterialProperties::setPWMaterialPropertyID` at `0x493a4` and reuses an assigned ID for another matching attribute at `0x4944f`. The manager returns the current 64-bit value and advances it at `sldmodu` RVA `0x10bd340`. This establishes the document allocator and the separate sidecar binding. The exact original allocation chronology that assigned 3 to the saved default appearance is unobserved.

At byte 581 each sidecar saves the wide locator `<SystemTexture>\graphics\materials\color.p2m`. The RealView writer at `sldmfcu` RVA `0x177f39–0x177f4c` writes the `+0x68` filename on this ordinary branch. The exported `uoRVAppearanceProperties::getFilename` at `0x176040` resolves the 15-character token by appending the remaining path to `ui_GetDataDir(1)` at `0x1760ac–0x1760bc`. The appearance converter calls this resolver at `0x55f3a`. The CMgr stores an absolute capture-installation locator in the corresponding field. The sidecar can use the native token plus the relative installed asset suffix independently of that path.

## Component and attribute references

The default-state builder reaches `0x932d0` at `0x7e879`. This path takes `moModel_c::getSelfComponent` at `0x934c0` into the native `moCompHolder_c` constructor at `0x934d2`. In `sldmodu` the holder serializer at `0xa65a60` forwards to `moCompRef_c::Serialize`. The reference base emits its `+0x58` component pointer at `0xa662ef` or `0xa662fe` on the object-pointer route. The separate feature population at `0x93060` requests reference geometry, reference curves and profile features from the opened model and constructs `moCompFeature_c` with the self component and the feature at `0x9315b`.

The root serializer writes an empty filtered component vector at byte 129 through `0x407f0`. The second component-owner map at `0x40bfe` owns the six rows beginning at byte 133. At byte 137 the first row defines `moCompHolder_c` as archive object 4. Its component at 157 defines `moUnitComponent_c` as object 6. The holder row binds the sole representation ID 1 and two distinct attributes. The first is visual-properties attribute object 8 at byte 275, containing a fresh visual object 10 at byte 320. The second is state attribute object 12 at byte 1125. [Component collection framing](VisualStateWire.md#two-component-collections)

The typed cursor resolves the following links in the same order across all eight saves. Each row has one binding to representation ID 1 and two attribute pointers. Object numbers refer to this member's own archive map.

| Owner and saved feature ID | Pointer offset | Feature object | Unit component object | Visual-properties attribute | Visual-state attribute |
| --- | ---: | ---: | ---: | ---: | ---: |
| RectangleSketch, 26 | 1181 | 14 | 15 | 16, new class reference with null visual child | 12, existing |
| Origin, 5 | 1317 | 17 | 18 | 16, existing | 12, existing |
| Right Plane, 4 | 1428 | 19 | 20 | 16, existing | 21, new class reference |
| Top Plane, 3 | 1559 | 22 | 23 | 16, existing | 21, existing |
| Front Plane, 2 | 1670 | 24 | 25 | 16, existing | 21, existing |

Every feature row creates a fresh unit component through the prior class slot 5. The allocation at 1307 creates object 16 through class slot 7 with selector 1 and a null visual pointer. The allocation at 1537 creates state object 21 through class slot 11. Its base selector and four signed fields are `(1, 0, 6, 1, 0)`, compared with `(1, 1, 6, 1, 0)` for object 12. These shared references and two state shapes recur in all eight files. The final attribute reference ends at byte 1781 with next archive index 26. The component payloads and two empty terminal counts have typed owners. The state-attribute fields still need attribution. [Typed component records and terminal counts](VisualStateWire.md)

## Missing-member behavior

The native loader opens `ThirdPtyStore` at `0x7cb09–0x7cb3b`, tries `VisualStates` at `0x7cba9`, and falls back to `VisualStates-Dev` at `0x7cc15`. If both are missing it reaches the null archive test at `0x7cc63`, bypasses deserialization and enters `0x7cdf7`. Under its document predicates it visits open configuration models, releases existing state at model `+0xd60` and clears that pointer at `0x7cead–0x7ceb0`. The path rejoins the normal continuation that can initialize the fresh root above.

A licensed omission witness should remove both member names from a single receipt-bound ordinary P03 scratch input, preserve the inline configuration and appearance, and observe the display state before and after rebuild, a driving-dimension change, save and fresh reopen with healthy controls. If native save recreates the member, compare appearance, default representation, each row's feature ownership and shared attributes by role. If it remains absent, record whether the same appearance and visibility state are independently observable in the application. The current generation-19000 omission campaign retained VisualStates. [Existing licensed campaign](../../../Documentation/Changes/Research/Writers/SolidWorks/SolidWorksArchiveOmissions.md)

## Evidence pins

The component and attribute pointers were checked by the existing archive cursor with local class and object maps seeded at index 1. The replay used the receipt's eight input file hashes, the native rows above and the independently saved CMgr and Definition values. Embedded native positions describe the measured framing. New construction would supply ownership from the authored configuration, feature identities, display state and actual material allocation.

| Installed module | SHA-256 |
| --- | --- |
| `sldvisualstateu.dll` | `bcbe477995e6631e8b339f8ed043f6ef0b9c2450c5cce5c67cabeff27cb85e2a` |
| `sldmodu.dll` | `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99` |
| `sldmfcu.dll` | `bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6` |
| `slduiu.dll` | `88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6` |
| `sldprtu.dll` | `cb1e260f8411a39dc44f4d8a6255ea585c7a5e60b223d0e69d3f51a258ee96de` |
