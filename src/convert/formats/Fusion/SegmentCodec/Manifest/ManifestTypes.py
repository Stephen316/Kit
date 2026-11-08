# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass


# root state retains opaque ids and words without assigning them revision roles
@MakeDataClass(frozen=True, slots=True)
class RootManifest:
    Title: str
    Description: str
    OpaqueIds: tuple[str, str]
    OpaqueWords: tuple[int, int]
    Versions: tuple[tuple[str, int], ...]
    AssetId: str


# asset state retains the captured extension token and the opaque segment word
@MakeDataClass(frozen=True, slots=True)
class AssetManifest:
    AssetId: str
    SnapshotId: str
    Versions: tuple[tuple[str, int], ...]
    PhysicalGuid: str
    OpaqueWord: int
