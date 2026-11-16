# Blind boss feature handle and dimension boundary

All eight generation-19000 [P03 SOLIDWORKS captures](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json) have the same 133-byte `moFeatureDimHandle_c` span with SHA-256 `13282cefe47002dea925f0081a4341fb4210ab2c373696857a4d09095efce523`. The [production typed path](../../../src/convert/adapters/solidworks/Resolved/BossDepth.py) reaches it from the one-handle count after [inline display text](DisplayStyle.md#first-feature-handle-and-owned-dimension). Receipt file sizes and digests and the independent native measurement digest were checked before reading each archive. The native addresses below refer to SOLIDWORKS 34.4.1.1011 and the pinned modules identified in the [display style evidence](DisplayStyle.md).

## Empty component reference

The handle starts with a 26-byte compact schema-1 archive definition. Its serializer calls `0x4c828570` at `0x4c832432`. That reference serializer calls `moCompRef_c::Serialize` at `0x4bba6160`, using the regular archive object pointer for member `+0x58`. The no-argument `moCompRef_c` constructor at `0x4b7e7a80` clears that pointer at `0x4b7e7ac6`. The following offsets are relative to the handle definition.

| Handle offset | Component fields | Plain wire type and saved values | Store addresses |
| ---: | --- | --- | --- |
| 26 | `+0x58` component | null object | `0x4bba62fe` on the direct component branch |
| 28 | `+0x68` | `i32` 0 | `0x4bba6340` |
| 32 | `+0x18`, `+0x1c` | `2 i32` 0, 0 | `0x4bba6382`, `0x4bba638e` on the ordinary fields branch |
| 40 | `+0x20`, `+0x30`, `+0x70` | `3 i32` 0, 0, 0 | `0x4bba639a`, `0x4bba63a6`, `0x4bba63b2` |
| 52 | `+0x84` optional record presence | `i32` 0 | `0x4bba63c4`, after the store itself clears the member |
| 56 | `+0xa0`, `+0x34`, `+0x48` | `i32 u32 i32` 0, 0, 0 | `0x4bba642c`, `0x4bba6438`, `0x4bba6444` |
| 68 | `+0x90`, `+0x94`, `+0x98`, `+0x9c` | `4 i32` all -1 | loop at `0x4bba6466` |
| 84 | `+0xb0`, `+0xb8`, `+0xc0`, `+0xc8`, `+0xd0` child presence | `5 i32` all 0 | `0x4bba6489`, `0x4bba64b6`, `0x4bba64e1`, `0x4bba650c`, `0x4bba653b` |
| 104 | `+0x4c` creation generation | `u32` 19000 | `0x4bba6586` when archive generation is at least `0x3ef6` |

The handle initializer at `0x4c839f80` calls the base constructor at `0x4c839f9a`. The base clears the component scalars and optional fields, installs the four -1 values with two qword stores at `0x4b7e7b32` and `0x4b7e7b3d`, and stores the current native file version into `+0x4c` at `0x4b7e7b81`. The `+0xc8` member is initialized null at `0x4b7e7b16`. Its nonempty store would call `mgXform_c::save` at `0x4bba6521`. Every pinned handle stores only the zero presence word, with no basis, translation or scale payload. The `0x2000` archive condition can separately force the pair at offsets 32 and 36 to zero. These saved words cannot distinguish that route from the zero constructor defaults.

## Reference fields and dimension ownership

The reference serializer resumes at offset 108. The handle initializer clears transform slots `+0x120` and `+0x128`, view slots `+0x130` through `+0x148`, reference slots `+0xe8` and `+0x100`, route byte `+0x150`, and flags `+0x118`. It sets the signed route value `+0x154` to -1.

| Handle offset | Reference field | Plain wire type and saved value | Store address |
| ---: | --- | --- | --- |
| 108 | first transform presence `+0x120` | `u16` 0 | `0x4c8285d0` |
| 110 | view objects `+0x130`, `+0x138`, `+0x140`, `+0x148` | four compact nulls | `0x4c828636`, `0x4c828645`, `0x4c828654`, `0x4c828663` on the typed view route |
| 118 | `+0x150` | `u8` 0 | `0x4c8286cd` |
| 119 | `+0xe8` geometric feature reference | null object | `0x4c8286f3` |
| 121 | `+0x100` optional reference | null object | `0x4c828702` |
| 123 | `+0x154` | `i32` -1 | `0x4c828788` |
| 127 | second transform presence `+0x128` | `u16` 0 | `0x4c82882e` |
| 129 | `+0x118` | `i32` 0 | `0x4c828f64` |

The view helper at `0x4c8262f0` writes `moDrViewTag_c` objects. An alternate archive-condition branch emits four literal null objects at `0x4c82866f` through `0x4c828690`. The empty branch has identical bytes and leaves condition selection unresolved by those four tags. The null at offset 121 skips the associated transform and optional name at `0x4c828714` through `0x4c82874c`. An archive-condition or drawing route that writes more fields needs its own evidence. These observations cover the plain part handle with absent component, views, references and transforms.

At offset 133 the feature serializer's object store at `0x4c832545` writes the value from `+0xf0`. The native initializer at `0x4c839fb3` puts the supplied owned dimension there. The eight saved files allocate the handle definition as class 297 and object 298, then allocate the 32-byte `ParallelPlaneDistanceDim_c` definition as class 299 and object 300. Its `Dimension_c` base begins immediately after that definition. The first signed scalar is 2 in all eight captures. The [depth parameter fragment](BlindDepth.md) starts at dimension offset +36 with `moLengthParameter_c` class reference 200 and allocates object 301. The name child uses existing `moNodeName_c` class 4 and allocates object 302. The base native dimension ID is 29 and the observed next index after these allocations is 303. A new archive must derive both class references and the dimension identity from its own enclosing state. The reopened API receipt binds `BlindBoss` and `depth_mm` to the same positive magnitude stored by the parameter and both display copies. Seven saves are 0.010 metres, and `edit-depth_mm-12` is 0.012 metres. The negative-direction save has the same positive parameter and a separately reversed model direction.

## Where the owned dimension ends

The `ParallelPlaneDistanceDim_c` archive slot 5 at `0x4c831c60` calls the base dimension store at `0x4c827320`. On the witnessed path the first three points start at dimension offset +114 and are written at `0x4c831cbd`, `0x4c831ccd` and `0x4c831cdd`. The vector pair selector is `u16` 1 at +186 and precedes the vectors written at `0x4c831d0f` and `0x4c831d1f`. The pose selector is `u16` 1 at +236 and the 106-byte pose starts at +238. The plain `mgXform_c::save` path writes a one-byte basis flag, nine ordered basis doubles, three translation doubles, the scale double, and a masked status byte. The basis and scale store calls are `0x31e13d56` and `0x31e13d6f` in the pinned `sldmgu.dll`. All eight records carry explicit basis `(1, 0, 0, 0, 0, 1, 0, -1, 0)`, scale 1.0 and no nested payload. Baseline pose translation is `(-0.04, 0, -0.02)` metres. The width and height edits change the corresponding translation components, and the YZ file stores `(0, 0, 0)`. Scale 1.0 occurs in the present pose with real saved controls. The handle's absent transforms spend only presence fields.

| Saved control | First two dimension points in metres | First vector | Pose translation in metres |
| --- | --- | --- | --- |
| Baselines and inch units | `(0.04, 0.02, 0)` and `(0.04, 0.02, 0.01)` | `(0, 0, 1)` | `(-0.04, 0, -0.02)` |
| Width 41 mm | `(0.041, 0.02, 0)` and `(0.041, 0.02, 0.01)` | `(0, 0, 1)` | `(-0.041, 0, -0.02)` |
| Height 23 mm | `(0.04, 0.023, 0)` and `(0.04, 0.023, 0.01)` | `(0, 0, 1)` | `(-0.04, 0, -0.023)` |
| Depth 12 mm | `(0.04, 0.02, 0)` and `(0.04, 0.02, 0.012)` | `(0, 0, 1)` | `(-0.04, 0, -0.02)` |
| YZ plane | `(0, 0, 0)` and `(0.01, 0, 0)` | `(1, 0, 0)` | `(0, 0, 0)` |
| Negative direction | `(0.04, 0.02, 0)` and `(0.04, 0.02, -0.01)` | `(-0, -0, -1)` | `(-0.04, 0, -0.02)` |

The third point is zero throughout. The second vector is `(1, 0, 0)` except in YZ, where it is `(0, 0, 1)`. The native child writes the terminal `u16` at +344 via `0x4c831e66`. The two low bits indicate optional following points from `+0x98` and `+0xb8`. Both bits are clear in all eight saves, so the child ends at **+346**. In `Contents/Config-0-ResolvedFeatures` the end offsets are 14130 for baseline A, 14358 for baseline B and each dimensional edit or inch save, 14200 for YZ, and 14128 for reversed direction.

The next three ushorts belong to the enclosing `moDisplayDim_c` store, with `ArrowHead0`, `ArrowHead1` and `Position` at `0x4c82a455`, `0x4c82a4ad` and `0x4c82a505`. Its four subsequent empty CStrings occupy the prefix, suffix and two callout positions. The production read bundles these display fields and additional placement into `ReadParDepthMut`, which returns at +586. The 240-byte span belongs to the outer display owner. The scoped research encoder takes explicit annotation and document settings. Native selection beyond the normal blind route and the closing favorite remain open. [Enclosing placement](DisplayTail.md)

## Constructing the ordinary owned distance

The [research constructor](BlindDimension.py) uses the first schema-1 `ParallelPlaneDistanceDim_c` route at generation 19000. The ordinary extrusion constructor selects the runtime distance class at `0x4bad2e68` and `0x4bad2eb3`. Native initialization at `0x4c81ea90` allocates its length parameter through slot `+0x3d8` at `0x4c81f210`. The caller supplies the authored positive length in millimetres and its name. The shared length emitter uses the enclosing class map, and the distance class definition and its two already-defined children consume four archive slots in total.

The base dimension constructor at `0x4c81d430` initializes the reference count at `+0x20` to zero. The dimension virtual slot `+0x1d0` increments it at `0x4c81e340`. Handle ownership calls that slot at `0x4c83a081`. The serializer writes the signed `RefCount` at `0x4c8273bb`. All eight captures store 2, and the second runtime retain site remains unresolved. The research writer therefore requires the enclosing caller to supply the witnessed value. The caller also assigns the model dimension ID, stored as `amObjectID` at `0x4c8274d5`. Runtime retains, dimension ID and archive indices are distinct inputs or allocations.

After the parameter, the base writer emits the supported empty branch. It writes a null tolerance at `0x4c82749c`, then the caller's ID and the signed words for members `+0x30`, `+0x54` and `+0x5c` at `0x4c827524`, `0x4c827573` and `0x4c827595`. Those words are zero. The null attachment at `0x4c8275cf`, zero driven state at `0x4c82761f` and clear alternate-name presence at `0x4c8276e6` follow.

The extrusion regeneration path sets the two measured points at `0x4baf50ce` and `0x4baf50e4`, passes the direction and tangent to the handle at `0x4baf5103` and `0x4baf5121`, constructs its reference frame with `mg_CoordinateXform` at `0x4baf54e4`, inverts it at `0x4baf55ad` and installs the result at `0x4baf55e6`. The research caller provides the selected reference anchor, local-to-model axes, unsigned extrusion normal, profile tangent and reversal. The second point is the anchor plus the signed depth along the unit normal. The stored direction is signed and the model depth parameter stays positive. The inverse translation is the negative dot product of the anchor with each forward axis. The native save writes nine consecutive basis doubles at `0x31e139e0`. Its point application at `0x31f198be` through `0x31f19915` takes a column for each output coordinate, so the inverse maps into native row-vector order. The constructor restricts this path to the explicit matrix and unit-scale branch.

The independent reopened measurement rows supply the rectangle vertices, first profile edge, principal support, reversal and blind length for the comparison. The comparison takes the maximum measured vertex for the Front controls and the origin for YZ. These choices describe the saved reference points for the pinned controls. The tested display frame uses forward column axes `((1, 0, 0), (0, 0, -1), (0, 1, 0))` for this observed route. Read-only comparison against the production archive path matched points, both vectors, the inverse basis and translation, and positive length across all eight controls. This confirms the placement math with the supplied frame. The selection of that frame and anchor in other extrusion routes remains open.

The constructor ends at the clear optional-point mask, which is offset +346 from this class definition for the captured `depth_mm` name. Different encoded name lengths shift the byte offset without changing that field boundary. Hosted verification compares the emitted child bytes with the bounded archive span and gives the production reader the separately generated 240-byte enclosing presentation tail to check the next cursor. [Enclosing placement](DisplayTail.md)
