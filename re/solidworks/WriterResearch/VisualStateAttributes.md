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

The sidecar classifier calls the profile getter at `sldvisualstateu` RVA `0x4a633`. Status 2 selects visibility one. Status 4 consults the feature's runtime owner at `0x4a642` and selects one if that owner is null or belongs to neither `moBodyFeature_c` nor `moRefSurface_c`. The primary profile vtable's `+0x1280` entry reads `moFeature_c` member `+0x290` at `sldmodu` RVA `0xa05050`. The inherited feature loader clears that pointer at `0x9d124e`; `setOwner` can later set it at `0xa10bde`. The typed Boss reference establishes saved profile selection. The resolved-list owner repair and the alternate selector's lifetime are described below.

## Temporary status and the owner after reopen

The alternate selector at profile-data `+0x10c` belongs to the native blank-state override. `saveBlankStatus` at `0xfa26a0` copies current `+0x100` to `+0x104` at `0xfa26b6` and raises the selector at `0xfa26c3`. Its guard preserves the first snapshot if called again. `restoreBlankStatus` at `0xfa1380` copies the snapshot back at `0xfa13c4`, updates sketch graphics and clears the selector at `0xfa1421`. A separate query at `0xf9cd90` temporarily installs the saved state to evaluate the existing visibility virtual, then reinstates the current value at `0xf9cdd4`.

The pinned `slduiu` path at `0x124ee10` enumerates typed `moProfileFeature_c` children of a model feature. It snapshots their current state at `0x124ee8c`, then applies temporary status 2 at `0x124ee9d`. The counterpart enumerates the children and restores their state at `0x124b1a9`. This branch can therefore save status 4 into `ResolvedFeatures` while the sidecar classifier's direct getter observes live status 2. The eight archives preserve the saved status and the effective attribute. Neither stream identifies whether that override was active at the moment the sidecar was built. The capture harness exits the sketch before selecting it for extrusion. Baseline A, YZ and reverse are authored cases. Baseline B, the edits and the inch case save after reopening baseline A. [Capture lifecycle](../../automation/PairedCaptures/SolidWorksAuthoring/SolidWorksCapture.cs)

The modern resolved-node loader at `0x10357f0` selects virtual `+0x4c0` for generation `0xc7d` and later. Both `moExtrusion_c` and `moProfileFeature_c` select `0x1039160` in the pinned primary vtables. The extrusion's loaded child list attaches to its enclosing node at `0x10394ad`. The attachment helper stores the parent at list member `+0x48` and calls each child's virtual `+0x4d8` at `0x103a565`. For the profile this virtual is `0x1be0e0`, which increments the node reference count at `+0x10`. That explains how the saved Boss can own a child-list link while the profile's separately loaded runtime owner member `+0x290` remains null through this attachment.

After loading the top-level resolved list, `moModel_c::loadResolvedFeatures` inserts the reached features at `0x448abb` and passes the same loaded model as both model arguments to helper `0x10facf0` at `0x448b14`. A top-level node with a null runtime owner branches from `0x10fae4c` directly to the assignment at `0x10fb106`. For this profile, virtual `+0x1288` is `moFeature_c::setOwner`, so the branch installs the loaded ordinary `moPart_c`. The pinned native class hierarchy confirms that the part derives through `moModel_c` and `moFiledConcept_c`, while the extrusion derives through `moBodyFeature_c`. A profile using the part-owner fallback therefore passes the status-4 visibility predicate despite the separate extrusion child-list link. [Ordinary resolved load route](Resolved/EndMap.md#native-ownership)

The reopen path establishes the part-owner fallback and the distinct extrusion attachment. The archives do not carry a live `+0x290` or `+0x10c` sample during initial authoring or sidecar save. The next section traces the native authoring transition to initial Boss adoption.

## First authoring and the first sidecar save

The capture's initial P03 path leaves sketch editing via `ISketchManager::InsertSketch(true)`, selects the whole `RectangleSketch` feature and calls `IFeatureManager::FeatureExtrusion2`. It names the Boss and binds its driving dimension, rebuilds the model, sets the display view, measures and calls `IModelDocExtension::SaveAs`. The licensed baseline A receipt and the YZ and reverse reauthors exercise that sequence. The automation makes no explicit profile visibility call. [Capture lifecycle](../../automation/PairedCaptures/SolidWorksAuthoring/SolidWorksCapture.cs)

The installed interop metadata and native primary COM dispatch tables identify `ISketchManager::InsertSketch` as slot 33, DispId 25, at `sldapiu` RVA `0xaca160`. Its helper calls `slduiu!uiModelDoc_c::OnInsertSketch2` at `0xad2475`, which calls `insertSketch` at `0xe1ed3c` on its ordinary branch. The exact `IFeatureManager::FeatureExtrusion2` slot 110, DispId 101, is `sldapiu` RVA `0x852dd0`. It enters helper `0x8530c0` and calls `slduiu!auModelDoc_c::iApiFeatureExtrusion4` at `0x8532d6`. The normal command path loads `uiExtrusionCmd_c` from `sldbasegeomu` at `slduiu` RVA `0x3b39f5` and runs it at `0x3b3ccb`. This trace uses the feature-manager entry exercised by the capture.

The command's preparation code in `sldbasegeomu` at `0xf5a10` gets the chosen sketch profile at `0xf5d5e` and passes it to the created `moExtrusion_c` through virtual `+0x1d30` at `0xf6206`. The extrusion allocation at `0xf655a` calls the typed constructor. The primary extrusion vtable resolves `+0x1d30` to `sldmodu` RVA `0x991ea0`. That wrapper calls the extrusion's `+0xfb8` implementation, `moConcept_c::addFeature` at `0xc652e0`. On insertion, `0xc65381` calls the profile's `setOwner` with the extrusion as owner. The captured Boss child reference aliases the earlier `RectangleSketch`, so this is the native adoption path for the same profile. This establishes the owner at insertion. The subsequent owner through command completion, rebuild and first save remains unobserved.

The recorded `SaveAs` entry uses `IModelDocExtension` slot 102, DispId 93, at `sldapiu` RVA `0x945530`. Its native helper calls `uiModelDoc_c::iFileSaveAs` at `0x962663`. The sidecar save wrapper at `sldvisualstateu` RVA `0x81550` queries the existing per-context state at `0x81584` through the map lookup at `0x91480`. When it finds a state it calls `0x81330` at `0x81594`. That routine writes the already-held state pointer at `0x814de`. The native builder separately calls the per-feature attribute classifier dispatcher at `0x7eb85` and its live descriptor at `0x931ee`. Therefore the first sidecar's stored visibility can come from an earlier classifier invocation.

Three source-supported explanations remain for first-save visibility 1. Reassignment after Boss adoption could supply a null owner or an owner outside the excluded body-feature and reference-surface classes while the live status remains 4. `uoSelFeature_c::unblankProfiles` can temporarily set live status 2 with a saved status 4, through the guarded selection path at `slduiu` RVA `0x1230fc1`. The sidecar writer can also persist an attribute produced from the pre-adoption graph. The first save establishes the stored values of 4 and 1. It leaves the source of the written attribute unresolved. A discriminating observation would follow the same profile identity through the owner setter and status save/restore, record its owner class and three status fields at the classifier call, and check whether that attribute is the one later written at `0x40e48`.

The added native entry points use the installed `sldapiu.dll` SHA-256 `0b49965b538d26d5b6520e9b73453181917e07557c41352687b4a4606c0ed5ca` and `sldbasegeomu.dll` SHA-256 `5e81100df31986dd1a06667c769804f22c0d97fa53e724ba98a8ca664d286158`. The installed `SolidWorks.Interop.sldworks.dll` metadata SHA-256 is `423c0fd109006a13700a7b4703b56200ccde38552c96c327af371921408d7477`. [Other native module pins](VisualStateOwners.md#evidence-pins)

## Holder appearance and its allocation

The standalone holder path at `0x932d0` obtains the configuration's cached visual property at `0x9346c` and can fall back to `moConcept_c::getVizPropDirectNonConst` at `0x9347d`. A material branch checks `cachedVizProp_c::applyDefaultPWMaterial` at `0x93587`. The latter is a getter for cache policy byte `+0x69` in `sldmodu`. When default material preparation is needed, helper `0x96650` reuses existing RealView properties or calls `CreateAppearanceVizPropFromVizProp` at `0x96724`. The visual-properties attribute constructor can obtain the holder's visual property through its native virtual `+0x1040` at `0x4a088`, copy it at `0x4a0e9` and install that pointer at object `+0x10`.

These paths establish the live holder property and a conditional source for its default material. The observed sidecar property ID 3, CMgr IDs 4 or 5 and final manager counters 5 or 6 still leave the preceding allocation calls unobserved. A fresh writer needs a proven allocation sequence from the authored document's material lifecycle before assigning the sidecar property identity. The saved profile blank status and reopened owner fallback are independently available. The live owner and override state before the initial sidecar save remain unobserved, as does the initial appearance allocation sequence. [Appearance allocator and capture IDs](VisualStateOwners.md#appearance-identity-and-locator)
