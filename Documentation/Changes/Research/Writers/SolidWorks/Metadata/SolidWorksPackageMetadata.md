<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A12 package manifests and open timing

The generation-19000 manifest constructor uses the exact extended, core
and custom property paths in the supplied emission inventory. It emits the
native relationship IDs, ordering, content type defaults and overrides.
It requires an existing nonempty stream for each target. The native
document property serializers supply these payloads with caller-owned
metadata.
[Package constructor](../../../../../../re/solidworks/WriterResearch/PartOpc.py)
[Document property writers](SolidWorksDocumentProperties.md)

## Native source

Installed SOLIDWORKS 34.4.1.1011 uses `sldmfcu.dll` with SHA-256
`bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6`.
The addresses in this table use the binary's preferred image base
`0x3c730000`. `suDocumentProperties::SaveToStorage` starts at
`0x3c7da3d0` and saves these native DOMs through
`SldXmlStreamHelper::saveXMLToStream` at `0x3c773d40`.

| Member | Native owner and expanded stream evidence |
| --- | --- |
| `_rels/.rels` | The initialization branch at `0x3c7da52f–0x3c7da61c` creates the relationships document. The protocol node definitions start at `0x3cc79750`. They assign IDs `rId3`, `rId2` and `rId4` to `docProps/app.xml`, `docProps/core.xml` and `docProps/custom.xml` respectively. The DOM is saved at `0x3c7daefc`. |
| `[Content_Types].xml` | The initialization branch at `0x3c7da61c–0x3c7da6f8` creates the content types document. The protocol node definitions start at `0x3cc79bb0`. The relationship and XML defaults precede overrides for the core and custom properties. The DOM is saved at `0x3c7daf4f`. |
| `docProps/OpenTime.xml` | The branch at `0x3c7da6f8` gets the dedicated open-time DOM and emits named counters and totals at `0x3c7da78a`, `0x3c7da895`, `0x3c7da91c` and `0x3c7daa27`. The stream is saved at `0x3c7dafa2`. |

The `suFileOpenTime` constructor at `0x3c7d9260` initializes resolved
and lightweight count and total pairs to `0` and `-1`. The total is a
seconds counter, and the constructor's all-ones value appears as the
signed decimal sentinel in XML. The typed constructor accepts caller-owned
timing pairs for a fresh document and for a single open with an elapsed
time of zero seconds. These measured branches have four scalar children
and no formatted average elements. The lightweight pair remains fresh in
all eight P03 captures. [Open-time constructor](../../../../../../re/solidworks/WriterResearch/PartOpenTime.py)

## P03 results

The read-only archive walk resolved all three relationship paths to
nonempty saved members in each of the eight files. It matched both
override paths to their corresponding targets and decoded the two
observed timing states. Three captures have fresh counters, and five
have recorded one resolved open. The manifest and relationships have one
expanded SHA-256 each across the eight files. The hosted proof rebuilds
each complete member and checks its bytes against the pinned native
evidence.
[Evidence and hosted proof](../../../../../../re/solidworks/WriterResearch/VerifyPartSidecars.py)

| Member | Expanded bytes | Native SHA-256 |
| --- | ---: | --- |
| `[Content_Types].xml` | 556 | `a50ae48af011114c4a400111c09ca34e083c21db7e82a2f3e3c641c752b89f4d` |
| `_rels/.rels` | 597 | `8fae89749a8d95ff5996361cf8f7dedb7c74a374c6ed87285d3d8c9e5a48717b` |
| `docProps/OpenTime.xml` | 402 or 403 | `31bf54eb417fca4f8e55095c69fea019f7f6b55f5385d4dce84a5d77a49efa4f`, `d4f8f737a68254a385bb281db7c44ec79d862e90b416d143ff8cdd941741ffec` |

Both manifests and the timing stream were retained in the licensed
omission run. Their individual necessity remains unmeasured.
[Retained roster](SolidWorksPartSidecars.md#retained-p03-members)
