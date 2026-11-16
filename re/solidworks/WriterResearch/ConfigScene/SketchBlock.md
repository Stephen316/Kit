# Ordinary Config-0 sketch block manager

`WriteSketchBlock` constructs the empty ordinary generation-19000 sketch block manager with the existing part archive allocator and inherited feature codec. Its caller supplies a coherent feature FILETIME and a fresh manager UUID. The writer requires the prior standard-view and feature-color classes, allocates the `moSketchBlockMgr_c` definition and object once, and writes its settings alias to that exact object. It emits the two empty block collections. [Research constructor](SketchBlock.py) · [Packaged manager reader](../../../../src/convert/adapters/solidworks/Config/Scene.py)

## Native ownership

The SOLIDWORKS 34.4.1.1011 `sldmodu.dll` has SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`. The `moSketchBlockMgr_c` primary slot-5 serializer at `0x4c908d90` calls the inherited `moFeature` serializer at `0x4c908db7`. The binary branch writes the exact 16-byte GUID member `+0x380` at `0x4c908e96`. The reader copies those 16 bytes back at `0x4c908eab`. The runtime/load constructor initializes the member from `GUID_NULL` at `0x4c924663–0x4c92466a`. The owner-aware model constructor creates a fresh GUID at `0x4c924b53` with `CoCreateGuid`.

The persistent settings constructor called at `0x4c924b2d` stores the parent manager at `0x4c9244be` and clears mode `+0x18` at `0x4c9244b4`. The manager reaches the associated settings at `0x4c908f0e–0x4c908f19`. Their serializer writes the signed mode at `0x4c905e76` and the exact back-reference from member `+0x30` at `0x4c905eea`. It writes unsigned collection counts at `0x4c905f49` and `0x4c9060d9`. Both are zero for an empty manager. The archived UUID happens to be the same in all fourteen controls. The fresh constructor supplies the model identity independently of those observed bytes.

## Independent archive controls

Read-only replay checked all six P01 and eight P03 discovery receipts, independently hashed the native files and measurement receipts, and reached the real typed interval after the standard views. Every manager occupies 199 bytes. The inherited feature at relative `+58..169` passes the existing `ReadCmgrFeature` guard in all fourteen controls. It carries the initial update stamp 101 and separate feature FILETIME words. The following UUID occupies `+169..185`, signed mode occupies `+185..189`, the self alias occupies `+189..191`, and two empty collection counts reach `+199`.

The view path enters the manager at next map 94 on P01 and 98 on P03. The manager consumes two slots, and the ordinary annotation list then ends at next map 99 or 104 respectively. P01 has one selected principal view. P03 has that view plus a second `*Top` occurrence. The hosted verifier compares the entire manager with the archived span, then passes an independent UUID through the same writer and rereads its manager and the preserved, independently bounded annotation list using the packaged reader. [Hosted replay](../VerifySketchBlock.py) · [Archive integration](../../../../tests/Research/Archives/SolidWorksWriterStreamTests.py)

The following annotation views remain separate authoring work. The native `moAnnotationView_c` slot-5 serializer starts at `0x4c214900`, calls the inline view base at `0x4c214939`, and has optional reference branches after that inherited record. Whole-file licensed acceptance remains pending.
