# SOLIDWORKS part container bookkeeping

Native editable authoring remains open. The metadata-only container below passes Kit's archive reader and directory validation. It omits the document-level streams and has no native readiness, rebuild or edit measurement.

## Generate without a capture

```sh
python re/solidworks/authoring/PartBookkeeping.py emit /scratch/PartMetadata.container \
  --created 1750000000 --update 7 --body 0
```

The emitter uses explicit creation time, update and body counters. It reads zero captured archives or vendor payloads. The existing container codec emits format 4 with its admitted default file ID and signature triplet, builds the compressed records, and derives offsets, lengths, directory and checksums. `SldprtArchive.from_bytes` reads all three streams back. `Container` verifies matching local, central and end signatures and a central record for each local record. The output is 401 bytes with SHA-256 `60a62ec90ba384e383aa29396baf87f6fe10f81a7f35cc0c35189c211bab8881`. [Container framing and signatures](../container/README.md)

| Stream | Bytes | Exact native store rule |
| --- | ---: | --- |
| `Contents/CnfgObjs` | 12 | `doccplu+0x2fa5d` calls `moBaseConfiguration_c::SerializeConfigObjects` at `sldmodu+0xc85120`. Its call at `+0xc85283` uses the ordinary empty `suObList` count at `swccu+0x16662`. A null `moConfiguredRelationList_c` is serialized at `sldmodu+0xc86249`. The absent reference-name table branches store an empty CString at `+0xc864c4` and `+0xc8567d`. |
| `ModelStamps` | 12 | `doccplu+0x21543`, `+0x21557` and `+0x21569` store the header's creation `su_CTime`, current update stamp and current body stamp. The latter two outputs are unsigned dwords. The returned time uses the four-byte archive time operator. |
| `_DL_VERSION_19000/DLUpdateStamp` | 6 | `doccplu+0x26149` stores the supplied update stamp as a dword. Its following call at `+0x26153` writes a null `CObject` archive tag. All six controls share the same update value between this stream and `ModelStamps`. |

The store paths use the exact `34.4.1.1011` installed [loader image hashes](../records/P04ArchiveWalk.md#inputs). Nonempty configuration-object contents require separate rules. The display-list namespace is generation 19000. The shell carries no `_MO_VERSION_*` document generation marker or `Contents/Definition`, `Contents/CMgr`, `Contents/Config-0`, the model headers, or `Contents/Config-0-ResolvedFeatures`. Those absences are checked explicitly. [Historical load-critical streams](../archive/Multistream.md#4-which-streams-are-load-critical)

## Configuration dispatch

The [generation-19000 configuration index and dispatch](PartStorage/ConfigurationIndex.md) adds a typed `Contents/CMgrHdr2` reconstruction for the active standalone part and records the remaining version folder and container framing questions.

Run `python re/solidworks/authoring/PartBookkeeping.py compare` for the six pinned P01 SOLIDWORKS archives. The command verifies the named default configuration and zero bodies using the independent historical readback. It checks all 18 reconstructed metadata streams and the computed class tag, split lengths and resolved root header. Source receipts and generation are the same as the [rectangle experiment](RectangleFields.md). The compact comparison SHA-256 is `9517b7b283b054af1249f5fcdfc055b1124d18250b0ecadbaa1b934027aa8caf` before the terminal newline.

| Archive group | Root class tag | Split word offsets | Computed body lengths | Inherited next map index | Logical root count |
| --- | ---: | --- | --- | ---: | ---: |
| Baseline A | 0–14 | 14, 2,893 | 2,875 and 22,076 | 106 | 18 |
| Baseline B, width, height and inch | 0–14 | 14, 2,933 | 2,915 and 22,076 | 106 | 18 |
| YZ | 0–14 | 14, 2,893 | 2,875 and 22,148 | 106 | 18 |

The first split excludes the root class tag and its own dword. The second ends at configuration stream end and excludes its preceding dword. The resolved list begins with the completed configuration map counter and the compact root list count. The typed cabinet children stay nested. The environment alias is a root item with no new allocation. The existing resolved reader inherits the full class and object maps and accepts the six-byte reconstructed header. [Native map handoff](../records/P04ArchiveWalk.md#map-handoff-in-the-loader)

The [generation-19000 root constructor](../WriterResearch/ConfigRoot.md) now covers the semantic body from the first split word to the first visual-properties pointer. Configuration construction continues with the actual visual, material, units and presentation objects using the same archive allocator. The nonempty atom writer, model header and journal dependencies continue separately in the [portable boss research](../WriterResearch/PortableBoss.md).
