<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Configuration manager visual properties

The generation-18000 [configuration manager emitter](../../../src/convert/adapters/solidworks/container/Cmgr.py) includes a 104-byte compatibility record that generation 19000 omits. The record is inside the configuration's visual properties. A separate optional visual property is present in all 25 measured generation-19000 saves. It adds 300 bytes. The installed serializer and saved archives establish both changes.

## Version and ownership

The evidence uses installed SOLIDWORKS 2026 `34.4.1.1011`, `sldmfcu.dll` SHA-256 `bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6` with preferred base `0x3c730000`. The exported `moVisualProperties_c::Serialize` at `0x3c930ca0` agrees with the RTTI vtable's archive slot 5. The signed integer, unsigned integer, unsigned long, float, double and wide CString operations come from the `su_CArchive` imports. The stored integer and float primitives are little-endian.

- `getMatProps` at `0x3c75f9b0` exposes the outer object's `+0x20` member as `uoMaterialProperties`. The call at `0x3c930d19` serializes it inline at `0x3c861a60`. Its accessor `getRVAppProps` at `0x3c75f810` exposes `+0x90` as `uoRVAppearanceProperties`. The presence word at `0x3c861c29` precedes the inline call at `0x3c861c39` to `0x3c8a7d40`.
- The `uoRVAppearanceProperties` serializer writes the `+0x98` float at `0x3c8a80f0`. The following checks at `0x3c8a80ff` and `0x3c8a8113` include the compatibility record for archive versions `13128..18105` inclusive. The temporary initializer at `0x3c8a5b50` constructs three empty CStrings and zeros every serialized numeric member. The calls at `0x3c8a812f..0x3c8a827f` write the three strings, 17 floats, two unsigned integers and four signed integers, in that order. The measured generation-18000 record contains four bytes per empty wide CString and 92 numeric bytes.
- After that guarded branch the enclosing `uoMaterialProperties` writes its `+0xb8` CString at `0x3c861c52`, a presence word for `+0x98`, and the counted collection at `0x3c897c80`. The presence word and collection count are both zero in the measured forms.
- The outer `moVisualProperties_c` serializer writes the `+0x88` presence word at `0x3c930dba` for archive version `16137` or later. Exported `getDSPBRprops` at `0x3c773a00` identifies that pointer as `uoDSPBRProperties_c`. The outer default constructor clears it at `0x3c9307ef`. The observed modern saves carry a populated object.

## Saved spans

All four tested class definitions use schema 1, with `moConfigurationMgr_c`, `moPartConfiguration_c`, `moNodeName_c` and `moVisualProperties_c` starting at offsets `0`, `165`, `192` and `252` in these saves. Read the visual body as three unsigned longs followed by the material record. Advance through the typed fields and the encoded CString lengths to reach the version check. The table records the resulting offsets in these files. The writer's existing reserved byte groups combine parts of several native fields.

| Boundary | Generation 18000 | Generation 19000 |
| --- | --- | --- |
| Visual body start | 278 | 278 |
| Compatibility branch after the `+0x98` float | 743, emits through 847 | 743, omitted |
| Enclosing `+0xb8` CString | 847 | 743 |
| Inline material record returns | 859 | 755 |
| Outer DSPBR presence word | 895, zero | 791, one |
| DSPBR body | Absent | 795–1095 |
| Visual record returns | 899 | 1095 |

The optional record's store procedure at `0x3c78af90` writes 26 floats, one signed integer, 18 floats, one signed integer, two floats, five CStrings and one float. At `0x3c78b41e`, archive version `18101` or later adds two CStrings, one signed integer, six floats and two CStrings. At `0x3c78b508`, archive version `18802` or later adds two floats and three CStrings. All 25 records contain 55 floats, three integers and 12 CStrings. The only nonempty strings are `basic` and `2025x`. The 300-byte DSPBR body has SHA-256 `3b77a4c24f8a5953b871c3b9fa7b0df54008ddf61bacb11baffc7c78fba937a9` in every measured save. Its end leaves later configuration-manager members outside this proof.

## Color appearance initialization

The installed appearance conversion can construct the populated record from the saved visual properties and the installed material library. The absence branch of `moVisualProperties_c::Serialize` allocates `uoDSPBRProperties_c` with its exported default constructor at `0x3c93103e`, sets the outer pointer and calls `convertVizpropToDSPBR` at `0x3c931055`. On conversion failure it frees the new object and clears the pointer. This proves a native path for filling an absent record. The existing saves establish the selected material and saved values. Their histories leave the original population call unobserved.

- The converter obtains `uoRVAppearanceProperties::getFilename` at `0x3c785f3a` and `getRVShaderName` at `0x3c785f4d`, then passes them to `s_findP2mToDspbr` at `0x3c785f8d`. The 25 saved objects carry the leaf `color.p2m` at stream offset `513` and shader `defaultplastic` at `400`. The installed legacy material `data/graphics/Materials/color.p2m` declares that shader. Its SHA-256 is `5a1df25caf4be9b191ad6829ce1c2f7aaf1a9af6e80c5ae65c7d0ee8039f42e6`.
- The shader lookup loads `data/dspbr/shaderToDspbr.dat` through the branch at `0x3c78a865..0x3c78a8c8`. Its `defaultplastic` entry resolves to `color`. The mapped branch at `0x3c78a2b8..0x3c78a331` appends the native data root, the DSPBR directory, the mapped name and `.dspbr`, then checks the path. The converter calls exported `readDSPBRfile` at `0x3c78612a`. The shader table SHA-256 is `c2d0b4f43a9cf9e02a9fd1c16008240f2b27d8082bb756a9fd83f58a4095cd69`. The selected `data/dspbr/color.dspbr` SHA-256 is `08ae163e93f9dd806d3ec37b0f04a101a05b4a2f86aa7a43adf55ef363484632`. Its declared subtype, version, metallic and roughness match the stored `basic`, `2025x`, `0.0` and float32 `0.2`.
- Exported `getColorForm` selects mode `1` at `0x3c78619c..0x3c7861a9`. In all 25 inputs the archived color form is `1` at offset `477`. This branch calls `moVisualProperties_c::getColor` at `0x3c7861ba`, then sends the packed color to `setAlbedo` and `setAttenuationColor` at `0x3c7861c6` and `0x3c7861d0`. Both setters use `0x3c789c70` to multiply each color byte by float32 `1/255` with bits `0x3b808081`. The source color word is `0x00e4e4e4` at stream offset `278` in all 25 inputs. The resulting channel bits are `0x3f64e4e6` in both saved triples, starting at offsets `795` and `951`. The installed material file specifies albedo `0.898039` and white attenuation. These differing source values independently distinguish the conversion overrides from direct file values.

### Saved field attribution

`readDSPBRfile` initializes 52 named property descriptors from `0x3c788800` through `0x3c7894a6`. Each text key enters the first matching descriptor in the loop at `0x3c7894c1..0x3c78951d`. The call at `0x3c789501` reaches the selected callable through its vtable `+0x10` entry. Following that entry through its thunks identifies the destination member. For example, the roughness descriptor at `0x3c788951` reaches `0x3c784d10` and then `0x3c783730`, which passes member `+0x2c` to the scalar float parser. `0x3c78b013` stores that member. The [installed asset](#color-appearance-initialization) supplies 44 of the 52 recognized keys.

The following order joins those setter destinations to the store calls. RGB entries occupy three float32 values, other numeric material fields are float32, and names and textures are wide CStrings. Emission mode, emission energy normalization and the flags word are signed 32-bit fields.

| Save order | Fields |
| --- | --- |
| Common numeric prefix | Albedo, metallic, roughness, anisotropy, anisotropy rotation, transparency, cutout opacity, displacement, flip-flop, IOR, IOR-derived float, specular, specular tint, sheen roughness, sheen color, subsurface anisotropy, emission color, emission value, emission energy normalization, clearcoat, clearcoat roughness, flip-flop color, flake coverage, flake size, flake roughness, flake color, attenuation distance, attenuation color, subsurface color, flags, translucency, Abbe number. |
| Common string suffix | Albedo texture, normal, roughness texture, cutout opacity texture, material subtype, then the float32 RealView-to-DSPBR texture scale. |
| Added at version 18101 | Version, clearcoat normal, emission mode, thin film, thin-film thickness, thin-film IOR, translucency color, displacement texture, thin-film thickness texture. |
| Added at version 18802 | Normal strength, clearcoat normal strength, metallic texture, transparency texture, emission color texture. |

The nontrivial defaults and transformations have separate source evidence.

- The asset's `displacement ""` key reaches the float parser through member `+0x48`. The `%f` conversion at `0x3c78adca` consumes no value for that argument. The constructor zero at `0x3c78227e` remains in effect, matching the float at stream offset `831`.
- The asset omits the texture scale, both normal strengths, displacement texture, and the metallic, transparency, and emission color textures. The constructor at `0x3c782210` initializes the three numeric members to `1.0` at `0x3c7823b6`, `0x3c782408` and `0x3c782412`, and the four CStrings empty through the calls at `0x3c7823a1`, `0x3c7823e5`, `0x3c7823f3` and `0x3c782401`. The measured material also has no legacy texture object. Its absence bypasses the legacy texture transfer branches.
- The reader starts the flags word at zero through the constructor's write at `0x3c78232a`. The `thinWalled` setter parses the asset's `1` into the temporary at `0x3c788fd3`. The post-read calls at `0x3c789526` and `0x3c789542` assign bit 0 from that temporary and bit 1 from transparency at least `1e-8`. The asset omits `normalMap`, whose setter would update bit 2. The measured word at stream offset `975` is `1`.
- The post-reader at `0x3c789547..0x3c789572` derives member `+0x12c` by subtracting and adding one to IOR in float32, dividing in float32, squaring in float64 and narrowing to float32. The asset IOR `1.5` gives bits `0x3d23d70b` at stream offset `843`. The saved cutout opacity is also explained by the conversion branch at `0x3c7861e8..0x3c786201`, which computes `1.0` minus zero legacy transparency for this profile.

The read-only archive comparison used all 52 setter routes, the installed asset values, the explicit constructors and the three archive store blocks. It checked the 70 serialized fields independently in each of the 25 saves. All 1,750 comparisons matched, with float32 values equal bit-for-bit and both nonempty CString values preserved. This completes the observed DSPBR body mapping. Other material assets, textured appearances and application acceptance require separate evidence.

## Inputs and reproduction

Use [`capture_inputs`](../../automation/SolidworksCensusInputs.py) at capture revision `466dcb172dfa3803463e07ccde963ba01671d200`. It checks the three discovery receipts, independent reopen measurements and exact native file identities for six P01, eight P03 and eleven P04 saves. Read `Contents/CMgr` through [`SldprtArchive`](../../../src/convert/adapters/solidworks/container/Container.py), checking generation through `ContainerMo`. The old comparison is the [1,957-byte CMgr donor](../Fixtures/donors/boss1_front_rect_blind/container/Contents__CMgr.bin) in revision `1dcffae99f4bbf2a70f1c47fe24cee004b5f0ab2`, SHA-256 `3e2894581c3f5b25f523146a01e0f394d9c027f22c6a6a343000d64078fe6cd5`. Use the schema-1 visual tag, the `su_CArchive` operation sequence above and [`FieldCursor`](../../../src/convert/adapters/solidworks/container/ArchiveCursor.py) to compare the boundaries. The store calls can be inspected with `dumpbin /DISASM:NOBYTES /RANGE:<start>,<end>` against the pinned DLL. The archived values verify the sequence and cannot supply default values for an independent writer.
