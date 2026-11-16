<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A12 empty OLE and custom-property streams

The generation-19000 writer accepts a caller-owned empty OLE inventory and
empty file and cut-list property state for an ordinary standalone part.
It emits three complete expanded members. The OLE selections have separate
counts. The custom-property inventory also carries the saved container key
and the absence of weldment and representation linkage.
[OLE writer](../../../../../../re/solidworks/WriterResearch/PartOle.py)
[Property writer](../../../../../../re/solidworks/WriterResearch/PartProperties.py)

## Native write ownership

| Expanded member | Native save path in SOLIDWORKS 34.4.1.1011 |
| --- | --- |
| `Contents/OleItems` | `SolidStorageBase_c::SaveOleItems` selects eligible embedded items at `doccplu+0x42936..0x429b3`. The call at `+0x429bf` writes the unsigned 32-bit count. The second traversal writes the selected records and has no records to visit for an empty inventory. |
| `OleItemInformation/OLE_Item_Data` | `SolidStorageBase_c::SaveOleItemsImage` builds its own selection vector at `doccplu+0x449a0..0x44a67`. The stream opens at `+0x44acc`, and the call at `+0x44b24` writes the unsigned 32-bit count. The loop is skipped when the vector is empty. |
| `Contents/CusProps` | `SolidStorage_c::SaveAllCustomProperties` opens the member and writes a `moCusPropMgr_c` at `doccplu+0x2e1a9`. Its serializer at `sldmodu+0x161e10` writes the manager sentinel, property architecture state and keyed container count. The constructor at `+0x1eaf80` initializes the sentinel to −1. `iConvertLegacyCusPropsToNewArch` sets the architecture word to 1 at `+0x1f5032`, and `isCPReArchEnabled` tests the same field. |

`doccplu.dll` has SHA-256
`120e1d5c359f5895d9785325995ebfaafc790ef7d74fe4fb0e242303f933939b`.
`sldmodu.dll` has SHA-256
`2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`.
The property manager has one keyed entry in the pinned scope. Its
`moCusPropContainer_c` serializer at `sldmodu+0x1614e0` stores the file,
cut-list and optional weldment objects, followed by the zero from its
constructor at `+0x1eade0`. The file serializer at `+0x1612e0` sends two
null `suObList` pointers through the installed archive operator. The
cut-list serializer at `+0x1627b0` stores each map count as a signed
32-bit word. The null weldment pointer allocates no index. The
manager's final byte is the flag read by
`getCopyAndLinkPropsToReps` at `+0x1630c0`.

Each of the eight receipt-pinned P03 files has the same 138-byte
custom-property payload. Its SHA-256 is
`9fd3dc57a5b385acbbd4b0f36fffec581481014616bb254a4f417f3537c1f036`.
The read-only archive walk binds four class and object pairs and ends at
byte 138 with next index 9. Both four-byte OLE payloads have SHA-256
`df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119`.
The hosted proof compares all three complete typed outputs with each
source member. [Verification](../../../../../../re/solidworks/WriterResearch/VerifyPartSidecars.py)
[P03 receipt](../../../../../../re/automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)

## Package manifests

The ordinary standalone part emits two XML package manifests from its property inventory. Content types declare the relationship and extended-properties defaults plus exact overrides for the core and custom property parts. The relationship table links the actual `docProps/app.xml`, `docProps/core.xml` and `docProps/custom.xml` members in the saved order. The serializer constructs each element and attribute independently using the standard XML writer. The native package framing uses two declaration forms, with CRLF boundaries and no whitespace between elements. [Manifest writer](../../../../../../re/solidworks/WriterResearch/PartManifests.py)

All six P01 and eight P03 receipt-pinned archives matched both generated streams byte-for-byte. The type manifest is 556 bytes with SHA-256 `a50ae48af011114c4a400111c09ca34e083c21db7e82a2f3e3c641c752b89f4d`. The 597-byte relationship manifest SHA-256 is `8fae89749a8d95ff5996361cf8f7dedb7c74a374c6ed87285d3d8c9e5a48717b`. All 42 individual missing-target controls were refused. The aggregate replay SHA-256 is `c01ca63bd2fc5c306aaf072423da0aeb0c4209fdd2636abf19603e3a02399b27`. [Receipt-pinned replay](../../../../../../re/solidworks/WriterResearch/VerifyPartManifests.py)

## Application, core and open-time property XML

The writer builds the nine application fields from supplied values, with the observed lexical value of `AppVersion` independent of the licensed SOLIDWORKS build. Core properties encode the caller's modifier and two whole-second UTC timestamps. Open-time fields retain their counters, sentinel values and optional display time. The modifier uses the saved Dublin Core elements namespace. Open-time child elements explicitly reset the outer vendor namespace. All text is escaped by the standard XML writer. [Property writer](../../../../../../re/solidworks/WriterResearch/PartSimpleProperties.py)

The 14 pinned P01/P03 controls matched all 42 generated documents byte-for-byte. They cover one app payload, eleven core timestamp combinations and three open-time payloads. The previous two-manifest digest also reproduced after sharing the XML serializer. The three-property replay SHA-256 is `06c9388493935704c0d19a9f9b87a5609301c9036052ede981bc2cff8a6824c4`. The report retains hashes and counts. [Receipt-pinned replay](../../../../../../re/solidworks/WriterResearch/VerifySimpleProperties.py)

## Retained P03 members

The licensed omission run kept 33 of the original 37 physical members
while opening, rebuilding, editing, saving and reopening the part. Its
four omissions were the physical partition, lightweight graphics,
display lists and ghost partition. The same 33 names are present in all
eight P03 captures when those four are excluded. The table records
constructive coverage of that retained roster. Separate evidence would
be needed to omit another member. [Licensed omission measurements](../SolidWorksArchiveOmissions.md)

| Coverage | Retained members | Constructive source or missing dependency |
| --- | --- | --- |
| Full typed payload | `Contents/CMgr`, `Contents/CMgrHdr2` | `CmgrComposition.BuildCmgr`, `CmgrIndex.EncodeCmgrIndex` |
| Full typed payload | `Contents/CnfgObjs`, `ModelStamps`, `_DL_VERSION_19000/DLUpdateStamp` | `PartBookkeeping.metadata_streams` |
| Full typed payload | `Contents/Definition` | `DefinitionStream.EncodeModernPartDefinition` |
| Full typed payload | `Contents/Config-0-ModelHeader`, `Header2` | `HeaderTail.WriteModelHdr`, with explicit source-owned time, feature IDs and saved state |
| Full typed payload | `Contents/CusProps`, `Contents/OleItems`, `OleItemInformation/OLE_Item_Data` | `PartProperties.EncodePartProperties`, `PartOle.EncodePartOle` |
| Fresh-document payload | `_MO_VERSION_19000/History`, `_MO_VERSION_19000/Biography` | `PartFraming.EncodeVersionStreams`, which creates fresh state from absence of prior saved history |
| Partial content | `Contents/Config-0`, `Contents/Config-0-ResolvedFeatures` | `ConfigResolvedFraming` derives the framing and shared allocation. Both bodies need end-to-end authoring composition. |
| Open | `Contents/3DExperienceExchange2`, `Contents/3DExperienceExchange_ConfigHeader`, `Contents/PMISemanticDataDB` | Database stream constructors or licensed omission evidence |
| Open | `Contents/eModelLic` | Scoped native save-context semantics and a justified caller input |
| Open | `Preview`, `PreviewPNG` | Native preview encoding from generated content or licensed omission evidence |
| Open | `SwDocContentMgr/SwDocContentMgrInfo`, `ThirdPtyStore/VisualStates` | Content manager and visualization state constructors or licensed omission evidence |
| Full typed payload | `[Content_Types].xml`, `_rels/.rels` | `PartManifests.EncodeManifests` binds the actual app, core and custom property targets |
| Full typed payload | `docProps/OpenTime.xml`, `docProps/app.xml`, `docProps/core.xml` | `PartSimpleProperties` constructs caller-owned property values in the exact namespaces |
| Open | `docProps/Config-0-Properties.xml`, `docProps/ISolidWorksInformation.xml`, `docProps/custom.xml` | Typed property-section owners and serialization |
| Open | `swXmlContents/Features`, `swXmlContents/KeyWords` | XML derived from authored feature and document metadata or licensed omission evidence |

There are 18 retained members with standalone constructors, including two
fresh-document payloads. Two are partially composed and 13 lack a
constructive owner. Native acceptance of a fully generated archive is pending.
