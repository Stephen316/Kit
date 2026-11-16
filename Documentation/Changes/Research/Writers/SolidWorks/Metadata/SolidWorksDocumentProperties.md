<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A12 document-property streams

The standalone generation-19000 metadata writer emits the exact three
property members used by the package manifests. It accepts the caller's
last modifier and UTC creation and save timestamps, plus the empty and
unlinked custom summary state. The app metadata comes from the pinned
application's fresh property defaults. Each XML value is serialized from
typed fields and encoded as UTF-8.
[Document property constructor](../../../../../../re/solidworks/WriterResearch/PartDocProperties.py)
[Package manifests](SolidWorksPackageMetadata.md)

## Native owners

These addresses use the preferred image base of the installed
SOLIDWORKS 34.4.1.1011 `sldmfcu.dll` with SHA-256
`bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6`.

| Member | Store evidence |
| --- | --- |
| `docProps/app.xml` | `suDocumentProperties::SaveToStorage` initializes an absent app DOM at `0x3c7da4bc` through `getXMLStringForAppProperties`. Its named elements and values are set by the initializer at `0x3c799fc0`. The grouped names and values start at `0x3cb41840`. The DOM is serialized at `0x3c7daea9`. |
| `docProps/core.xml` | `CZipStorageSummInfo::WriteToStorage` dispatches to the core DOM writer at `0x3c8d9640`. That writer sets `dc:lastModifiedBy`, `dcterms:created` and `dcterms:modified` at `0x3c8d99a6`, `0x3c8d9b22` and `0x3c8d9b87`. The UTC timestamp format is at `0x3cb408a0` and the DOM is serialized at `0x3c8d9c84`. |
| `docProps/custom.xml` | `suCustomProperties::SaveToStorage` dispatches the OLE property set at `0x3c7da3c4`. Its constructor adds the document-summary and user-defined section IDs from `0x3cc79160` and `0x3cc79170`. The XML writer selects their names at `0x3c8a174a` and `0x3c8a1767`, and emits the property-name dictionary at `0x3c8a1f8e`. |

The native `suOlePropertySection::GetCodePage` seeds PID 1 with codepage
65001 and variant type 2 at `0x3c89b205`. The document's hyperlink
update path calls `addOrUpdateOfficeProperty` with PID 22 and variant
type 11 at `0x3c7dc018`. The P03 office summary has the clear boolean
state and both dictionaries have zero user entries. The empty dictionary
node retains explicit start and end tags, which distinguishes this XML
stream's native formatting from the empty manifest nodes.

## P03 property and archive joins

Independent read-only inspection joined the eight P03 core XML creation
times to the model creation field and the corresponding `ModelStamps`
word. The last modifier matches the model header user entry. The XML
modification time matches `HeaderSelf.ModifiedTime` in all eight files.
The independent current-update clock in the header differs by one second
in four files.

The app XML is 570 bytes with SHA-256
`d69d246f37c251bb4a300d89745e66fbb6c19a4f6a23cf3dcb1cec93c24f6f51`
in all eight captures. The custom XML is 853 bytes with SHA-256
`9e1eb86e90840d66d6dba6cf3fb53bdecf1972e3b18342d874eb30aff80e64d5`
in all eight. Core XML has seven distinct payload digests because the
caller dates vary. The hosted replay reconstructs all three streams,
constructs the manifests from the generated targets, and exercises XML
escaping with separate fresh caller metadata.
[Hosted proof source](../../../../../../re/solidworks/WriterResearch/VerifyPartSidecars.py)
[Retained member inventory](SolidWorksPartSidecars.md#retained-p03-members)
