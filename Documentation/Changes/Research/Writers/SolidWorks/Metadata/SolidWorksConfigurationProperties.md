<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A12 configuration custom-property metadata

The configured property constructor takes the caller's storage index
and additional property count. It supports the first storage lane with
no additional properties. The 699-byte XML member has two independent
OLE dictionaries. Only the user-defined section carries the native
UTF-8 codepage entry. Both sections write their empty dictionary
elements with explicit start and end tags.
[Typed constructor](../../../../../../re/solidworks/WriterResearch/PartDocProperties.py)

## Native save path

The addresses below use the binaries' preferred image bases for
installed SOLIDWORKS 34.4.1.1011. The [same native OLE writer](SolidWorksDocumentProperties.md#native-owners)
emits document and configured sections from their respective property sets.

| Owner | Native evidence |
| --- | --- |
| `moBaseConfiguration_c::getStorageName` | `sldmodu.dll` at `0x4bdd97f0` constructs the storage name. The standalone branch at `0x4bdd9887` starts with `Config-` and appends the numeric lane from the configuration's native storage index. |
| Configured property set | The configuration constructor at `sldmodu.dll` addresses `0x4bdbd24a` and `0x4bdbd56d–0x4bdbd58e` initializes `suCustomProperties` and installs the configured XML properties data and DOM. The native root comes from `SldPropertyXMLHelper::getXMLStringForConfigProperties` at `sldmfcu.dll` address `0x3c79a050`. |
| `SolidStorage_c::SaveConfigMgr` | `doccplu.dll` calls `getStorageName` at `0x18003f8f7` and appends `-Properties` at `0x18003f90f`. It checks the configuration user-defined section count at `0x18003f935`. A nonempty native section goes to `suCustomProperties::SaveToStorage` at `0x18003f954`. The supported section carries its codepage record even with zero caller properties. |
| User section codepage | The call at `sldmodu.dll` address `0x4bddbedc` gets the codepage from the configured user section at configuration offset `+0x948`. The property writer at `sldmfcu.dll` address `0x3c89b205` initializes a missing codepage to 65001. |

`doccplu.dll` SHA-256 is
`120e1d5c359f5895d9785325995ebfaafc790ef7d74fe4fb0e242303f933939b`.
`sldmodu.dll` SHA-256 is
`2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`.

## Exact saved scope

Read-only inspection confirmed the owner `Contents/Config-0` and the
configuration property stream in all eight licensed P03 captures. The
office section had only its dictionary element. The user section
had PID 1 as `vt:i2` with value 65001, then its empty dictionary
element. All eight expanded payloads have SHA-256
`74295bb0e2888c500a9e979eb21ea08e97fd1f1f597160d284be476d6f3144f6`.
The hosted proof compares complete generated members and passes the
generated configuration property name into the OPC inventory.
[Hosted proof source](../../../../../../re/solidworks/WriterResearch/VerifyPartSidecars.py)

## Remaining SOLIDWORKS information metadata

The eight `ISolidWorksInformation.xml` streams share a layout of 49
property entries and 64 dictionary entries in one user-defined section.
The caller's filename, folder, summary and locale-sensitive date
properties need explicit ownership. `uiModelDoc_c::addSytemUnits` at
`slduiu.dll` address `0x4977a600` adds unit properties from named native
preferences. `uiModelDoc_c::SaveMassProperties` at `0x49772f00` forms
the configuration mass properties name at `0x497731bd`. The saved mass
payload varies across the authored geometry edits and requires the
same typed mass source and numeric formatting as the native producer.
Native acceptance and independent necessity of the remaining
information member are still open.
[Retained member inventory](SolidWorksPartSidecars.md#retained-p03-members)
