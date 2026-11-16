# Standalone P03 visual-state attribute sources

The eight receipt-pinned P03 saves at `466dcb172dfa3803463e07ccde963ba01671d200` carry the same three representation scalars and the same two interned state attributes. The independent replay reads the sidecar, CMgr, ModelHeader and typed resolved-feature records from each exact archive. Native addresses below are RVAs in the installed SOLIDWORKS 34.4.1.1011 libraries. [P03 receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json) [Native module pins](VisualStateOwners.md#evidence-pins) [Component records](VisualStateWire.md)

## Representation scalars

The `sldvisualstateu` serializer at `0x40403–0x4042a` writes the following three fields from the representation map node. Its contained record begins at node `+0x28`.

| Node field | Record field | Archive scalar | Source in the standalone route |
| --- | --- | --- | --- |
| `+0x384` | `+0x35c` | Signed long | The creation path reads the live owning configuration's virtual `+0x188` ID at `0x7e827` and stores it at `0x7e82d`. All eight CMgr records independently name `Default` with native ID 0, matching this scalar. |
| `+0x394` | `+0x36c` | Signed int | The representation record constructor clears the word at `0x9f9bb`. |
| `+0x38c` | `+0x364` | Signed int | The constructor clears the containing qword at `0x9f9b4`. |

The creation path sets the separate representation allocation ID through `0xa4c50` into record `+0x358`. ID 1 on these rows comes from the representation allocator. The lookup's temporary-record constructor call at `0x3f2e0` supplies a null optional host pointer. Its binding helper `0xa4b00` leaves the two constructor defaults intact on that branch. The bound branch can set the words at `0xa4bef` and `0xa4c14` based on live model and configuration context. Other transfer paths write the same members. The saved pair `(0,0)` is consistent with the ordinary unlinked branch. The alternate branches preclude assuming universal zero values or assigning a visibility meaning to the pair. [Representation identity](VisualStateOwners.md#default-configuration-representation)

## Typed state attributes and saved visibility

The unsigned `visStateAttribute_c` selector at object `+0x8` has constructor value 1 at `0x44f49`. The base serializer stores it at `0x3fe6a`. The derived `visStateVisualStateAttribute_c` serializer appends four signed longs in this order.

| Object member | Native config-object getter | Serializer write |
| --- | --- | --- |
| `+0x10` | `getVisibility` at `0x49cae`, normalized to a Boolean at `0x49cb9` | `0x428c4` |
| `+0x14` | `getDisplayMode` at `0x49ca1` | `0x428d0` |
| `+0x18` | `getEdgesInShadedMode` at `0x49c96` | `0x428dc` |
| `+0x1c` | `getHlrDisplayQuality` at `0x49c8b` | `0x428e8` |

The config-object path passes these values to the constructor at `0x49cc9`. The live standalone feature and self-holder callers use the descriptor's classifier at `0x4a3b0` through calls at `0x931ee` and `0x9367e`. The self-holder call supplies the actual part configuration. The ordinary branch starts at `(1,6,1,0)` at `0x4a44c–0x4a45b` and dispatches special cases for typed features. The writer can reuse attribute objects when the descriptor finds the same state at `0x4a7ba–0x4a857`.

All eight sidecars save object 12 at byte 1161 with selector and values `(1,1,6,1,0)` for the self holder, `RectangleSketch` and `Origin`. Object 21 at byte 1539 carries `(1,0,6,1,0)` for all three principal reference planes. For those planes, the classifier reads `moRefGeom_c::getBlankStatus` at `0x4a591`. The getter in `sldmodu` at `0x118bdb0` returns the low two bits of `+0x6dc`. The native reference-geometry serializer writes the corresponding flags at `0x11342f9`. The independent typed resolved walk found plane IDs 2, 3 and 4 and raw flags 5 at offsets 3273, 3792 and 4362 in all eight captures. All 24 words yield blank status 1 and select visibility zero in the classifier. [Saved attribute links](VisualStateOwners.md#component-and-attribute-references)

## Profile blank status

`moProfileFeature_c` holds its profile-data record at `+0x3d0`. The constructors in `sldmodu` install that record at `0xf889ef` or `0xf88bf0` and initialize its `+0x100` blank status to 4 at `0xf88408` or `0xf88186`, respectively. Both constructors initialize the alternate `+0x104` status to 4 and clear selector `+0x10c`. The live `setBlankStatus` path writes the requested enum to `+0x100` at `0xfa2a8f`. The getter used by the sidecar classifier reads the same member at `0xf93d57`.

The primary `moProfileFeature_c` archive slot 5 is `0x9db0b0`. After the optional transform and before the derived-profile pointer, the store writes an unsigned short at `0x9db9c6`. It selects `+0x100` at `0x9db9bf` when `+0x10c` is clear and `+0x104` at `0x9db9b6` when the selector is set. The matching load at `0x9dc1b5` reads the short, zero-extends it and writes it to `+0x100` at `0x9dc1c6`. Before generation `0x5a` the loader instead maps the old zero or nonzero word to 4 or 3, respectively. The generation-19000 records use the direct load. [Enclosing profile tail](RectangleTrim.md#native-ownership)

The receipt-pinned replay advances through the typed system planes, Origin, RectangleSketch, contour chain and supporting-plane reference to the start of `ReadRectTrim` in `Contents/Config-0-ResolvedFeatures`. All eight saves carry status 4 immediately after the zero transform-presence word. The next fields are the null derived-profile pointer and signed values `(-1,0)`. The following typed trim returns to `moExtrusion_c`. Its sole profile reference aliases the same reached profile at object slot 176 and document feature ID 26. [Typed trim guard](../../../src/convert/adapters/solidworks/Resolved/ContourTrim.py) [Typed Boss reference](../../../src/convert/adapters/solidworks/Resolved/BossEntry.py)

| P03 controls | Trim start | Status offset | Unsigned status | Saved sidecar visibility |
| --- | ---: | ---: | ---: | ---: |
| Positive XY, six saves | 11625 | 11627 | 4 | 1 |
| Reverse direction on XY | 11625 | 11627 | 4 | 1 |
| YZ support | 11697 | 11699 | 4 | 1 |

The read-only replay records the file, resolved stream and sidecar digests, the reached profile and datum, the framed status and the matching Boss and sidecar references in receipt order. The private JSONL evidence has SHA-256 `207b6bd16bdf7637990168315527f375cede0b94ab3859370b2d8ec071184c5d`. Each `ModelHeader` independently sets the document-wide `VisibleSketches` field to false. The profile's local status has its own saved source.

The sidecar classifier calls the profile getter at `sldvisualstateu` RVA `0x4a633`. Status 2 selects visibility one. Status 4 consults the feature's runtime owner at `0x4a642` and selects one if that owner is null or belongs to neither `moBodyFeature_c` nor `moRefSurface_c`. The primary profile vtable's `+0x1280` entry reads `moFeature_c` member `+0x290` at `sldmodu` RVA `0xa05050`. The inherited feature loader clears that pointer at `0x9d124e`; `setOwner` can later set it at `0xa10bde`. The typed Boss reference establishes saved profile selection. The subsequent owner binding for this exact profile and the lifetime of the alternate status selector at save time still need independent evidence before deriving the sidecar visibility for a fresh model.

## Holder appearance and its allocation

The standalone holder path at `0x932d0` obtains the configuration's cached visual property at `0x9346c` and can fall back to `moConcept_c::getVizPropDirectNonConst` at `0x9347d`. A material branch checks `cachedVizProp_c::applyDefaultPWMaterial` at `0x93587`. The latter is a getter for cache policy byte `+0x69` in `sldmodu`. When default material preparation is needed, helper `0x96650` reuses existing RealView properties or calls `CreateAppearanceVizPropFromVizProp` at `0x96724`. The visual-properties attribute constructor can obtain the holder's visual property through its native virtual `+0x1040` at `0x4a088`, copy it at `0x4a0e9` and install that pointer at object `+0x10`.

These paths establish the live holder property and a conditional source for its default material. The observed sidecar property ID 3, CMgr IDs 4 or 5 and final manager counters 5 or 6 still leave the preceding allocation calls unobserved. A fresh writer needs a proven allocation sequence from the authored document's material lifecycle before assigning the sidecar property identity. The saved profile blank status is now independently available. The profile's live owner binding, the alternate status selector's lifetime and the initial appearance allocation still gate complete construction. [Appearance allocator and capture IDs](VisualStateOwners.md#appearance-identity-and-locator)
