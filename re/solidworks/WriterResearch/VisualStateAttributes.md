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

For profiles, the classifier reads `moProfileFeature_c::getBlankStatus` at `0x4a633` and consults the feature owner at `0x4a642`. The getter at `sldmodu` RVA `0xf93d50` reads `[feature+0x3d0]+0x100`. Status 2 selects visibility one. Status 4 uses the typed owner and accepts an independent profile or a context outside the body-feature and reference-surface cases. Each resolved archive binds the selected profile to `RectangleSketch` ID 26 and independently identifies `Origin` ID 5. Each ModelHeader sets the document-wide `VisibleSketches` field to false. That flag alone cannot explain the saved local visibility of one. The independent saved or authored source of the live profile blank-status at `+0x100` remains unresolved.

## Holder appearance and its allocation

The standalone holder path at `0x932d0` obtains the configuration's cached visual property at `0x9346c` and can fall back to `moConcept_c::getVizPropDirectNonConst` at `0x9347d`. A material branch checks `cachedVizProp_c::applyDefaultPWMaterial` at `0x93587`. The latter is a getter for cache policy byte `+0x69` in `sldmodu`. When default material preparation is needed, helper `0x96650` reuses existing RealView properties or calls `CreateAppearanceVizPropFromVizProp` at `0x96724`. The visual-properties attribute constructor can obtain the holder's visual property through its native virtual `+0x1040` at `0x4a088`, copy it at `0x4a0e9` and install that pointer at object `+0x10`.

These paths establish the live holder property and a conditional source for its default material. The observed sidecar property ID 3, CMgr IDs 4 or 5 and final manager counters 5 or 6 still leave the preceding allocation calls unobserved. A fresh writer needs a proven allocation sequence from the authored document's material lifecycle before assigning the sidecar property identity. This replay establishes the principal-plane visibility input and the ordinary representation defaults within the observed route. The profile's local blank state and the initial appearance allocation still gate complete construction. [Appearance allocator and capture IDs](VisualStateOwners.md#appearance-identity-and-locator)
