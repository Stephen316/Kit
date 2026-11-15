# P04 archive loader continuation

The SOLIDWORKS `34.4.1.1011` loader copies the archive map from the configuration read into the resolved-feature read. A guarded offline walk of all eleven P04 `_MO_VERSION_19000` captures reaches the unit component. Its first child needs object slot 2, whose incoming identity and allocation history remain unproved for P04. The [sketch ownership evidence](P04SketchResidence.md) records the independent cross-stream references and geometry inventory.

## Inputs

The capture files are pinned at Git revision `466dcb172dfa3803463e07ccde963ba01671d200`. Each native file matched its SHA-256 in the committed receipt, whose own SHA-256 is `7fd2fffa3c690998753a80cab81da2f1c2446c9fcec39574e3983a7f4345cae5`. The walker source checkpoint was `dcfb17f495d2bc441d5eb36cdbd13ea443ba8e22`. The analysis used captured streams and offline disassembly of the matching installed build. [Capture receipt](../../automation/PairedCaptures/P04/solidworks-c1986308375a/receipt.json)

| Installed PE | SHA-256 |
| --- | --- |
| `sldmfcu.dll` | `bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6` |
| `sldmodu.dll` | `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99` |
| `swccu.dll` | `7254b30f4eb77fd5b49fdbb0a7ab499ba3bf1d39a3f8f18d72090c2568967b49` |
| `doccplu.dll` | `120e1d5c359f5895d9785325995ebfaafc790ef7d74fe4fb0e242303f933939b` |

## Map handoff in the loader

| Location in the matching build | Observed archive operation |
| --- | --- |
| `doccplu!SolidStorage_c::iLoadModelDefn` at RVA `0x3c6a0`, call at `0x3d8d8` | Invokes `useCacheArchive_c` with state 2 to cache the active load map. |
| `sldmodu!moModel_c::loadResolvedFeatures` at RVA `0x448760`, call at `0x4489bc` | Invokes the cache constructor with state 1 before reading the integer header and first object list. |
| `sldmodu!useCacheArchive_c` constructor at RVA `0xece740`, calls at `0xece7ef` and `0xece899` | Calls `su_CArchive::copyLoadArrayStoreMapFrom` into and out of the model's cache, respectively. |
| `swccu!su_CArchive::copyLoadArrayStoreMapFrom` at RVA `0x9210` | The load branch at `0x92ed` copies the pointer array at archive +0x58. The write at `0x942c` copies the counter at +0x50. |

The matching loader confirms continuation of the class and object index space, including the counter. Historical runtime traces show the resulting external references in resolved streams. The current offline `SegmentWalkMut` initializes fresh maps per call and can use the declared slot type to describe an absent object. A strict cross-stream walk needs the observed allocation state carried into the resolved read. [Historical external references](../archive/ExternalClasses.md), [offline walker](../../../src/convert/adapters/solidworks/container/Archive.py)

## Guarded walk of Config-0

With a trial base of 2 and zero header bytes, the merged, decompiled and versioned layout tables stop on the missing `moPart_c` layout at byte 0. Starting at byte 26 with base 4 stops on the missing `moNodeName_c` layout. The scratch probe checks MO 19000 inside the schema-1 root lead, consumes its 12-byte body, reads the node-name CString, then consumes the node tail with the flag `0x40000000` at tail +4, CString at tail +16 and final dword. These steps establish the physical prefix using the trial map. [Configuration prologue](ConfigZero.md#1-the-prologue-and-base-4)

`sldmfcu!moVisualProperties_c::Serialize` at RVA `0x200ca0` reads three dwords and inlines `uoMaterialProperties::restore` at `0x131160`. Its exercised path reads two framed CStrings and six doubles, with both texture flags clear, RV appearance present and zero custom properties. The inline RV loader at `0x1776a0` reads fixed-width scalars and four CStrings. The obsolete version interval `0x3348..0x46b9` is skipped. The outer serializer reads the present DSPBR flag at `0x200fbe` and calls the inline loader at `0x59620`. Both DSPBR gates `0x46b5` and `0x4972` are active. The DSPBR body reads 58 four-byte fields and 12 CStrings. These exercised visual branches perform no archive object allocations. Framed strings and primitive widths account for the full 817-byte visual body on each capture.

`sldmfcu!moUnitsTable_c::Serialize` at RVA `0x1cb980` uses the `swccu` array reader at `0xd0c0`. Its `ReadCount` at `0x6ad0` reads a u16, with a u32 count after sentinel `0xffff`. Each P04 file uses the short form with 16 direct elements. The common scalar unit body is 62 bytes. The length-unit serializer at `0x1ecb30` adds a u16 and reads a nested unit object. The density serializer at `0x1ec8c0` has a zero optional-child flag at body +66 and consumes 73 bytes on that path. The angle, force and unit-system exports share the serializer at `0x1ec860`, which appends two bytes to the scalar body. [Unit layout inventory](ConfigZero.md#71-the-17-unit-records)

The scratch walk reaches 23 archive rows in each capture, including the `moUnitComponent_c` definition. The offsets below are zero-based in the decompressed stream. Each first-child token is `02 00`.

| P04 capture group | Visual definition | Units definition | Unit component definition | Unit component first child |
| --- | ---: | ---: | ---: | ---: |
| Baseline A | 84 | 927 | 2,414 | 2,437 |
| Baseline B, six parameter edits and inch display | 122 | 965 | 2,452 | 2,475 |
| YZ and through-all | 82 | 925 | 2,412 | 2,435 |

## Incoming object slot 2

The unit-component vtable slot 5 leads from `sldmodu` RVA `0x10e9990` to `moComponent_c::Serialize` at `0x10da2c0`. Its call at `0x10da5f1` goes to the generic archive object-pointer reader. The `swccu` reader at RVA `0xa56c` indexes the load array at `0xa5ae`, so the observed token is a reference to actual object slot 2. The trial root walk had allocated slot 2 to a class and therefore stops at this reference. Independent historical baseline, Cutbase and vendor-ring traces identify the document as the target of this component child. [External document references](../archive/ExternalClasses.md)

The matching model-definition loader has an existing-model branch that consumes a root class through `ReadClass` at `0x3ce97` and invokes the existing object's vtable at `0x3ceb4` and `0x3cece`. Its other branch reads a typed `moPart_c` pointer. The branch taken for the P04 configuration stream and the initial slot 2 state still need an independent observation. Both determine how the first root and node-name records affect the map. The trial indices are provisional, including class and object indices 43 and 44 at the unit-component definition.

## Reproduce and extend

1. Verify the eleven Git blobs against the pinned receipt. Extract `Contents/Config-0` and `Contents/Config-0-ResolvedFeatures` using `SldprtArchive.from_bytes`. The scratch inventory `P04OwnershipTrace.py` exported these as separate `P04Trace.*.Config-0.bin` and `P04Trace.*.Config-0-ResolvedFeatures.bin` files. Baseline A's configuration stream is 42,879 bytes and has SHA-256 `e40cdd1e562a9e501a0a29ac252745d5c5cac6a7265ef924ccef4f5d078b34ab`. [Container reader](../../../src/convert/adapters/solidworks/container/Container.py)
2. Verify the installed PE hashes and inspect the listed RVAs with an offline x86-64 disassembler. The scratch `DisasmPE.py` used Capstone 5.0.6 and the repository's PE export inventory. Follow the exercised serializer branches and record scalar widths, each CString boundary and every archive object read. [PE export inventory](../../tooling/ghidra/Exports.py)
3. Apply the guarded prefix, visual and unit layouts to a scratch copy of the merged table and walk the verified configuration streams using `Archive.Segment`. The scratch `P04ArchiveWalk.py` reproduces the physical stop at the unit-component child in the table above. The resolved profile scan is a separate probe of the sketch child slot with its own input stream. A full join also needs the exact layout continuation past that slot. [Merged layout table](../../data/Layouts/ClassLayouts.json)
4. Capture the missing seed in a licensed runtime using the existing debugger trace setup. Match the active decompressed input buffer to baseline A's size and digest, then observe the selected class-only or typed-pointer root load. Before and after the first class read and node-name record, record the load-map counter at +0x50, slots 0–4 in the array at +0x58, each entry's runtime type and the active model pointer. Follow `MapObject` to distinguish an incoming entry from an allocation made while reading the root. At the unit-component child, check whether the lookup of slot 2 yields the same model object. Confirm on a repeat or YZ input before using that seed to mirror the cache handoff and follow both sketch allocations. [Existing debugger commands](../../tooling/windbg/Commands/Traces/CdbTraceBaseline.txt), [trace method](../archive/Segmentation.md#2-the-productive-trace-and-the-segmentation)
